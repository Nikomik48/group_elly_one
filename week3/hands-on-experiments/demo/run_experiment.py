"""Measured local CPU baseline. No hosted API calls; JSONL is the raw record."""
import argparse, base64, collections, csv, datetime, hashlib, json, math, os
import platform, re, resource, shutil, socket, sqlite3, statistics, subprocess, sys
import threading, time, urllib.request
from pathlib import Path
import sqlglot
from sqlglot import exp
from bootstrap import ROOT, LOCAL, MODEL_NAME, RUNTIME_TAG

BASE = 'http://127.0.0.1:18917'
ROW_CAP = 50000
SQL_TIMEOUT = 30
SYSTEM = 'Generate one read-only SQLite SELECT query for the supplied question. Return SQL only, without explanation or markdown. Use only the supplied schema. Do not change the database.'


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def post(path, body, timeout=600):
    request = urllib.request.Request(BASE + path, data=json.dumps(body).encode(),
                                     headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.load(response)


def sql_ast(sql):
    statements = sqlglot.parse(sql, read='sqlite')
    if len(statements) != 1 or not isinstance(statements[0], exp.Query):
        raise ValueError('Only one read-only query is permitted')
    if any(isinstance(n, (exp.Insert, exp.Update, exp.Delete, exp.Create, exp.Drop, exp.Into))
           for n in statements[0].walk()):
        raise ValueError('Write operation is not permitted')
    return statements[0]


def normalize_sql(text):
    text = text.strip()
    if text.startswith('```') and text.endswith('```'):
        lines = text.splitlines()
        text = '\n'.join(lines[1:-1]).strip()
    return text


def worker(db, sql_path):
    begin = time.perf_counter()
    try:
        sql = Path(sql_path).read_text()
        sql_ast(sql)
        conn = sqlite3.connect(Path(db).resolve().as_uri() + '?mode=ro&immutable=1', uri=True)
        conn.execute('PRAGMA query_only=ON')
        conn.execute('PRAGMA temp_store=MEMORY')
        deadline = time.perf_counter() + SQL_TIMEOUT
        conn.set_progress_handler(lambda: int(time.perf_counter() > deadline), 1000)
        allowed = {sqlite3.SQLITE_SELECT, sqlite3.SQLITE_READ, sqlite3.SQLITE_FUNCTION, sqlite3.SQLITE_RECURSIVE}
        def authorize(action, arg1, arg2, database, trigger):
            if action not in allowed:
                return sqlite3.SQLITE_DENY
            if action == sqlite3.SQLITE_FUNCTION and str(arg2 or arg1).lower() in {'load_extension', 'readfile', 'writefile', 'fts3_tokenizer'}:
                return sqlite3.SQLITE_DENY
            return sqlite3.SQLITE_OK
        conn.set_authorizer(authorize)
        cursor = conn.execute(sql)
        rows = cursor.fetchmany(ROW_CAP + 1)
        if len(rows) > ROW_CAP:
            raise ValueError('Result exceeds recorded row cap; evaluation incomplete')
        def encode(value):
            return {'__bytes__': base64.b64encode(value).decode()} if isinstance(value, bytes) else value
        result = {'ok': True, 'rows': [[encode(v) for v in row] for row in rows],
                  'columns': [c[0] for c in cursor.description], 'row_count': len(rows)}
        conn.close()
    except Exception as exc:
        result = {'ok': False, 'error_type': type(exc).__name__, 'error': str(exc)}
    result['worker_seconds'] = time.perf_counter() - begin
    print(json.dumps(result, allow_nan=False))


def execute(db, sql, destination):
    destination.write_text(sql)
    begin = time.perf_counter()
    try:
        p = subprocess.run([sys.executable, str(Path(__file__).resolve()), '--worker', str(db), str(destination)],
                           capture_output=True, text=True, timeout=SQL_TIMEOUT + 5)
        result = json.loads(p.stdout) if p.returncode == 0 else {'ok': False, 'error': p.stderr[-1000:]}
    except subprocess.TimeoutExpired:
        result = {'ok': False, 'error_type': 'TimeoutExpired', 'error': 'SQL worker killed after timeout'}
    result['sql_wall_seconds'] = time.perf_counter() - begin
    return result


def key_cell(v):
    if v is None: return (0, '')
    if isinstance(v, (int, float)): return (1, v)
    if isinstance(v, str): return (2, v)
    return (3, json.dumps(v, sort_keys=True))


def results_match(gold, predicted, ordered):
    if not gold.get('ok') or not predicted.get('ok'):
        return False
    if len(gold['columns']) != len(predicted['columns']) or len(gold['rows']) != len(predicted['rows']):
        return False
    a, b = gold['rows'], predicted['rows']
    if not ordered:
        a = sorted(a, key=lambda row: tuple(key_cell(v) for v in row))
        b = sorted(b, key=lambda row: tuple(key_cell(v) for v in row))
    for row_a, row_b in zip(a, b):
        for x, y in zip(row_a, row_b):
            if isinstance(x, int) and isinstance(y, int):
                if x != y: return False
            elif isinstance(x, (int, float)) and isinstance(y, (int, float)):
                if not math.isclose(x, y, rel_tol=1e-9, abs_tol=1e-6): return False
            elif x != y:
                return False
    return True


def snapshot(pid):
    r = subprocess.run(['ps', '-p', str(pid), '-o', 'rss=,%cpu=,time=,vsz='], capture_output=True, text=True)
    fields = r.stdout.split()
    if len(fields) != 4: return {}
    pieces = fields[2].split(':')
    cpu_seconds = sum(float(part) * 60**i for i, part in enumerate(reversed(pieces)))
    return {'rss_kib': int(fields[0]), 'ps_cpu_percent_lifetime': float(fields[1]),
            'cpu_seconds_cumulative': cpu_seconds, 'vsz_kib': int(fields[3])}


class Monitor:
    def __init__(self, process, destination):
        self.process = process
        self.destination = destination
        self.samples = []
        self.stop = threading.Event()
        self.thread = threading.Thread(target=self.run, daemon=True)
    def run(self):
        with self.destination.open('w') as f:
            while not self.stop.is_set():
                value = {'timestamp_utc': now(), 'monotonic_s': time.perf_counter(), **snapshot(self.process.pid)}
                self.samples.append(value)
                f.write(json.dumps(value) + '\n'); f.flush()
                self.stop.wait(0.5)
    def start(self): self.thread.start()
    def finish(self): self.stop.set(); self.thread.join()


def generate(messages, folder):
    begin = time.perf_counter()
    formatted = post('/apply-template', {'messages': messages, 'chat_template_kwargs': {'enable_thinking': False}})['prompt']
    tokens = post('/tokenize', {'content': formatted, 'add_special': False, 'parse_special': True})['tokens']
    (folder / 'prompt.txt').write_text(formatted)
    if len(tokens) > 12288:
        raise ValueError(f'Input overflow: {len(tokens)} tokens')
    payload = {'prompt': tokens, 'n_predict': 2048, 'temperature': 0, 'seed': 42,
               'cache_prompt': False, 'stream': True, 't_max_predict_ms': 600000}
    (folder / 'request.json').write_text(json.dumps({**payload, 'prompt': '[token IDs omitted; see prompt.txt]'}, indent=2))
    request = urllib.request.Request(BASE + '/completion', data=json.dumps(payload).encode(),
                                     headers={'Content-Type': 'application/json'})
    call_begin = time.perf_counter()
    first = None; text_parts = []; final = {}
    with urllib.request.urlopen(request, timeout=600) as response, (folder / 'events.jsonl').open('w') as trace:
        for raw in response:
            if time.perf_counter() - call_begin > 600:
                raise TimeoutError('Generation request exceeded 600 seconds')
            line = raw.decode().strip()
            if not line.startswith('data: '): continue
            content = line[6:]
            if content == '[DONE]': break
            data = json.loads(content)
            trace.write(json.dumps({'client_elapsed_s': time.perf_counter() - call_begin, 'event': data}) + '\n')
            if data.get('error'): raise RuntimeError(str(data['error']))
            piece = data.get('content', '')
            if piece:
                if first is None: first = time.perf_counter()
                text_parts.append(piece)
            if data.get('stop'):
                final = data
    if not final:
        raise RuntimeError('No final generation event received')
    call_seconds = time.perf_counter() - call_begin
    timings = final.get('timings', {})
    truncated = bool(final.get('truncated') or final.get('stopped_limit') or final.get('stop_type') == 'limit')
    text = ''.join(text_parts)
    (folder / 'model_output.txt').write_text(text)
    return {'model_output': text, 'input_tokens': len(tokens),
            'output_tokens': timings.get('predicted_n', final.get('tokens_predicted')),
            'prompt_cached_tokens': timings.get('cache_n'),
            'cache_tokens_after_request': final.get('tokens_cached'), 'runtime_timings': timings,
            'generation_wall_s': call_seconds, 'prompt_preparation_s': call_begin - begin,
            'ttft_s': None if first is None else first - call_begin,
            'stop_type': final.get('stop_type'), 'truncated': truncated,
            'prompt_sha256': hashlib.sha256(formatted.encode()).hexdigest(),
            'prompt_utf8_bytes': len(formatted.encode()), 'llm_calls': 1}


def percentile(values, q):
    if not values: return None
    s = sorted(values); index = (len(s) - 1) * q
    lo, hi = math.floor(index), math.ceil(index)
    return s[lo] + (s[hi] - s[lo]) * (index - lo)


def main(args):
    data_dir = LOCAL / 'data'
    question_file = data_dir / ('smoke_questions.json' if args.split == 'smoke' else 'questions_50.json')
    questions = json.loads(question_file.read_text())
    if args.limit: questions = questions[:args.limit]
    manifest = json.loads(Path(args.model_manifest).read_text()) if args.model_manifest else json.loads((ROOT / 'outputs' / 'artifact_manifest.json').read_text())
    model_path = ROOT / manifest['model_file']
    if not model_path.is_file():
        raise FileNotFoundError('Model file is missing; download it before running the experiment')
    slug = manifest.get('run_slug', '')
    if slug and not re.fullmatch(r'[a-z0-9_]+', slug):
        raise ValueError('Invalid model run slug')
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    out = ROOT / 'outputs' / (stamp + ('_' + slug if slug else '') + '_' + args.split + '_cpu')
    out.mkdir(parents=True)
    with socket.socket() as check:
        check.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        check.bind(('127.0.0.1', 18917))
    command = [str(LOCAL / 'runtime' / ('llama-' + RUNTIME_TAG) / 'llama-server'),
               '--model', str(model_path), '--host', '127.0.0.1', '--port', '18917',
               '--ctx-size', '16384', '--parallel', '1', '--threads', '4', '--threads-batch', '4',
               '--device', 'none', '--gpu-layers', '0', '--no-kv-offload', '--no-op-offload',
               '--cache-ram', '0', '--no-context-shift', '--no-warmup', '--metrics', '--perf',
               '--jinja', '--chat-template-kwargs', '{"enable_thinking":false}']
    metadata = {'started_utc': now(), 'split': args.split, 'questions': len(questions), 'command': command,
                'model_manifest': manifest, 'runner_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                'question_file_sha256': hashlib.sha256(question_file.read_bytes()).hexdigest(),
                'system_prompt_sha256': hashlib.sha256(SYSTEM.encode()).hexdigest(),
                'backend': 'CPU-only', 'threads': 4, 'context': 16384, 'input_cap': 12288, 'output_cap': 2048,
                'temperature': 0, 'seed': 42, 'cache_prompt': False, 'thinking': False,
                'python': platform.python_version(), 'sqlite': sqlite3.sqlite_version, 'sqlglot': sqlglot.__version__,
                'os': platform.mac_ver()[0], 'architecture': platform.machine(),
                'hardware': {'chip': 'Apple M3', 'ram_gb': 16, 'cpu_cores': 8},
                'free_disk_bytes_before': shutil.disk_usage(ROOT).free,
                'energy_j': None, 'energy_note': 'No power meter or supported energy counter used; energy not inferred from CPU time.',
                'measurement_note': 'RSS sampled every 0.5 s, not an exact allocation peak. ps CPU percent is a lifetime average. Model warm-up is reported separately.',
                'comparator': 'Local result comparator: column positions, duplicate multiplicity, outer ORDER BY; integer equality; other numbers abs_tol=1e-6, rel_tol=1e-9. Sorted-row matching can be conservative for near-tied numeric rows. Not an official BIRD score.'}
    power_state = subprocess.run(['pmset', '-g', 'batt'], capture_output=True, text=True).stdout
    metadata['power_state_before'] = re.sub(r'\(id=\d+\)', '', power_state)
    rows = []; process = None; monitor = None
    try:
        start = time.perf_counter()
        log = (out / 'server.log').open('w')
        process = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT)
        monitor = Monitor(process, out / 'resource_samples.jsonl'); monitor.start()
        while True:
            if process.poll() is not None: raise RuntimeError('Server exited; inspect server.log')
            try:
                with urllib.request.urlopen(BASE + '/health', timeout=1) as r:
                    if r.status == 200: break
            except Exception:
                if time.perf_counter() - start > 180: raise TimeoutError('Model startup exceeded 180 seconds')
                time.sleep(0.2)
        metadata['startup_to_health_s'] = time.perf_counter() - start
        warmup = out / 'warmup'; warmup.mkdir()
        metadata['warmup'] = generate([{'role': 'system', 'content': SYSTEM}, {'role': 'user', 'content': 'Return SELECT 1;'}], warmup)
        (out / 'run_metadata.json').write_text(json.dumps(metadata, indent=2))
        print(json.dumps({'event': 'ready', 'startup_s': metadata['startup_to_health_s'], 'output_dir': str(out)}), flush=True)
        with (out / 'questions.jsonl').open('w') as logrows:
            for index, question in enumerate(questions):
                begin = time.perf_counter()
                folder = out / f'case_{index:03d}'; folder.mkdir()
                db_id = question['db_id']
                db = data_dir / 'databases' / db_id / (db_id + '.sqlite')
                row = {'index': index, 'question_id': question.get('question_id'), 'db_id': db_id,
                       'question': question['question'], 'evidence': question.get('evidence', ''),
                       'gold_sql': question['SQL'], 'started_utc': now(), 'matched': False, 'execution_success': False}
                cpu_before = snapshot(process.pid)
                try:
                    gold = execute(db, question['SQL'], folder / 'gold.sql')
                    row['gold_result'] = gold
                    if not gold['ok']: raise ValueError('Reference query failed; no accuracy claim for this case')
                    schema_start = time.perf_counter()
                    with sqlite3.connect(db.resolve().as_uri() + '?mode=ro&immutable=1', uri=True) as conn:
                        objects = conn.execute("SELECT name, sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name").fetchall()
                        columns = sum(len(conn.execute('PRAGMA table_info(' + '"' + name.replace('"', '""') + '"' + ')').fetchall()) for name, _ in objects)
                    schema = '\n\n'.join(sql for _, sql in objects if sql)
                    row.update(schema_tables=len(objects), schema_columns=columns, schema_characters=len(schema), schema_read_s=time.perf_counter() - schema_start)
                    user = 'SQLite schema:\n' + schema + '\n\nQuestion: ' + question['question'] + '\nEvidence: ' + question.get('evidence', '')
                    generation = generate([{'role': 'system', 'content': SYSTEM}, {'role': 'user', 'content': user}], folder)
                    row.update(generation)
                    if generation['truncated']: raise ValueError('Truncated model output; SQL not executed')
                    sql = normalize_sql(generation['model_output'])
                    row['predicted_sql'] = sql
                    prediction = execute(db, sql, folder / 'prediction.sql')
                    row['predicted_result'] = prediction
                    row['execution_success'] = prediction['ok']
                    row['matched'] = results_match(gold, prediction, bool(sql_ast(question['SQL']).args.get('order')))
                except Exception as exc:
                    row.update(error_type=type(exc).__name__, error=str(exc))
                after = time.perf_counter()
                row['end_to_end_s'] = after - begin
                row['evaluation_overhead_s'] = row.get('gold_result', {}).get('sql_wall_seconds', 0)
                row['application_wall_s'] = row['end_to_end_s'] - row['evaluation_overhead_s']
                samples = [x for x in monitor.samples if begin <= x['monotonic_s'] <= after]
                row['sampled_peak_server_rss_mib'] = max([x.get('rss_kib', 0) for x in samples] or [snapshot(process.pid).get('rss_kib', 0)]) / 1024
                cpu_after = snapshot(process.pid)
                row['server_cpu_seconds'] = cpu_after.get('cpu_seconds_cumulative', 0) - cpu_before.get('cpu_seconds_cumulative', 0)
                row['sampling_count'] = len(samples)
                row['energy_j'] = None
                logrows.write(json.dumps(row) + '\n'); logrows.flush(); rows.append(row)
                print(json.dumps({k: row.get(k) for k in ['index', 'question_id', 'db_id', 'matched', 'execution_success', 'input_tokens', 'output_tokens', 'generation_wall_s', 'ttft_s', 'sampled_peak_server_rss_mib', 'error']}), flush=True)
    finally:
        if process:
            process.terminate()
            try: process.wait(timeout=10)
            except subprocess.TimeoutExpired: process.kill(); process.wait()
        if monitor: monitor.finish()
        metadata['completed_utc'] = now()
        metadata['free_disk_bytes_after'] = shutil.disk_usage(ROOT).free
        metadata['runtime_child_rusage'] = {'max_rss_bytes_macos': resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss,
                                             'note': 'Maximum across completed children, including SQL workers; not a summed service peak.'}
        (out / 'run_metadata.json').write_text(json.dumps(metadata, indent=2))
    keys = ['question_id', 'db_id', 'matched', 'execution_success', 'input_tokens', 'output_tokens', 'generation_wall_s',
            'ttft_s', 'application_wall_s', 'end_to_end_s', 'schema_read_s', 'schema_tables', 'schema_columns',
            'sampled_peak_server_rss_mib', 'server_cpu_seconds', 'truncated', 'stop_type', 'error_type', 'error']
    with (out / 'questions.csv').open('w') as f:
        writer = csv.DictWriter(f, fieldnames=keys, extrasaction='ignore'); writer.writeheader(); writer.writerows(rows)
    values = lambda key: [r[key] for r in rows if isinstance(r.get(key), (int, float))]
    summary = {'split': args.split, 'completed_questions': len(rows), 'requested_questions': len(questions),
               'matches': sum(r['matched'] for r in rows), 'execution_successes': sum(r['execution_success'] for r in rows),
               'reference_failures': sum(not r.get('gold_result', {}).get('ok', False) for r in rows),
               'local_execution_accuracy': (sum(r['matched'] for r in rows) / len(rows)) if rows and all(r.get('gold_result', {}).get('ok') for r in rows) else None,
               'metric_scope': metadata['comparator'], 'startup_to_health_s': metadata.get('startup_to_health_s'),
               'input_tokens_total': sum(values('input_tokens')), 'output_tokens_total': sum(values('output_tokens')),
               'energy_j': None}
    for key in ['generation_wall_s', 'ttft_s', 'application_wall_s', 'end_to_end_s']:
        sample = values(key)
        summary[key] = {'mean': statistics.mean(sample) if sample else None, 'p50': percentile(sample, .5), 'p95': percentile(sample, .95),
                        'scope': 'Cases with this metric available; missing metrics/errors remain in raw rows.'}
    summary['sampled_peak_server_rss_mib'] = max(values('sampled_peak_server_rss_mib'), default=None)
    (out / 'summary.json').write_text(json.dumps(summary, indent=2))
    print(json.dumps({'event': 'finished', 'summary': summary, 'output_dir': str(out)}), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--split', choices=['smoke', 'scored'], default='smoke')
    parser.add_argument('--limit', type=int)
    parser.add_argument('--model-manifest', help='Pinned model manifest; defaults to the original Qwen3 baseline')
    parser.add_argument('--worker', nargs=2, metavar=('DATABASE', 'SQL_FILE'))
    args = parser.parse_args()
    if args.worker: worker(*args.worker)
    else: main(args)

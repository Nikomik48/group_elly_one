"""Show one frozen benchmark question, generated SQL and reference results.

Live mode performs fresh local inference. Saved mode re-executes an old prediction
and is labelled explicitly; neither mode changes the benchmark records.
"""
import argparse
import datetime
import hashlib
import html
import json
import socket
import sqlite3
import subprocess
import time
import urllib.request
from pathlib import Path

import run_experiment as runner
from bootstrap import LOCAL, ROOT, RUNTIME_TAG

RUNS = {
    'qwen3': ('Qwen3-1.7B', '20261018T123527Z_scored_cpu', 'artifact_manifest.json'),
    'coder': ('Qwen2.5-Coder-3B-Instruct', '20261018T130607Z_qwen25_coder_3b_scored_cpu', 'artifact_manifest_qwen25_coder_3b.json'),
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def table(result, limit=10):
    if not result.get('ok'):
        return 'Execution failed: ' + result.get('error', 'Unknown error')
    def cell(value):
        return str(value if value is not None else 'NULL').replace('|', '\\|').replace('\n', ' ')
    cols = result['columns']
    lines = ['| ' + ' | '.join(map(cell, cols)) + ' |', '| ' + ' | '.join(['---'] * len(cols)) + ' |']
    lines += ['| ' + ' | '.join(map(cell, row)) + ' |' for row in result['rows'][:limit]]
    lines.append(f"\n{len(result['rows'])} row(s); showing up to {limit}. Full rows are in demo.json.")
    return '\n'.join(lines)


def schema(db):
    output = []
    with sqlite3.connect(db.resolve().as_uri() + '?mode=ro&immutable=1', uri=True) as conn:
        for name, ddl in conn.execute("SELECT name, sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name").fetchall():
            quote = '"' + name.replace('"', '""') + '"'
            output.append({'name': name, 'ddl': ddl, 'columns': conn.execute('PRAGMA table_info(' + quote + ')').fetchall(),
                           'foreign_keys': conn.execute('PRAGMA foreign_key_list(' + quote + ')').fetchall()})
    return output


def mermaid(tables):
    # Only declared FK links are drawn; no relationship cardinality is inferred.
    nodes = {item['name']: f't{i}' for i, item in enumerate(tables)}
    lines = ['flowchart LR']
    for item in tables:
        labels = [html.escape(item['name'])]
        for _, name, kind, _, _, pk in item['columns']:
            foreign = any(fk[3] == name for fk in item['foreign_keys'])
            marker = ' PK, FK' if pk and foreign else ' PK' if pk else ' FK' if foreign else ''
            labels.append(html.escape(name + ': ' + (kind or 'ANY') + marker))
        lines.append('    ' + nodes[item['name']] + '["' + '<br/>'.join(labels) + '"]')
    for item in tables:
        for fk in item['foreign_keys']:
            if fk[2] in nodes:
                label = html.escape(fk[3] + ' to ' + (fk[4] or 'primary key'))
                lines.append('    ' + nodes[item['name']] + ' -->|"' + label + '"| ' + nodes[fk[2]])
    return '\n'.join(lines) + '\n'


def live(model, question, ddl, out):
    label, _, manifest_name = RUNS[model]
    manifest = json.loads((ROOT / 'outputs' / manifest_name).read_text())
    model_path = ROOT / manifest['model_file']
    executable = LOCAL / 'runtime' / ('llama-' + RUNTIME_TAG) / 'llama-server'
    if not model_path.is_file() or not executable.is_file():
        raise FileNotFoundError('Model/runtime missing; use the setup commands in README.md first.')
    with socket.socket() as check:
        check.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        check.bind(('127.0.0.1', 18917))
    command = [str(executable), '--model', str(model_path), '--host', '127.0.0.1', '--port', '18917',
               '--ctx-size', '16384', '--parallel', '1', '--threads', '4', '--threads-batch', '4',
               '--device', 'none', '--gpu-layers', '0', '--no-kv-offload', '--no-op-offload',
               '--cache-ram', '0', '--no-context-shift', '--no-warmup', '--metrics', '--perf',
               '--jinja', '--chat-template-kwargs', '{"enable_thinking":false}']
    print(f'\nLoading {label} (CPU only)...', flush=True)
    started = time.perf_counter()
    with (out / 'server.log').open('w') as log:
        process = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT)
        try:
            while True:
                if process.poll() is not None:
                    raise RuntimeError(f'Server exited; see {out / "server.log"}')
                try:
                    with urllib.request.urlopen(runner.BASE + '/health', timeout=1) as response:
                        if response.status == 200:
                            break
                except Exception:
                    if time.perf_counter() - started > 180:
                        raise TimeoutError('Model startup exceeded 180 seconds')
                    time.sleep(0.2)
            startup = time.perf_counter() - started
            warmup = out / 'warmup'; warmup.mkdir()
            runner.generate([{'role': 'system', 'content': runner.SYSTEM}, {'role': 'user', 'content': 'Return SELECT 1;'}], warmup)
            prompt = 'SQLite schema:\n' + ddl + '\n\nQuestion: ' + question['question'] + '\nEvidence: ' + question.get('evidence', '')
            result = runner.generate([{'role': 'system', 'content': runner.SYSTEM}, {'role': 'user', 'content': prompt}], out)
            return {**result, 'startup_to_health_s': startup, 'command': command, 'model_manifest': manifest}
        finally:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill(); process.wait()


def html_table(result):
    esc = html.escape
    if not result.get('ok'):
        return '<pre>' + esc(result.get('error', 'Execution failed')) + '</pre>'
    header = ''.join('<th>' + esc(str(c)) + '</th>' for c in result['columns'])
    rows = ''.join('<tr>' + ''.join('<td>' + esc('NULL' if c is None else str(c)) + '</td>' for c in row) + '</tr>' for row in result['rows'][:10])
    return f'<div class="scroll"><table><tr>{header}</tr>{rows}</table></div><p>{len(result["rows"])} rows; preview limited to 10.</p>'


def write_report(report, out):
    q = report['question']; esc = html.escape
    md = ['# Text-to-SQL demo', f"\nMode: **{report['mode']}** · Question ID: **{q['question_id']}** · Database: **{q['db_id']}**",
          '\n' + q['question'], '\nEvidence: ' + q.get('evidence', ''), '\n## Database schema',
          '\nDeclared foreign keys only; lines do not specify cardinality.', '\n```mermaid\n' + report['schema_mermaid'].rstrip() + '\n```',
          '\n## Reference SQL', '\n```sql\n' + q['SQL'] + '\n```', '\n## Expected result', '\n' + table(report['gold_result'])]
    sections = []
    for item in report['models']:
        details = item['generation']
        stats = (f"Generation: {details['generation_wall_s']:.2f} s; input/output tokens: {details['input_tokens']}/{details['output_tokens']}. "
                 + ('Fresh inference; startup and warm-up are separate.' if report['mode'] == 'live' else 'Historical generation measurements; no fresh inference.'))
        md += ['\n## ' + item['label'], '\n```sql\n' + item['sql'] + '\n```', '\n' + table(item['result']),
               f"\nResult match: **{item['matched']}**. " + stats]
        sections += [f'<section><h2>{esc(item["label"])}</h2><pre>{esc(item["sql"])}</pre>{html_table(item["result"])}<p><strong>Result match: {item["matched"]}</strong></p><p>{esc(stats)}</p></section>']
    note = ('Read-only SELECT queries do not change stored data. The before/after database SHA-256 hashes are '
            + ('identical.' if report['database_unchanged'] else 'DIFFERENT; investigate before presenting results.')
            + ' The tables above are query outputs, not modified database states. This single example is a demonstration, not a new benchmark score.')
    md += ['\n## Database state', '\n' + note, '\nBefore: `' + report['database_sha256_before'] + '`', '\nAfter: `' + report['database_sha256_after'] + '`']
    (out / 'report.md').write_text('\n'.join(md) + '\n')
    cards = []
    for item in report['schema']:
        fields = '<br>'.join(esc(c[1] + ' : ' + (c[2] or 'ANY') + (' [PK]' if c[5] else '')) for c in item['columns'])
        fks = '<br>'.join(esc(f'{fk[3]} → {fk[2]}.{fk[4] or "primary key"}') for fk in item['foreign_keys'])
        cards += [f'<article><h3>{esc(item["name"])}</h3>{fields}<p class="fk">{fks}</p></article>']
    page = f'''<!doctype html><html lang="en"><meta charset="utf-8"><title>Text-to-SQL demo</title>
<style>body{{font:16px system-ui;max-width:1150px;margin:36px auto;padding:0 24px;color:#172b42;background:#f6f8fb}}h1,h2,h3{{color:#113e5b}}section,article{{background:white;border:1px solid #cdd9e4;border-radius:10px;padding:18px;margin:16px 0}}pre{{white-space:pre-wrap;overflow-wrap:anywhere;background:#eef3f8;padding:16px;border-radius:6px}}table{{border-collapse:collapse;width:100%}}td,th{{text-align:left;padding:9px;border:1px solid #cdd9e4}}th{{background:#eaf4fa}}.schema{{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:12px}}.schema article{{margin:0;font:14px ui-monospace,monospace}}.fk{{color:#255a83}}.flow{{padding:18px;background:#dfeff7;font-weight:600;text-align:center}}.scroll{{overflow-x:auto}}p{{line-height:1.55}}</style>
<h1>Text-to-SQL demo</h1><p><strong>{esc(report['mode'].upper())}</strong> · Question {esc(str(q['question_id']))} · {esc(q['db_id'])}</p>
<h2>{esc(q['question'])}</h2><p>Evidence: {esc(q.get('evidence',''))}</p>
<div class="flow">Same database snapshot → Reference SQL / Model SQL → Expected / Generated result tables → Result match</div>
<details><summary><h2 style="display:inline">Database schema ({len(report['schema'])} tables)</h2></summary><p>Declared foreign keys are shown with arrows. Cardinality is not inferred.</p><div class="schema">{''.join(cards)}</div></details>
<section><h2>Reference SQL and expected result</h2><pre>{esc(q['SQL'])}</pre>{html_table(report['gold_result'])}</section>
{''.join(sections)}<section><h2>Database state</h2><p>{esc(note)}</p><pre>Before: {report['database_sha256_before']}\nAfter:  {report['database_sha256_after']}</pre></section>
<p>Full returned rows and measurements: demo.json. Mermaid schema diagram: schema.mmd. Query failures are shown, not repaired.</p></html>'''
    (out / 'report.html').write_text(page)
    (out / 'schema.mmd').write_text(report['schema_mermaid'])
    (out / 'demo.json').write_text(json.dumps(report, indent=2) + '\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model', choices=['qwen3', 'coder', 'both'], default='both')
    parser.add_argument('--mode', choices=['live', 'saved'], default='live')
    parser.add_argument('--question-id', default='765', help='Frozen question ID; default is the first scored question')
    parser.add_argument('--list', action='store_true', help='List the frozen 50 questions without loading a model')
    args = parser.parse_args()
    questions = json.loads((LOCAL / 'data/questions_50.json').read_text())
    if args.list:
        for q in questions:
            print(f"{q['question_id']:>5}  {q['db_id']:<24} {q['question']}")
        return
    question = next((q for q in questions if str(q['question_id']) == args.question_id), None)
    if question is None:
        parser.error('Unknown question ID; use --list')
    db = LOCAL / 'data/databases' / question['db_id'] / (question['db_id'] + '.sqlite')
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')
    out = ROOT / 'outputs/demos' / (stamp + '_' + args.mode); out.mkdir(parents=True)
    before = digest(db)
    tables = schema(db); ddl = '\n\n'.join(item['ddl'] for item in tables if item['ddl'])
    report = {'mode': args.mode, 'created_utc': runner.now(), 'question': question, 'schema': tables,
              'schema_mermaid': mermaid(tables), 'database_sha256_before': before, 'models': []}
    (out / 'schema.sql').write_text(ddl + '\n')
    gold = runner.execute(db, question['SQL'], out / 'gold.sql'); report['gold_result'] = gold
    if not gold.get('ok'):
        raise RuntimeError('Reference failed: ' + str(gold))
    print(f"\nQuestion {question['question_id']} ({question['db_id']}): {question['question']}", flush=True)
    print('\nREFERENCE SQL:\n' + question['SQL'] + '\n\nEXPECTED RESULT:\n' + table(gold), flush=True)
    models = list(RUNS) if args.model == 'both' else [args.model]
    for model in models:
        label, run, _ = RUNS[model]; target = out / model; target.mkdir()
        if args.mode == 'live':
            generation = live(model, question, ddl, target)
        else:
            records = ROOT / 'outputs' / run / 'questions.jsonl'
            if not records.is_file():
                raise FileNotFoundError('Saved replay requires the original run records, which are not bundled. Use --mode live on a fresh installation.')
            old = [json.loads(x) for x in records.read_text().splitlines()]
            generation = next(x for x in old if str(x['question_id']) == args.question_id)
            generation = {**generation, 'source_run': run}
            print(f'\nSAVED prediction replay: {label}; no model inference.', flush=True)
        sql = runner.normalize_sql(generation.get('model_output', ''))
        result = ({'ok': False, 'error': 'Output truncated; query not executed'} if generation.get('truncated')
                  else runner.execute(db, sql, target / 'prediction.sql'))
        matched = runner.results_match(gold, result, bool(runner.sql_ast(question['SQL']).args.get('order')))
        report['models'].append({'label': label, 'sql': sql, 'result': result, 'matched': matched, 'generation': generation})
        print(f'\n{label} SQL:\n{sql}\n\nMODEL RESULT:\n{table(result)}\nMATCH: {matched}', flush=True)
        timing_label = 'Fresh' if args.mode == 'live' else 'Historical'
        print(f"{timing_label} generation: {generation['generation_wall_s']:.2f} s | "
              f"Input/output tokens: {generation['input_tokens']}/{generation['output_tokens']}", flush=True)
    report['database_sha256_after'] = digest(db)
    report['database_unchanged'] = before == report['database_sha256_after']
    write_report(report, out)
    print('\nDatabase unchanged:', report['database_unchanged'])
    print('HTML report:', out / 'report.html')
    print('Markdown report:', out / 'report.md')
    print('Schema:', out / 'schema.mmd')
    if not report['database_unchanged']:
        raise RuntimeError('Database hash changed')


if __name__ == '__main__':
    main()

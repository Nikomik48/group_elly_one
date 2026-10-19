"""Group-authored SQLite evaluation extracted from the measured baseline runner.

The six evaluation functions below are copied without changes. Only imports and
this standalone command-line entry point differ. See ../README.md for provenance.
"""
import argparse
import base64
import json
import math
import sqlite3
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import sqlglot
from sqlglot import exp

ROW_CAP = 50000
SQL_TIMEOUT = 30

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

def main():
    parser = argparse.ArgumentParser(description="Compare two SQL result tables on the same SQLite snapshot")
    parser.add_argument('--db', type=Path)
    parser.add_argument('--gold', type=Path, help='Reference .sql file')
    parser.add_argument('--pred', type=Path, help='Generated .sql file')
    parser.add_argument('--worker', nargs=2, metavar=('DATABASE', 'SQL_FILE'), help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.worker:
        worker(*args.worker)
        return
    if not all((args.db, args.gold, args.pred)):
        parser.error('--db, --gold and --pred are required')
    if not args.db.is_file():
        parser.error('Database does not exist')
    gold_sql = args.gold.read_text()
    predicted_sql = normalize_sql(args.pred.read_text())
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder)
        gold = execute(args.db, gold_sql, path / 'gold.sql')
        predicted = execute(args.db, predicted_sql, path / 'prediction.sql')
    if not gold.get('ok'):
        print(json.dumps({'reference_ok': False, 'gold_result': gold, 'matched': None}))
        raise SystemExit(2)
    ordered = bool(sql_ast(gold_sql).args.get('order'))
    print(json.dumps({'reference_ok': True, 'execution_success': predicted['ok'],
                      'matched': results_match(gold, predicted, ordered),
                      'ordered': ordered, 'gold_result': gold, 'predicted_result': predicted}, indent=2))


if __name__ == '__main__':
    main()

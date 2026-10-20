"""Fetch public source artifacts and freeze a small diagnostic subset before inference."""
import io, json, random, shutil, sqlite3, time, urllib.request, zipfile
from pathlib import Path
from bootstrap import ROOT, LOCAL, download, sha256, event

REVISION = 'fe766045c55b6875a43b30e9ac7683df5582f8cf'
URL = f'https://raw.githubusercontent.com/uiuc-kang-lab/text_to_sql_benchmarks/{REVISION}/data/arcwise_plat_full_with_diff.json'
ZIP_URL = 'https://bird-bench.oss-cn-beijing.aliyuncs.com/dev.zip'
ZIP_BYTES = 346207293
ZIP_SHA256 = 'cdd6d19faeb45a23970b98d3ef6c40a87987c95459c2cf12076897a60cf5a630'
LABELS_SHA256 = 'baefe2ca4fbab86c000df72aad9eaa563f7d422e425af2cbff071f656ea4eea8'


def main():
    start = time.perf_counter()
    folder = LOCAL / 'data'
    folder.mkdir(parents=True, exist_ok=True)
    labels = folder / 'arcwise_plat_full_with_diff.json'
    if not labels.exists():
        with urllib.request.urlopen(URL, timeout=45) as r:
            labels.write_bytes(r.read(4 * 1024 * 1024))
    if sha256(labels) != LABELS_SHA256:
        raise RuntimeError('Corrected labels do not match the pinned artifact')
    data = json.loads(labels.read_text())
    if not isinstance(data, list) or len(data) != 498:
        raise RuntimeError('Unexpected corrected-label artifact')
    archive = folder / 'dev.zip'
    download(ZIP_URL, archive, ZIP_BYTES, ZIP_SHA256)
    inner = folder / 'dev_databases.zip'
    with zipfile.ZipFile(archive) as z:
        member = next(i for i in z.infolist() if i.filename == 'dev_20240627/dev_databases.zip')
        if not inner.exists():
            with z.open(member) as source, inner.open('wb') as dest:
                shutil.copyfileobj(source, dest, 1024 * 1024)
    groups = {}
    for row in data:
        groups.setdefault(row['db_id'], []).append(row)
    with zipfile.ZipFile(inner) as z:
        candidates = []
        for i in z.infolist():
            p = Path(i.filename)
            if p.suffix == '.sqlite' and p.stem in groups and len(groups[p.stem]) >= 12:
                candidates.append((i.file_size, p.stem, i))
        candidates.sort(key=lambda x: (x[0], x[1]))
        chosen = candidates[:5]
        if len(chosen) != 5:
            raise RuntimeError('Could not match five databases to corrected labels')
        needed = sum(x[0] for x in chosen)
        if needed > 2 * 2**30 or shutil.disk_usage(ROOT).free - needed < 6 * 2**30:
            raise RuntimeError('Selected database extraction exceeds storage budget')
        selected = []
        smoke = []
        database_rows = []
        rng = random.Random(42)
        for size, db_id, member in chosen:
            db = folder / 'databases' / db_id / (db_id + '.sqlite')
            db.parent.mkdir(parents=True, exist_ok=True)
            if not db.exists():
                with z.open(member) as source, db.open('wb') as dest:
                    shutil.copyfileobj(source, dest, 1024 * 1024)
            if db.stat().st_size != size:
                raise RuntimeError('Database extraction size mismatch')
            with sqlite3.connect(db.resolve().as_uri() + '?mode=ro', uri=True) as conn:
                check = conn.execute('PRAGMA quick_check').fetchone()[0]
                tables = conn.execute("SELECT count(*) FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'").fetchone()[0]
            if check != 'ok':
                raise RuntimeError(f'Database integrity check failed: {db_id}')
            questions = sorted(groups[db_id], key=lambda x: str(x.get('question_id', x.get('question', ''))))
            rng.shuffle(questions)
            for row in questions[:2]:
                smoke.append(row)
            for row in questions[2:12]:
                selected.append(row)
            database_rows.append({'db_id': db_id, 'bytes': size, 'sha256': sha256(db), 'tables': tables,
                                  'path': str(db.relative_to(ROOT))})
        (folder / 'smoke_questions.json').write_text(json.dumps(smoke, indent=2))
        (folder / 'questions_50.json').write_text(json.dumps(selected, indent=2))
    manifest = {'label_revision': REVISION, 'label_url': URL, 'labels_sha256': sha256(labels),
                'database_archive_url': ZIP_URL, 'database_archive_sha256': sha256(archive),
                'database_archive_bytes': ZIP_BYTES, 'selection_seed': 42,
                'selection_rule': 'Five smallest matching DBs with >=12 corrected questions; 2 smoke and 10 scored IDs per DB, sampled before inference.',
                'scope': 'Storage-constrained diagnostic subset, not representative of the full benchmark; query-family audit pending.',
                'databases': database_rows, 'smoke_count': len(smoke), 'scored_count': len(selected),
                'query_ids': [r.get('question_id') for r in selected],
                'source_license': 'Corrected labels: CC-BY-SA-4.0; database terms: original BIRD release.'}
    (ROOT / 'outputs' / 'data_manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    event('prepare_data', 'completed', elapsed_seconds=time.perf_counter() - start,
          selected_database_bytes=needed, databases=database_rows,
          disk_free_bytes=shutil.disk_usage(ROOT).free)


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        event('prepare_data', 'failed', error_type=type(exc).__name__, message=str(exc))
        raise

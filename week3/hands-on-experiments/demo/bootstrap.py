"""Project-local, checksummed runtime/model setup. Python standard library only."""
import datetime, hashlib, json, os, platform, shutil, sys, tarfile, time, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LOCAL = ROOT / '.local'
EVENTS = ROOT / 'outputs' / 'setup_events.jsonl'
MODEL_REPO = 'ggml-org/Qwen3-1.7B-GGUF'
MODEL_REVISION = 'daeb8e2d528a760970442092f6bf1e55c3b659eb'
MODEL_NAME = 'Qwen3-1.7B-Q4_K_M.gguf'
MODEL_SHA256 = 'd2387ca2dbfee2ffabce7120d3770dadca0b293052bc2f0e138fdc940d9bc7b5'
MODEL_BYTES = 1282439264
RUNTIME_TAG = 'b11719'
RUNTIME_SHA256 = '076a2b0d15253078b90bd520a82dc2edc6c17657968878876ba3def3e80f54ba'


def event(stage, status, **fields):
    row = {'timestamp_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
           'stage': stage, 'status': status, **fields}
    EVENTS.parent.mkdir(parents=True, exist_ok=True)
    with EVENTS.open('a') as f:
        f.write(json.dumps(row) + '\n')
    print(json.dumps(row), flush=True)


def sha256(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(4 * 1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def get_json(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'ENS491-local-feasibility'}), timeout=60) as f:
        return json.load(f)


def download(url, dest, expected_size, expected_hash=None):
    if dest.exists():
        if dest.stat().st_size == expected_size and (not expected_hash or sha256(dest) == expected_hash):
            event(dest.name, 'reused', bytes=expected_size)
            return
        raise RuntimeError(f'Existing file does not match expected artifact: {dest}')
    if shutil.disk_usage(ROOT).free - expected_size < 6 * 2**30:
        raise RuntimeError('Download would leave less than 6 GiB free; no download started.')
    dest.parent.mkdir(parents=True, exist_ok=True)
    partial = dest.with_name(dest.name + '.part')
    start = time.perf_counter()
    event(dest.name, 'download_started', expected_bytes=expected_size, source_url=url)
    req = urllib.request.Request(url, headers={'User-Agent': 'ENS491-local-feasibility'})
    received = 0
    last_log = start
    with urllib.request.urlopen(req, timeout=90) as response, partial.open('wb') as out:
        while chunk := response.read(4 * 1024 * 1024):
            out.write(chunk)
            received += len(chunk)
            if received > expected_size:
                raise RuntimeError('Response exceeds expected file size')
            if time.perf_counter() - last_log >= 20:
                event(dest.name, 'download_progress', received_bytes=received)
                last_log = time.perf_counter()
    elapsed = time.perf_counter() - start
    if received != expected_size:
        raise RuntimeError(f'File size mismatch: {received} != {expected_size}')
    verify_start = time.perf_counter()
    actual_hash = sha256(partial)
    if expected_hash and actual_hash != expected_hash:
        raise RuntimeError('SHA256 mismatch; artifact will not be used')
    partial.rename(dest)
    event(dest.name, 'download_verified', bytes=received, download_seconds=elapsed,
          mean_download_mib_s=received / 2**20 / elapsed, sha256=actual_hash,
          verification_seconds=time.perf_counter() - verify_start)


def main():
    if platform.system() != 'Darwin' or platform.machine() != 'arm64':
        raise RuntimeError('This installer uses the Apple Silicon macOS runtime. Other platforms need a separately configured runtime.')
    if sys.version_info < (3, 13):
        raise RuntimeError('Use Python 3.13 or newer; the baseline was tested with Python 3.13.2.')
    start = time.perf_counter()
    LOCAL.mkdir(parents=True, exist_ok=True)
    event('bootstrap', 'started', disk_free_bytes=shutil.disk_usage(ROOT).free)
    release = get_json(f'https://api.github.com/repos/ggml-org/llama.cpp/releases/tags/{RUNTIME_TAG}')
    asset = next(a for a in release['assets'] if a['name'] == f'llama-{RUNTIME_TAG}-bin-macos-arm64.tar.gz')
    archive = LOCAL / asset['name']
    download(asset['browser_download_url'], archive, asset['size'], RUNTIME_SHA256)
    runtime = LOCAL / 'runtime'
    extraction = time.perf_counter()
    if not runtime.exists():
        with tarfile.open(archive, 'r:gz') as tar:
            if sum(m.size for m in tar.getmembers()) > 300 * 2**20:
                raise RuntimeError('Unexpectedly large runtime archive')
            tar.extractall(runtime, filter='data')
    event('runtime_extract', 'completed', elapsed_seconds=time.perf_counter() - extraction)
    model = LOCAL / 'models' / MODEL_NAME
    url = f'https://huggingface.co/{MODEL_REPO}/resolve/{MODEL_REVISION}/{MODEL_NAME}'
    download(url, model, MODEL_BYTES, MODEL_SHA256)
    manifest = {'runtime_tag': RUNTIME_TAG, 'runtime_asset_sha256': sha256(archive),
                'model_repository': MODEL_REPO, 'model_revision': MODEL_REVISION,
                'model_file': str(model.relative_to(ROOT)), 'model_sha256': MODEL_SHA256,
                'model_bytes': MODEL_BYTES}
    (ROOT / 'outputs' / 'artifact_manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    event('bootstrap', 'completed', elapsed_seconds=time.perf_counter() - start,
          disk_free_bytes=shutil.disk_usage(ROOT).free)


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        event('bootstrap', 'failed', error_type=type(exc).__name__, message=str(exc))
        raise

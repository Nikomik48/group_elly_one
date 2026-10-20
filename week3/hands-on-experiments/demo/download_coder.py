"""Add the official Qwen2.5-Coder-3B Q4 model; reuse runtime, data and environment."""
import json, shutil, time, urllib.request
from bootstrap import ROOT, LOCAL, download, event, sha256, RUNTIME_TAG

REPOSITORY = 'Qwen/Qwen2.5-Coder-3B-Instruct-GGUF'
REVISION = 'f74adce6aa16316c625447af059dbebe4983757c'
FILENAME = 'qwen2.5-coder-3b-instruct-q4_k_m.gguf'
SIZE = 2104932800
SHA256 = '724fb256bec1ff062b2f65e4569e871ad2e95ab2a3989723d1769c54294730b7'


def main():
    start = time.perf_counter()
    event('setup_qwen25_coder_3b', 'started', disk_free_bytes=shutil.disk_usage(ROOT).free)
    path = LOCAL / 'models' / FILENAME
    download(f'https://huggingface.co/{REPOSITORY}/resolve/{REVISION}/{FILENAME}', path, SIZE, SHA256)
    license_path = LOCAL / 'models' / 'qwen25_coder_3b_LICENSE.txt'
    license_url = f'https://huggingface.co/{REPOSITORY}/resolve/{REVISION}/LICENSE'
    with urllib.request.urlopen(license_url, timeout=45) as response:
        license_path.write_bytes(response.read(512 * 1024))
    manifest = {'model_id': 'Qwen2.5-Coder-3B-Instruct', 'run_slug': 'qwen25_coder_3b',
                'model_repository': REPOSITORY, 'model_revision': REVISION,
                'model_file': str(path.relative_to(ROOT)), 'model_sha256': SHA256, 'model_bytes': SIZE,
                'quantization': 'Q4_K_M', 'runtime_tag': RUNTIME_TAG,
                'license_label': 'qwen-research', 'license_url': license_url,
                'license_sha256': sha256(license_path),
                'reused_components': ['runtime', 'Python environment', 'SQLite snapshots', 'frozen 50 question IDs', 'validator and comparator']}
    (ROOT / 'outputs' / 'artifact_manifest_qwen25_coder_3b.json').write_text(json.dumps(manifest, indent=2) + '\n')
    event('setup_qwen25_coder_3b', 'completed', elapsed_seconds=time.perf_counter() - start,
          disk_free_bytes=shutil.disk_usage(ROOT).free)


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        event('setup_qwen25_coder_3b', 'failed', error_type=type(exc).__name__, message=str(exc))
        raise

# Requirements and first-time setup

This folder includes the code needed to download the public artifacts and run a fresh local demo. **The supplied installer supports Apple Silicon Macs (M-series).** It was tested on an M3 MacBook Air with 16 GB RAM, macOS 26.3.1 and Python 3.13.2. Windows, Linux and Intel Mac installation is not covered by these commands; their runtime and monitoring setup would need adaptation.

## Requirements

- Python **3.13** and Git. Install Python from the [official macOS downloads](https://www.python.org/downloads/macos/); select a 3.13 installer. For Git, follow the [official macOS instructions](https://git-scm.com/install/mac).
- **16 GB RAM recommended** to match the tested machine. Models run sequentially on four CPU threads, with GPU offloading disabled. Smaller memory configurations have not been validated.
- Start with **12 GiB free disk space**. Keeping both models, data, runtime and environment uses roughly 4 GiB; download scripts preserve at least 6 GiB free.
- Internet access for setup. No hosted model API key, Docker, PyTorch or Ollama is required. Inference stays local after setup.

Check the prerequisites in Terminal:

```sh
uname -m                       # expected: arm64
python3.13 --version
git --version
```

## Download and install

```sh
git clone https://github.com/Nikomik48/group_elly_one.git
cd group_elly_one/week3/hands-on-experiments/demo

python3.13 -m venv .local/venv
.local/venv/bin/python -m pip install -r ../requirements.txt

# Pinned llama.cpp runtime and Qwen3-1.7B Q4_K_M model.
.local/venv/bin/python bootstrap.py

# Corrected questions and five small SQLite database snapshots.
.local/venv/bin/python prepare_data.py

# Add Qwen2.5-Coder-3B-Instruct Q4_K_M.
.local/venv/bin/python download_coder.py

.local/venv/bin/python -m unittest discover -p 'test_runner.py' -v
```

For an existing checkout, pull the latest changes rather than cloning again. Run the commands inside `week3/hands-on-experiments/demo`. Downloads and the virtual environment stay in `.local/`; generated records stay in `outputs/`. Both are ignored by Git.

| Download | Size and source |
| --- | --- |
| llama.cpp `b11719` | About 12 MB compressed; [official release](https://github.com/ggml-org/llama.cpp/releases/tag/b11719), macOS ARM64 binary |
| Qwen3-1.7B Q4_K_M | 1.28 GB; [ggml-org GGUF](https://huggingface.co/ggml-org/Qwen3-1.7B-GGUF) |
| Qwen2.5-Coder-3B-Instruct Q4_K_M | 2.10 GB; [official Qwen GGUF](https://huggingface.co/Qwen/Qwen2.5-Coder-3B-Instruct-GGUF) |
| BIRD development archive | 346 MB; [original archive](https://bird-bench.oss-cn-beijing.aliyuncs.com/dev.zip). Setup also retains its 346 MB inner ZIP; only five databases, 24 MB in total, are extracted. |
| Corrected Arcwise-Plat labels | Small JSON file; [pinned source](https://github.com/uiuc-kang-lab/text_to_sql_benchmarks/blob/fe766045c55b6875a43b30e9ac7683df5582f8cf/data/arcwise_plat_full_with_diff.json) |

GB/MB above are decimal download sizes. Models and runtime are pinned to specific versions; checksums are verified. Data preparation checks the archive and label hashes, then recreates the original seed-42 selection: 50 scored questions and ten separate smoke-test IDs. Setup durations and failures are logged in `outputs/setup_events.jsonl`; manifests record artifact versions and hashes. Verified downloads are reused when setup is repeated.

## Run the demo

```sh
caffeinate -i .local/venv/bin/python demo.py --model both --question-id 765
.local/venv/bin/python demo.py --list
```

Each run prints SQL, expected and generated result tables, matching, time and token counts. It saves an HTML report and schema diagram under `outputs/demos/`. See [usage-notes.md](usage-notes.md) for single-model commands and interpretation. Saved replay requires the original run records, which are not included; **fresh installations should use live mode**.

## Common issues and terms

The packaged scripts were checked in a fresh virtual environment on the original Mac, reusing checksum-verified download caches. They recreated the same frozen question files; five evaluation tests passed. Both models also completed a live one-question demo, with matching results and unchanged database hashes. This was not an independent installation on another operating system.

- `CERTIFICATE_VERIFY_FAILED`: with the python.org installer, run its bundled **Install Certificates.command** from the Python application folder, then retry. Keep certificate verification enabled.
- Port 18917 already in use: stop the other demo/server; run only one instance at a time.
- Insufficient disk space: free space and rerun the same setup command. Interrupted `.part` downloads restart rather than resume.
- Results may differ across hardware or runtime environments. The original 10% and 24% scores describe one 50-question diagnostic run, not an expected result for every installation.

The Coder checkpoint carries the **qwen-research** license; the downloader saves its license locally. Corrected labels use CC-BY-SA-4.0, and database terms come from the original BIRD release. These instructions reproduce an academic experiment; they do not establish commercial deployment rights. Do not upload models, databases or generated records to this repository.

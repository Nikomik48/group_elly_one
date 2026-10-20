# Demo usage notes

These commands use the models, databases and Python environment already installed on this Mac. Nothing needs to be downloaded again on that machine. The commands below refer to its existing local experiment folder; cloning this repository alone does not recreate that installation. The demo runner and its inference setup are currently local; the published `utils/` folder contains evaluation utilities. Run one demo at a time; the local server uses port 18917 and stops automatically.

## Fresh inference

```sh
cd /Users/cem/Documents/ens491/experiments/qwen3_arcwise

# Both models, one after the other; first question from the original scored subset.
caffeinate -i .local/venv/bin/python demo.py --model both --question-id 765

# Or run just one model.
caffeinate -i .local/venv/bin/python demo.py --model coder --question-id 765
caffeinate -i .local/venv/bin/python demo.py --model qwen3 --question-id 765
```

`caffeinate -i` prevents idle sleep while the demo runs. Timing depends on background load; a live demonstration is not a controlled latency benchmark. CPU-only settings, prompt, warm-up, decoding limits and comparison rules match the original baseline.

The terminal shows the question, reference SQL, model SQL, expected and generated result tables, the result-match decision, generation time and token counts. Each run also saves an English `report.html`, `report.md`, `schema.mmd`, `schema.sql` and `demo.json` under `outputs/demos/`. The script prints their full paths. Open `report.html` in a browser to show the schema cards and separate sections for the queries and their outputs. Full returned rows are saved in JSON; the visible preview is limited to ten rows.

To open the newest demo report on this Mac:

```sh
.local/venv/bin/python - <<'PY'
from pathlib import Path
import subprocess
reports = list(Path('outputs/demos').glob('*/report.html'))
if not reports:
    raise SystemExit('Run a demo first.')
latest = max(reports, key=lambda p: p.parent.name)
subprocess.run(['open', str(latest.resolve())], check=True)
PY
```

## Choose a different question

```sh
.local/venv/bin/python demo.py --list
caffeinate -i .local/venv/bin/python demo.py --model both --question-id 758
```

Question 765 is an introductory count query. Both models matched it in the original run. Question 758 failed for both in that run and is useful for discussing limitations. These examples do not represent the overall 10% and 24% accuracy; any of the frozen 50 question IDs can be selected. Fresh output may differ.

## Replay saved SQL without inference

```sh
.local/venv/bin/python demo.py --mode saved --model both --question-id 765
```

This re-executes the original saved predictions against the local database. It is labelled **saved** in both the terminal and report. Generation times and tokens are historical, not fresh measurements.

## Database state and result matching

The reference SQL comes from the corrected Arcwise-Plat labels, not from another model. Both queries run on the same read-only SQLite snapshot. `results_match()` compares returned values using the local rules described in the published [evaluation README](https://github.com/Nikomik48/group_elly_one/blob/main/week3/hands-on-experiments/README.md).

SELECT queries leave stored data unchanged. The demo verifies this with before/after SHA-256 hashes. What we display after execution is the **query result table**, not a modified database. The schema diagram uses declared foreign keys only; it does not infer relationships or cardinalities.

## Repeat the full 50-question runs

These take longer and create new records without replacing the originals:

```sh
caffeinate -i .local/venv/bin/python run_experiment.py --split scored
caffeinate -i .local/venv/bin/python run_experiment.py \
  --model-manifest outputs/artifact_manifest_qwen25_coder_3b.json --split scored
```

The full runner does not produce the presentation view; use `demo.py` for the demonstration. Model inference is local, and no hosted model API is used.

# Evaluation code and scoring notes

The scores in [results.md](results.md)—**5/50 for Qwen3-1.7B and 12/50 for Qwen2.5-Coder-3B-Instruct**—were calculated with our local comparator. They have **not** been scored with the upstream evaluator below and are not official BIRD scores.

## Which code is whose?

| File | Source and purpose |
| --- | --- |
| [utils/local_evaluation.py](utils/local_evaluation.py) | Our evaluation functions, extracted unchanged from the experiment runner. Runs reference and generated SQL with execution restrictions, then compares results. A standalone command-line interface was added. |
| [utils/test_local_evaluation.py](utils/test_local_evaluation.py) | Our five existing tests for ordering, duplicates, NULLs, numbers and execution restrictions; only the import path was changed. |
| [utils/upstream_arcwise/evaluate.py](utils/upstream_arcwise/evaluate.py) | Unmodified evaluator from the UIUC Kang Lab repository accompanying the Arcwise-Plat release. This is the releasing research team's code, not our implementation or a claim of authorship by the Arcwise company. |
| [utils/SOURCES.json](utils/SOURCES.json) | Source revision, file hashes and extraction details. |

The upstream code accompanies *Pervasive Annotation Errors Break Text-to-SQL Benchmarks and Leaderboards* by Tengjun Jin, Yoojin Choi, Yuxuan Zhu and Daniel Kang. We copied it from [commit fe76604](https://github.com/uiuc-kang-lab/text_to_sql_benchmarks/blob/fe766045c55b6875a43b30e9ac7683df5582f8cf/text_to_sql_agents/evaluate.py), preserving its bytes and the repository's [CC-BY-SA-4.0 license](utils/upstream_arcwise/LICENSE). No upstream code was changed.

## What is compared?

For each question, the dataset supplies a reference SQL query. We execute it and the model's SQL on the **same SQLite snapshot**, then compare the returned tables. Different SQL statements can therefore receive the same score. The model receives the schema, question and evidence; it does not receive the reference SQL.

| Rule | Our comparator | Upstream `compare_sql()` |
| --- | --- | --- |
| Row order | Required when the reference has an outer `ORDER BY`; otherwise ignored | Always ignored |
| Duplicate rows | Counts must match | Discarded by `set()` |
| Column order | Compared by position | Compared by position |
| Column names / aliases | Ignored | Ignored |
| Numbers | Integers exact; other numeric comparisons use absolute tolerance `1e-6`, relative tolerance `1e-9` | Python equality through `set()`; no explicit tolerance |

Both methods check results on one database instance, not semantic equivalence across all possible data. Two empty outputs may match accidentally. Our ordered check can reject alternative orders among tied rows; sorting unordered numeric rows before tolerant comparison can also be conservative.

The extracted functions reproduce all 100 saved match decisions from the two runs. The five local tests pass, and both command-line interfaces were checked on a disposable database. The upstream evaluator has not yet been applied to the real runs.

**Validation is separate from correctness.** Our code uses sqlglot to permit one query, then read-only SQLite, an authorizer, a 30-second query deadline, a 35-second worker limit and a 50,000-row cap. Successful execution alone does not count as a result match. Reference failures must be resolved before reporting accuracy.

## Run the code

From this folder, using Python 3.13 (the version used locally):

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r utils/requirements.txt
.venv/bin/python -m unittest discover -s utils -p 'test_local_evaluation.py' -v
.venv/bin/python utils/local_evaluation.py \
  --db /path/to/database.sqlite --gold /path/to/gold.sql --pred /path/to/prediction.sql
```

The local command prints execution status, result matching and returned tables as JSON. A failed reference exits with status 2 and no accuracy decision.

To use the upstream evaluator:

```sh
.venv/bin/python utils/upstream_arcwise/evaluate.py \
  --pred /path/to/predictions.json --gold /path/to/gold.json \
  --db_path /path/to/databases
```

`predictions.json` maps numeric question IDs to SQL strings, e.g. `{"12": "SELECT COUNT(*) FROM vessels"}`. `gold.json` is a list with `question_id`, `db_id`, `question` and `SQL`. Databases must follow `databases/<db_id>/<db_id>.sqlite`.

For this pinned upstream script, use exactly the same IDs in both inputs and **sort the gold list by numeric question ID**: predictions are sorted internally, but gold rows retain file order. It appends to `results.txt` in the working directory. Use isolated database copies: it executes through a regular connection with rollback and does not enforce its declared timeout argument. It does not provide our execution restrictions.

Only evaluation utilities are included here. Model downloads, databases, inference setup and private data are not bundled.

# Local Text-to-SQL Baseline Results

**18 October 2026**

We evaluated Qwen3-1.7B and Qwen2.5-Coder-3B-Instruct on the same **50 corrected BIRD-derived Arcwise-Plat questions**, with ten questions from each of five small SQLite databases. Both used Q4_K_M quantization on an Apple M3 MacBook Air with 16 GB RAM, four CPU threads and no GPU offloading.

The schema, question order, evidence and evaluator were unchanged. Each question received one SQL-only generation call, without retrieval, examples or repair. The limits were 16,384 context, 12,288 input and 2,048 output tokens; decoding was greedy. Each model used its own chat template.

## Results

### Query outcomes

Each model answered the same **50 questions** once: **100 scored attempts** in total. Warm-up calls, smoke tests and later demos are excluded.

| Query outcome | Qwen3-1.7B | Qwen2.5-Coder-3B-Instruct |
| --- | ---: | ---: |
| Queries attempted | 50 | 50 |
| SQL failed validation or execution | 31 (62%) | 20 (40%) |
| SQL ran, but returned a different result | 14 (28%) | 18 (36%) |
| SQL ran and matched the reference result | **5 (10%)** | **12 (24%)** |
| SQL text identical to reference (included in matches above) | **0** | **8** |

Failed SQL + different results + matching results add up to 50 for each model. In total, **19 Qwen3 queries** and **30 Coder queries** ran successfully. All reference queries ran successfully.

**Literal SQL match** is included in the correct-result count, not added to it. It compares the recorded `predicted_sql` and `gold_sql` character for character, without normalizing whitespace, case or semicolons.

A correct result means a matching query result table. The read-only queries leave the database state unchanged.

### Time, memory and token use

| Metric | Qwen3-1.7B | Qwen2.5-Coder-3B-Instruct |
| --- | ---: | ---: |
| Generation time, median — active clock | 3.66 s | 10.17 s |
| Generation time, p95 — active clock | 10.04 s | 16.50 s |
| Sampled peak server RAM (RSS) | 3.47 GiB | 3.66 GiB |
| Total input tokens | 33,269 | 33,069 |
| Total output tokens | 2,569 | 2,911 |
| Model download and preparation | 68.1 s | 243.7 s |

RAM was sampled every 0.5 seconds; output counts include end tokens. Coder reused the existing runtime and data, and download times reflect the available connection.

## Interpretation and limitations

Coder retained all five Qwen3 matches and added seven, an observed improvement of **14 percentage points**. Unknown-column errors fell from 19 to 14. Accuracy remains low; schema understanding and value mapping should be priorities in the next experiments.

**Timing requires caution:** the Coder run spanned 36.53 minutes by UTC but 9.27 minutes on the sampled monotonic clock. The cause is unconfirmed. Reported times are provisional active-clock measurements; background load was also uncontrolled, so they do not establish a reliable speed ranking.

These are single-run diagnostic results on a small, storage-selected subset, not official BIRD scores or evidence of large-schema performance. Energy was not measured.

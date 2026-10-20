# Local Text-to-SQL Baseline Results

**18 October 2026**

We evaluated Qwen3-1.7B and Qwen2.5-Coder-3B-Instruct on the same **50 corrected BIRD-derived Arcwise-Plat questions**, with ten questions from each of five small SQLite databases. Both used Q4_K_M quantization on an Apple M3 MacBook Air with 16 GB RAM, four CPU threads and no GPU offloading.

The schema, question order, evidence and evaluator were unchanged. Each question received one SQL-only generation call, without retrieval, examples or repair. The limits were 16,384 context, 12,288 input and 2,048 output tokens; decoding was greedy. Each model used its own chat template.

## Results

| Metric | Qwen3-1.7B | Qwen2.5-Coder-3B-Instruct |
| --- | ---: | ---: |
| SQL generation attempts | 50 | 50 |
| SQL matching reference results | **5/50 (10%)** | **12/50 (24%)** |
| SQL executed successfully | 19/50 (38%) | 30/50 (60%) |
| SQL failing validation or execution | **31/50 (62%)** | **20/50 (40%)** |
| Executed SQL with nonmatching results | 14/50 (28%) | 18/50 (36%) |
| SQL text identical to reference | **0/50 (0%)** | **8/50 (16%)** |
| Generation time, median — active clock | 3.66 s | 10.17 s |
| Generation time, p95 — active clock | 10.04 s | 16.50 s |
| Sampled peak server RAM (RSS) | 3.47 GiB | 3.66 GiB |
| Total input tokens | 33,269 | 33,069 |
| Total output tokens | 2,569 | 2,911 |
| Model download and preparation | 68.1 s | 243.7 s |

There were **100 scored generation attempts in total: 50 per model on the same 50 questions**. Warm-up calls, smoke tests and later demos are excluded. A correct result means a query result table matching the reference; the read-only queries do not change the database state. Text identity compares the recorded `predicted_sql` and `gold_sql` character for character, without normalizing whitespace, case or semicolons. The eight identical Coder queries are included in its 12 result matches; Qwen3's five matches use different SQL text.

Result-match accuracy uses all 50 questions, including execution failures. All reference queries executed successfully. RAM was sampled every 0.5 seconds; output counts include end tokens. Coder reused the existing runtime and data, and download times reflect the available connection.

## Interpretation and limitations

Coder retained all five Qwen3 matches and added seven, an observed improvement of **14 percentage points**. Unknown-column errors fell from 19 to 14. Accuracy remains low; schema understanding and value mapping should be priorities in the next experiments.

**Timing requires caution:** the Coder run spanned 36.53 minutes by UTC but 9.27 minutes on the sampled monotonic clock. The cause is unconfirmed. Reported times are provisional active-clock measurements; background load was also uncontrolled, so they do not establish a reliable speed ranking.

These are single-run diagnostic results on a small, storage-selected subset, not official BIRD scores or evidence of large-schema performance. Energy was not measured.

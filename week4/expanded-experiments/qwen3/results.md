# Qwen3 Expanded Text-to-SQL Baseline

**Completed 30 October 2026 · Reported 31 October 2026**

Qwen3-1.7B completed **2,477 questions across 31 SQLite databases**, matching reference results on **15.22% of the revised BIRD subset** and **51.88% of the Spider subset**.

## Setup and data

We used Qwen3-1.7B Q4_K_M on an Apple M3 MacBook Air with 16 GiB RAM, two CPU threads, CPU-only inference and llama.cpp `b11719`. Limits were 16,384 context / 12,288 input / 2,048 output tokens; temperature 0, seed 42, thinking and prompt caching disabled. Each question received one generation attempt, without retrieval, examples, fine-tuning or repair. Prompts contained schema, question and supplied evidence; reference SQL was reserved for evaluation.

The pool contained 1,534 [revised BIRD Dev questions dated 2025-11-06](https://huggingface.co/datasets/birdsql/bird_sql_dev_20251106/tree/3c11fb193e5439b338e23677fa0aae11e8b85db9) and 1,034 [Spider 1.0 Dev questions](https://yale-lily.github.io/spider). We excluded 60 exposed IDs, 31 pilot items (one overlaps the exposed group), and one exact duplicate. Model-pretraining exposure and broader query-template overlap remain unknown.

Databases totalled **1.60 GB**; the largest was **597.75 MB**. Schemas reached 13 tables and 199 columns per database. These results do not establish enterprise-scale or maritime PostgreSQL performance.

## Query outcomes

| Outcome | Revised BIRD | Spider 1.0 | Total |
| --- | ---: | ---: | ---: |
| Questions processed | 1,463 | 1,014 | **2,477** |
| Reference evaluation failed | 4 | 2 | 6 |
| Questions with valid references | 1,459 | 1,012 | **2,471** |
| SQL matched the reference result | **222** | **525** | **747** |
| SQL executed but returned a different result | 525 | 312 | 837 |
| Generated SQL failed validation or execution | 697 | 167 | 864 |
| Generation failed before SQL execution | 15 | 8 | 23 |
| Successful SQL execution, including matches | 747 | 837 | 1,584 |
| SQL text identical to reference, included in matches | 8 | 13 | 21 |
| Result matching / valid references | **15.22%** | **51.88%** | 30.23% |

The four model outcomes sum to 2,471; six reference failures bring the total to 2,477. Execution success and identical SQL overlap with those outcomes. Report the benchmark rates separately.

Reference failures were three SQL interruptions under the execution limit, one row-cap exceedance and two UTF-8 decoding errors. They received no model call and were excluded from scoring; model failures remained. No backend failures were recorded. Counting all processed questions gives **747/2,477 = 30.16%**.

## Failure analysis

| Observed failure category | Revised BIRD | Spider 1.0 | Total |
| --- | ---: | ---: | ---: |
| Unknown column | 534 | 120 | **654** |
| SQL syntax or dialect | 69 | 9 | 78 |
| Unsupported function | 46 | 1 | 47 |
| Ambiguous column | 12 | 5 | 17 |
| Unknown table | 5 | 2 | 7 |
| Execution-policy rejection | 11 | 3 | 14 |
| SQL timeout | 3 | 3 | 6 |
| Result-row limit | 3 | 0 | 3 |
| Other SQL execution error | 14 | 24 | 38 |
| Output truncated; SQL not executed | 15 | 7 | 22 |
| Generation deadline exceeded; no SQL returned | 0 | 1 | 1 |
| Executed: duplicate counts differed | 30 | 11 | 41 |
| Executed: row ordering differed | 0 | 4 | 4 |
| Other executed result mismatch; semantic cause unreviewed | 495 | 297 | **792** |
| **Model/pipeline failures with valid references** | **1,237** | **487** | **1,724** |

Categories describe logged errors or result differences. The generation timeout was stored as `no_sql_output`; its log reports exceeding 600 seconds. Original records are unchanged. Duplicate/order differences and suspected join, filter or aggregation errors need manual review against question intent.

Unknown columns were the largest execution problem. Schema selection is a useful next experiment, although the **837 runnable but nonmatching queries** also require investigation.

## Time, memory and tokens

| Measurement | Recorded value |
| --- | ---: |
| Generation time, median, after clock exclusions | 11.89 s |
| Generation time, p95, after clock exclusions | 42.29 s |
| Questions included in generation-time percentiles | 2,332 |
| Questions flagged for UTC/active-clock disagreement | 139 |
| Maximum sampled server RSS in per-question windows | 2.06 GiB |
| Recorded input tokens | 1,749,250 |
| Recorded output tokens | 141,071 |

The Mac also ran another training job. This run used `nice 19` despite memory pressure. Latency excludes 139 clock-flagged questions and the generation timeout. Tokens cover 2,470 completed generation records, excluding warm-up and the timed-out request. RSS was sampled about once per second; it excludes compressed/swapped memory and other pipeline processes. These are shared-machine measurements, not isolated speed or total-memory requirements. Energy was not measured.

## Evaluation limits and provenance

Read-only SQLite execution used a 30-second SQL limit and 50,000-row cap. The local comparator checks counts, column positions, duplicates, NULLs and values. Row order matters with reference-level `ORDER BY`; column headings do not. Integers match exactly; other numeric tolerances are absolute `1e-6` and relative `1e-9`. We compare returned tables; database state remains unchanged.

These are **local scores on filtered development subsets**, not official BIRD or Spider test-suite scores. Single-instance matches do not prove semantic equivalence. The earlier Arcwise-Plat run used different labels, questions and CPU settings; its 10% is not a comparable before/after baseline.

All checkpoint IDs, configuration hashes, counts and token totals were checked against the completed summary. Source records remain in the local archive.

- Run ID: `20261027T072129_127519Z_qwen3_evaluation`.
- Python 3.13.2; SQLite 3.51.1; sqlglot 28.0.0.
- Model revision: `daeb8e2d528a760970442092f6bf1e55c3b659eb` in [ggml-org/Qwen3-1.7B-GGUF](https://huggingface.co/ggml-org/Qwen3-1.7B-GGUF/tree/daeb8e2d528a760970442092f6bf1e55c3b659eb).
- Frozen question-file SHA-256: `e2e4deea49111923995fe8a0ba865198766d51a7dbb75f8d26ce5a07e2b4bf81`.
- Completed summary SHA-256: `07af8bc0fbecc0c64730a33f1f870cee0710c68aa51d2f84fbc6aa9e469ed946`.

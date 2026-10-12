# Evaluation Benchmarks and KPIs

**Project:** ENS491 #417 · **Owner:** Cem Kaya · **Sources checked:** 12 October 2026

We will test correctness, resource use and safe execution on public benchmarks and Marine Transport questions. This proposal plan still needs the project database and hardware before experiments can begin.

## Select suitable public Text-to-SQL benchmarks

| Benchmark | Proposed use | Reason |
| --- | --- | --- |
| **BIRD-derived Arcwise-Plat** | Main public evaluation: 498 unique questions across 11 SQLite databases | Corrected questions, evidence and SQL. Report as modified BIRD, with its own score. [1, 2] |
| **Spider 1.0** | Secondary check: 200 development questions, sampled across databases and difficulty levels before any model run | Tests joins and aggregation across schemas. Use test-suite accuracy; publish sampled IDs and label the subset. [3] |
| **Dr.Spider** | Guide our paired paraphrase and schema-renaming tests | Supports testing changes in wording and schema names. Marine adaptations are a separate diagnostic set. [4] |
| **Spider 2.0** | Optional extension after the core experiments | Full Lite/Snow evaluation needs warehouse access and extra setup; optional for the CPU prototype. [5] |

Record dataset/database revisions, evaluator settings and licenses. Check Arcwise-Plat's corrected descriptions against the full BIRD-dev databases. Exclude the newer CRUD extension. Develop on separate training databases; public benchmark exposure during model pretraining may be unknown.

## Design the Marine Transport evaluation dataset

We propose **300 answerable questions: 100 for development and 200 for final testing**. Use the supervisor's schema and an isolated, approved database snapshot. Agree question language, units, time zones and business definitions before writing SQL. Keep confidential data out of the public repository.

| Main question type | Development / test | Example topic, subject to available data |
| --- | ---: | --- |
| Lookup and filtering | 20 / 40 | Vessel visits within a specified period |
| Joins | 20 / 40 | Cargo movements linked to vessels and ports |
| Aggregation | 20 / 40 | Cargo totals by port, with declared units |
| Time-based comparisons | 20 / 40 | Monthly changes in traffic or turnaround time |
| Nested queries or ranking | 20 / 40 | Ports above the overall average |

Equal counts cover operations rather than traffic frequencies. Tag NULLs, duplicates, empty results, date boundaries and snapshots. Empty results can be correct; forecasting without supporting data or a model is outside scope.

One member writes each question, intent and gold SQL; another verifies it. Resolve domain disagreements with the supervisor. Record ID, snapshot, family/split, tags, expected action and reviewer. Keep each query family in one split. A single port schema cannot establish unseen-schema generalization.

Add **40 ambiguous and 40 unanswerable questions**, each split 10 development / 30 test, with expected clarification/refusal [6]. Give 50 preselected test questions one paraphrase and one schema-renamed version each; update metadata and gold SQL consistently. Add edge-case database copies for 20 join/aggregation cases to detect coincidental matches [3]. These checks do not increase the 200-question accuracy sample.

## Define accuracy KPIs

| KPI | Definition |
| --- | --- |
| Execution accuracy (EX) | Correct final results / all answerable questions. Invalid SQL, timeouts, truncation and abstentions count as failures. Report public and Marine scores separately. |
| Test-suite accuracy | Fraction matching the gold results on every supplied database instance; use for Spider. Predict values ourselves and preserve DISTINCT rather than inserting gold values. [3] |
| Execution success | Queries that run within policy and time limits / all answerable questions. A runnable query can still answer the wrong question. |
| Selective accuracy and coverage | Correct answers / answered questions, together with answered / answerable questions. |
| Robustness loss | EX on the 50 original questions minus EX on each corresponding 50-question variant set, in percentage points. |

Check Marine output columns, duplicates, required ordering, NULLs and numerical tolerances. Freeze labels before evaluation; review later disputes without method names and retain original scores. Use result comparison rather than SQL string matching [3].

## Define efficiency KPIs

Measure **p50/p95 generation and end-to-end latency**, peak inference/retrieval RSS, tokens/calls, cost and energy/query. End-to-end time includes retrieval, validation, execution and repair. Report timeouts and label successful-request-only statistics. Cost/query is total billed cost divided by requests, including failures; report local electricity and offline costs separately.

Fix CPU settings and warm-up. For energy, repeat 50 questions in five blocks, vary configuration order and report gross and reliable idle-adjusted readings from RAPL or a wall meter, its measurement boundary and energy per correct answer [7]. R-VES combines correctness and SQL execution speed; it does not measure model latency or energy [1].

## Define safety and reliability KPIs

Test execution directly with **100 prohibited SQL cases**: writes/DDL, multiple statements, unauthorized reads and dangerous functions. Check false rejection on **100 allowed gold queries**. Add **20 cancellation/error tests**. Direct tests check the policy even when the model refuses. Enforce permissions and operation restrictions in isolation, beyond a SELECT prefix check [8].

Report blocked cases / 100, false rejections / 100 and controlled resource-limit outcomes / 20. Separately report correct clarification / 30 ambiguous questions, correct refusal / 30 unanswerable questions and unnecessary deferral / 200 answerable questions. Clarifications must request the labelled missing information. Check audit records for every request.

## Define defensible numeric targets

| Measure | Proposed target | Why we chose it |
| --- | --- | --- |
| Marine EX | **+5 percentage points** over the same-model baseline | Ten additional correct answers out of 200 is a useful improvement. It is a research objective, to be checked against pilot errors and available headroom. |
| Robustness loss | **No greater than the baseline's loss**, for each variant type | Directly tests whether our method improves robustness without choosing an unsupported absolute accuracy. |
| Clarification and refusal | **At least 24/30 correct in each set**; unnecessary deferral **≤10/200** | Initial usability goals: recognize most unsupported cases while limiting interruptions. Pilot-dependent, not copied from a paper. |
| CPU efficiency | Generation **p95 ≤30 s**, service RSS **≤8 GiB** | Carries forward the feasibility study's 16 GiB host and 2,048-input/256-output, one-call scenario; needs hardware testing. |
| Quantization | Observed EX loss **≤2 points**; model files **≥35% smaller** than Q8 | Published Q4/Q8 files are 1.12/1.89 GB, a 40.7% reduction [11]. The two-point limit is our proposed quality tolerance; **≥20% energy reduction** is a secondary goal needing measurement. |
| Execution policy | **100/100 prohibited cases blocked**, allowed-query false rejection **≤5/100** | A finite acceptance test for the execution layer. |
| Resource handling and logging | **20/20 controlled outcomes**, **100% of requests logged** | Software acceptance criteria. Initially configure a 5 s SQL timeout and 60 s request deadline; test cancellation within 1 s of the limit. |

Schema-alignment research supports testing for gains [9], not a predicted five-point improvement for our model. Review these proposed targets after the pilot; if EX has insufficient headroom, choose an error-reduction target before final testing. The draft's 70% accuracy, five-second response and five-joule values remain unvalidated.

Report 95% intervals: Wilson for descriptive proportions and paired resampling for accuracy differences, grouping by database or Marine query family. Under independence, worst-case Wilson half-widths are about **4.4 points for 498 questions** and **6.9 for 200**; dependence can widen uncertainty. Repeated runs do not add independent questions. Five-point gains and two-point retention may remain inconclusive. Likewise, 100/100 blocked cases is not a universal safety guarantee [10].

Compare baseline, selected method and ablation at fixed model/token/call limits. Count context overflow as failure rather than dropping questions. Report extra-call repair separately. Start with a **50-question development pilot**, reviewed dataset examples and a reproducible baseline configuration. SQL benchmarks do not validate an MDX extension.

## Sources

1. [BIRD Mini-Dev documentation](https://github.com/bird-bench/mini_dev).
2. Jin et al. (2026), [Pervasive Annotation Errors Break Text-to-SQL Benchmarks and Leaderboards](https://arxiv.org/html/2601.08778v2); [Arcwise-Plat release](https://github.com/uiuc-kang-lab/text_to_sql_benchmarks/blob/fe766045c55b6875a43b30e9ac7683df5582f8cf/data/arcwise_plat_full_with_diff.json).
3. Zhong, Yu and Klein (EMNLP 2020), [Semantic Evaluation for Text-to-SQL with Distilled Test Suites](https://aclanthology.org/2020.emnlp-main.29/); [evaluator](https://github.com/taoyds/test-suite-sql-eval); [Spider](https://yale-lily.github.io/spider).
4. Chang et al. (ICLR 2023), [Dr.Spider](https://arxiv.org/html/2301.08881v2).
5. [Spider 2.0 documentation](https://github.com/xlang-ai/Spider2).
6. Dong et al. (NAACL 2025), [PRACTIQ](https://aclanthology.org/2025.naacl-long.13/).
7. [Linux powercap measurement documentation](https://www.kernel.org/doc/html/latest/power/powercap/powercap.html).
8. SQLite documentation: [authorization](https://www.sqlite.org/c3ref/set_authorizer.html), [cancellation](https://www.sqlite.org/c3ref/progress_handler.html). Use equivalent controls for the confirmed Marine database engine.
9. Qu et al. (Findings of ACL 2024), [Before Generation, Align it!](https://aclanthology.org/2024.findings-acl.324/).
10. NIST, [confidence intervals for proportions](https://www.itl.nist.gov/div898/handbook/prc/section2/prc241.htm).
11. [Qwen2.5-Coder-1.5B publisher files](https://huggingface.co/Qwen/Qwen2.5-Coder-1.5B-Instruct-GGUF/tree/main).

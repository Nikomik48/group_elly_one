# Lightweight and CPU Deployable Model Feasibility

We plan to compare small language models on a CPU using Q4 and Q5 quantization. The memory estimates below assume a computer with 16 GiB RAM. We will check accuracy, response time and energy use once the project hardware is confirmed. We have not run these tests yet.

## Identify candidate small language models

| Model | Why we selected it | What we need to check |
| --- | --- | --- |
| [Qwen2.5-Coder-1.5B-Instruct](https://huggingface.co/Qwen/Qwen2.5-Coder-1.5B-Instruct) | Trained for coding; 1.54B parameters, Apache 2.0 | How well it generates SQL on our questions |
| [Qwen3-1.7B](https://huggingface.co/Qwen/Qwen3-1.7B) | Another small model to compare, Apache 2.0 | Whether thinking mode improves accuracy enough to justify longer responses |
| [Qwen3.5-0.8B](https://huggingface.co/Qwen/Qwen3.5-0.8B) | Smaller option if we need to stay below 1B, Apache 2.0 | Text-only runtime support and the number of parameters actually loaded |
| [SLM-SQL-1.5B](https://huggingface.co/cycloneboy/SLM-SQL-1.5B) | Trained specifically for Text-to-SQL | Model files, prompt format, license and conversion compatibility |

We would test the first two models and the 0.8B model, then select one based on accuracy, memory, response time and energy. If a strict 1B limit is required, larger models will serve only as references.

The [SLM-SQL paper](https://arxiv.org/html/2507.22478v1) reports 67.08% BIRD-dev execution accuracy for its 1.5B model. However, it uses 64 generation samples and eight merge-revision samples. Our one call experiment uses much less computation, so we cannot use that score as our expected accuracy.

## Estimate CPU inference requirements

We will start with **16 GiB RAM**, one request at a time, a **16,384-token context**, and limits of **12,288 input tokens and 2,048 output tokens**. Input includes the question, retrieved schema, descriptions, examples and chat formatting. These are upper limits; shorter questions will use fewer tokens. Both Qwen2.5-Coder-1.5B and Qwen3-1.7B support a native 32,768-token context, although this does not establish SQL accuracy at that length. We will check the full prompts on development data and increase the limits if necessary before fixing the test settings. Initial runs will generate SQL without a reasoning trace; thinking-mode runs need a separate budget. CPU measurements will use accelerator offloading disabled, with the CPU, OS and thread count recorded.

Qwen2.5-Coder-1.5B's model files are approximately **1.12 GB at Q4_K_M**, **1.29 GB at Q5_K_M** and **1.89 GB at Q8_0**. At a 16,384-token context, its estimated F16 KV cache is **448 MiB**, compared with **1,792 MiB (1.75 GiB)** for Qwen3-1.7B. These estimates cover one sequence and exclude runtime buffers, retrieval, the database and the operating system. [Model files](https://huggingface.co/Qwen/Qwen2.5-Coder-1.5B-Instruct-GGUF/tree/main), [coder configuration](https://huggingface.co/Qwen/Qwen2.5-Coder-1.5B-Instruct/raw/main/config.json), [Qwen3 configuration](https://huggingface.co/Qwen/Qwen3-1.7B/raw/main/config.json).

For illustration, at assumed speeds of 200 input tokens/s and 20 output tokens/s, generation at both token limits would take about **164 seconds**, before retrieval, validation and execution. This is a calculation, not a measured response time. We will measure typical and long requests on the selected CPU before setting a latency target. Input overflow and output cutoffs must be logged; prompts must not be silently shortened, and incomplete SQL must not be executed. [Runtime limits](https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md).

## Research model quantization options

We will compare **Q4_K_M and Q5_K_M** against F16 if it is practical to run, or Q8_0 otherwise. All versions should come from the same original model and use the same runtime, prompts, decoding settings and F16 KV cache. GGUF is the file format; weight precision and cache precision must be specified separately. [llama.cpp documentation](https://github.com/ggml-org/llama.cpp/blob/master/tools/quantize/README.md).

The coder's Q4 and Q5 files are **40.7% and 31.7% smaller than its Q8 file**, respectively. We will measure memory, speed and energy separately. If Q4 reduces accuracy too much, we will test Q5.

## Research energy-efficiency measurement

We can use **Linux RAPL** to measure supported processor domains or an external meter to measure the whole computer. The report should state which parts of the machine the readings cover. Overlapping counters should not be added together, and TDP multiplied by runtime should not be reported as measured energy. [Linux powercap documentation](https://www.kernel.org/doc/html/latest/power/powercap/powercap.html).

After warm-up, run the same 50 questions five times per configuration, vary configuration order and measure loaded-service idle power. Report total J/query and, if idle readings are stable, **(measured energy − idle power × duration) / question count**. Also divide total energy by correct answers, including energy spent on failures. Record preprocessing separately. We will report the energy difference from Q8_0; neither a five-joule limit nor a 20% saving is supported by measurements yet.

## Compare local small models with large cloud LLMs

We suggest [GPT-4.1-2025-04-14](https://developers.openai.com/api/docs/models/gpt-4.1) for the first cloud comparison. Both local and cloud models should receive the same questions, schema information and examples, use the same validator, and make one generation call per question. We will record token counts for each model, including billed reasoning tokens where applicable. Runs with extra reasoning or repair calls should be reported separately.

Compare accuracy, response time, tokens and cost. Local models keep data on the device but require electricity, hardware and maintenance. Cloud energy cannot be calculated from API prices. Start with public data; port data must follow agreed access and sharing rules. [API data controls](https://developers.openai.com/api/docs/guides/your-data).

## Proposed targets and evaluation

The settings below leave room for longer prompts and queries. Performance targets remain provisional until the development pilot. We will agree on the final thresholds with the supervisor before testing on held-out data.

| Metric | Proposed setting or target | Basis |
| --- | --- | --- |
| Context and input/output limits | 16,384 context; up to 12,288 input and 2,048 output tokens | Fits within the two Qwen models' native context; check prompt lengths and output cutoffs during development |
| Peak memory for inference and retrieval | ≤12 GiB RSS on a 16 GiB computer | Planning allowance leaving 4 GiB for the database and OS; verify total memory use on the selected machine |
| Generation and full-workflow time | Report p50 and p95; set the acceptance limit after the CPU pilot | Larger prompts need fresh measurements; 30 s is not a supported target for this workload |
| Model file size | ≥25% smaller than Q8_0 | The coder's published Q4 and Q5 files exceed this reduction; check other candidates separately |
| Loss in execution accuracy | Proposed tolerance ≤5 percentage points; prefer ≤2 points versus F16, or Q8_0 if F16 is impractical | Confirm this project tolerance after the pilot; report a 95% confidence interval for the difference |
| Energy per query | Report total and idle-adjusted J/query and percentage change versus Q8_0 | Set any required saving after measurement; also compare energy per correct answer |

**Execution accuracy (EX)** is the number of correct query results divided by all answerable test questions. Invalid queries, timeouts and abstentions count as failures. If we report accuracy only on answered questions, we must also report the fraction answered. We will measure both generation time and the time for the full workflow. Query results should be compared using the expected duplicates, ordering, NULL behavior and numerical tolerances.

Select models on development data; keep test material out of training, retrieval examples and calibration. Use separate test databases for claims about unseen schemas. Compare models on the same questions and report sample counts and 95% confidence intervals accounting for database grouping. If the confidence interval includes losses beyond the agreed tolerance, accuracy preservation remains uncertain. Keep model and inference budgets fixed for ablations. Test unsafe-query rejection and false rejection with read-only permissions enforced.

We need to confirm the hardware and parameter limit before running the pilot. These tests concern SQL; MDX or Cypher would need separate evaluation.

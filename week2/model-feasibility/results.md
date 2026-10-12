# Lightweight and CPU Deployable Model Feasibility

**Project:** ENS491 #417  
**Owner:** Cem Kaya  
**Sources checked:** 12 October 2026

We plan to compare small language models on a CPU using Q4 and Q5 quantization. The memory estimates below assume a computer with 16 GiB RAM. We will check accuracy, response time and energy use once the project hardware is confirmed. We have not run these tests yet.

## Identify candidate small language models

| Model | Why we selected it | What we need to check |
| --- | --- | --- |
| [Qwen2.5-Coder-1.5B-Instruct](https://huggingface.co/Qwen/Qwen2.5-Coder-1.5B-Instruct) | Trained for coding; 1.54B parameters, Apache 2.0 | How well it generates SQL on our questions |
| [Qwen3-1.7B](https://huggingface.co/Qwen/Qwen3-1.7B) | Another small model to compare, Apache 2.0 | Whether thinking mode improves accuracy enough to justify longer responses |
| [Qwen3.5-0.8B](https://huggingface.co/Qwen/Qwen3.5-0.8B) | Smaller option if we need to stay below 1B, Apache 2.0 | Text-only runtime support and the number of parameters actually loaded |
| [SLM-SQL-1.5B](https://huggingface.co/cycloneboy/SLM-SQL-1.5B) | Trained specifically for Text-to-SQL | Model files, prompt format, license and conversion compatibility |

We would test the first two models and the 0.8B model, then select one based on accuracy, memory, response time and energy. If the supervisor requires a strict 1B limit, larger models will serve only as references.

The [SLM-SQL paper](https://arxiv.org/html/2507.22478v1) reports 67.08% BIRD-dev execution accuracy for its 1.5B model. However, it uses 64 generation samples and eight merge-revision samples. Our one-call experiment uses much less computation, so we cannot use that score as our expected accuracy.

## Estimate CPU inference requirements

Initial tests would use **16 GiB RAM**, one request at a time, a 4,096-token context and a 2,048/256-token input/output limit. We need to confirm the CPU and OS and disable accelerator offloading.

Qwen2.5-Coder-1.5B's model files are approximately **1.12 GB at Q4_K_M**, **1.29 GB at Q5_K_M** and **1.89 GB at Q8_0**. At 4,096 tokens, its estimated F16 KV cache is **112 MiB**, compared with **448 MiB** for Qwen3-1.7B. We must also allow memory for runtime buffers, retrieval, the database and the operating system. [Model files](https://huggingface.co/Qwen/Qwen2.5-Coder-1.5B-Instruct-GGUF/tree/main), [coder configuration](https://huggingface.co/Qwen/Qwen2.5-Coder-1.5B-Instruct/raw/main/config.json), [Qwen3 configuration](https://huggingface.co/Qwen/Qwen3-1.7B/raw/main/config.json).

At assumed speeds of 200 input tokens/s and 20 output tokens/s, a 2,048/256-token request takes about **23 seconds**, plus retrieval, validation and execution. We need measured speeds to assess the draft's five-second target.

## Research model quantization options

We will compare **Q4_K_M and Q5_K_M** against F16 if it is practical to run, or Q8_0 otherwise. All versions should come from the same original model and use the same runtime, prompts, decoding settings and F16 KV cache. GGUF is the file format; weight precision and cache precision must be specified separately. [llama.cpp documentation](https://github.com/ggml-org/llama.cpp/blob/master/tools/quantize/README.md).

The coder's Q4 file is **40.7% smaller than its Q8 file**. We will measure memory, speed and energy separately. If Q4 loses more than two percentage points of accuracy, we will test Q5.

## Research energy-efficiency measurement

We can use **Linux RAPL** to measure supported processor domains or an external meter to measure the whole computer. The report should state which parts of the machine the readings cover. Overlapping counters should not be added together, and TDP multiplied by runtime should not be reported as measured energy. [Linux powercap documentation](https://www.kernel.org/doc/html/latest/power/powercap/powercap.html).

After warm-up, run the same 50 questions five times per configuration, vary configuration order and measure loaded-service idle power. Report total J/query and, if idle readings are stable, **(measured energy − idle power × duration) / question count**. Also divide total energy by correct answers, including energy spent on failures. Record preprocessing separately. The five-joule target needs measurement.

## Compare local small models with large cloud LLMs

We suggest [GPT-4.1-2025-04-14](https://developers.openai.com/api/docs/models/gpt-4.1) for the first cloud comparison. Both local and cloud models should receive the same questions, schema information and examples, use the same validator, and make one generation call per question. We will record token counts for each model, including billed reasoning tokens where applicable. Runs with extra reasoning or repair calls should be reported separately.

Compare accuracy, response time, tokens and cost. Local models keep data on the device but require electricity, hardware and maintenance. Cloud energy cannot be calculated from API prices. Start with public data; port data must follow agreed access and sharing rules. [API data controls](https://developers.openai.com/api/docs/guides/your-data).

## Proposed targets and evaluation

The following targets are a starting point. We will review them after a small development pilot and set the final values before testing on held-out data.

| Metric | Initial target | Basis |
| --- | --- | --- |
| Peak memory for inference and retrieval | ≤8 GiB RSS on a 16 GiB computer | Proposed limit; database and OS memory counted separately |
| Complete generation time after model loading | p95 ≤30 s for 2,048 input and 256 output tokens | Must be checked on the selected CPU |
| Model file size | ≥35% smaller than Q8_0 | Based on the coder's published file sizes |
| Loss in execution accuracy | ≤2 percentage points versus F16, or Q8_0 if F16 is impractical | Proposed limit; report a confidence interval for the difference |
| Mean energy/query after subtracting idle energy | ≥20% lower than Q8_0, with accuracy loss ≤2 points | Research target; savings have not been measured |

**Execution accuracy (EX)** is the number of correct query results divided by all answerable test questions. Invalid queries, timeouts and abstentions count as failures. If we report accuracy only on answered questions, we must also report the fraction answered. We will measure both generation time and the time for the full workflow. Query results should be compared using the expected duplicates, ordering, NULL behavior and numerical tolerances.

Select models on development data; keep test material out of training, retrieval examples and calibration. Use separate test databases for claims about unseen schemas. Compare models on the same questions and report sample counts and 95% confidence intervals accounting for database grouping. A wide interval may leave the two-point accuracy target unresolved. Keep model and inference budgets fixed for ablations. Test unsafe-query rejection and false rejection with read-only permissions enforced.

We need to confirm the hardware and parameter limit before running the pilot. These tests concern SQL; MDX or Cypher would need separate evaluation.

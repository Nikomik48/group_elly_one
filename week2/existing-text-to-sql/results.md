## Main Current Problems in Existing Text-to-SQL models
### 1) Database size
=> Spider 1.0 -> Avg size: 27.6 Columns + 5-10 Tables / BIRD -> Avg size: 54 Columns [viable for LLM context-window]
=> Reality: Spider 2.0 -> 812+ Columns / Beaver -> 1530 Columns + 97 Tables / Intel Telemetry -> 100+ tables + PB-sized data

Reasons:
- Tables are repetative: Same columns repeated
- Isomorphic Tables: Tables are duplicated according to Time or Region
- Composite Data: Json, Array etc. [Checking data type only is not applicable]
- Data Dictionaries are so complex [in-context noise]

Problem:
- 10K columns means 2.6m tokens [not viable for Context Window]
- Lost in the middle: in context noise -> %0 strict recall (SRR)


Solutions: 

=> Database Context Compression
- SGCF (Support-Gain Component Factorization)
- Component Factorization
- Template Hierarchy
--> Snow 2.0: 2.6m tokens -> 34.7k Tokens (%98.7 saving) / SRR: %0 -> %56.5
  

### 2) Cryptic Column Names & Semantic Layer Dimension
-> Semantic gap between business semantics and data scheme
=> Due to Cryptic names (SAP S/4HANA etc.) not viable for natural languages

Reasons:
- Cryptic & Obfuscated Identifiers -> Names like POurDocNetAmount which doesn't mean nothing -> LLM's look for semantic similarity -> Collapse
=> Spider 2.0 results;
    for clean scheme names: %86.6 
    for crypted scheme names: %10.1-%10.9
- RAG Insufficiency -> Search for semantic similarities in Retrievers
=> no semantic closure between BSTLDAT and Delivery Date
- Maps and explainations for this semantic connections are not included in dataset. It's distributed among several sources -> In context noise

Solutions: 
- Schema annotations 
- DoubleAgent / Knowledge Graph Integration
- TAHOE (Hint Bank Architecture)


### 3) Schema Linking & Inference Dimension
=> Besides Data complexity and documentation, LLM's may link the wrong columns and fail to generate SQL queries in a semantic way.

Problems:
- Schema Linking Trade-off & Excessive Pruning -> Pruning for a wrong amount
    Low pruning -> Noise 
    High Pruning -> Loss of crucial FOREIGN KEY
- Structural & Logical Errors -> 7 categories + 29 types of syntactic and semantic errors in the compile phase
- Silent Semantic Errors & Hallucinations -> No errors in compiler phase -> But errors in semantics and wrong outputs
=> Ex: No realtion between client and accout but "client.client_id = account.accoun_id" for no reason in JOIN Call

Solutions: 
- Bidirectional Schema Linking &amp; Binary Selection - RSL-SQL
- Agentic Exploration - APEX-SQL / LinkAlign
-  SQLHD / SQLens / Reflect-SQL


### 4) Input, Intent, Dialogue Quality
- This is the problem resulting from the input requested.

Reasons:
-> Natural Language & Question Ambiguity: 
- Database-sourced -> Data is not directly compatible with the database
    AmbiSchema: Biggest Town / but by size? by population?
    AmbiValue: Requested: New York City -> Data: NYC
    AmbiIntent: What is requested -> Show users by date -> order by? group by? where? which SQL query is wanted?
- LLM-sourced -> Will data be interpreted by LLM and what extent
    AmbiSource -> is the comparision limited by Database only or LLM knowledge?
    AmbiRef -> Ambiguities in request like "all user born after Vietnam War" -> by day, month or year? Which one?
- Single/Multi possible answers -> In most of the studies only single correct answer is accepted / In real world that is not the case -> Multi correct answers

-> Multi-Turn Context Drift & Aggregation Drift: User may ask several question and accepts previous ones as valid for all. However LLM's may pass them.
- Short Horizon -> Classical LLM's -> pass the previous requests as plain text. This might behaved in a different way each turn. 
- Aggregation Drift -> Continuation cues (in the SAME group, among THESE). Previous "group by/ having/ order by/ where" might be forgotten or mutated in next turns.
- Collapse in deep turns (more than 4) -> collapse in intent of user and generated SQL due to loss in semantic connection.

Solutions:
- AmbiSQL: Asking questions for clarifications
- MTSQL-R1
- Reflect-SQL


### 5) Infrastructure, Cost, Hardware & Privacy Dimension
=> Problems due to GPU and hardware limitations

Problems:
-> Agentic Cost Explosion -> Limited HW resource <-> Multiturn Agentic Cycles + Self Consistency -> Little amount of hw portion per query 
    FewShot (Single) -> 17.3 seconds in BEAVER
    DinSQL (Multi) -> 85.6 seconds
    MAC-SQL (Multi) -> 58.8 - 176 seconds
    - Also, wrong queries spends more HW source -> not applicable with database easily

-> Token Prices vs Real GPU Costs -> Token spent on 3rd party LLM Cloud Services != real usage of hw 
    - EX: FewShot and MAC-SQL spends same (13.8K token per query) in cloud, it uses 5 times more GPU than FewShot and 7 times more latency

-> Data & Schema Privacy: Some private data cannot be shared with Cloud models due to regulations, then GPU Usage becomes significant problem

Solutions:
- Mask SQL
- Lite-SQL / CodeS / SLM-SQL
- Adaptive Pipeline Router


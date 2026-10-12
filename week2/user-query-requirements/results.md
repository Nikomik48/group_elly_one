# User and Query Requirements

**Project:** ENS491 #417  

**Owner:** Furkan Yiğit Bakım  

**Date:** 12 October 2026

This document defines the expected users, their main problems, representative natural-language queries, query complexity levels, and database safety requirements for the proposed natural-language interface to the Marine Transport data system.

## Identify Target Users

The main target users are port employees who need operational information but may not know SQL, MDX, Cypher, or the underlying database structure.

- **Port and terminal operators:** vessel status, arrivals, departures, and berth information

- **Planning personnel:** schedules, berth availability, and possible conflicts

- **Operations managers:** historical and aggregated operational information

- **Technical personnel:** faster access to complex or poorly documented data

The system should allow these users to focus on the information they need instead of how that information is stored.

## Identify Customer Pain Points

A major problem is the gap between operational knowledge and database knowledge. A port employee may know exactly what information is needed but not how to retrieve it using SQL, MDX, or another query language.

Legacy systems are another important issue. Existing port systems may depend on old databases and OLAP structures that are difficult, expensive, or risky to replace. Their schemas may also contain cryptic names and incomplete documentation.

Instead of replacing these systems, our approach adds a natural-language and semantic layer on top of the existing infrastructure.

Main pain points:

- Technical query-language knowledge is required.

- Database schemas may be complex or poorly documented.

- Legacy databases can be difficult and expensive to modify.

- Operational users may depend on technical personnel for simple information requests.

- Analytical queries across multiple dimensions can be difficult to construct.

## Create Representative Natural-Language Queries

The following questions represent possible user requests. They will be adapted after the actual Marine Transport database and schema are provided.

### Simple

- "Which vessels are currently in the port?"

- "Show me next week's vessel schedule."

- "When is vessel X expected to arrive?"

- "Which berths are currently occupied?"

### Analytical

- "What was the average vessel delay last month?"

- "Which berth handled the most vessels last month?"

- "Compare average turnaround time by vessel type."

- "Which vessels were delayed by more than six hours?"

### Complex / What-if

- "If vessel X arrives eight hours late, which scheduled operations could be affected?"

- "If this vessel stays at its berth longer than planned, which upcoming schedules may conflict?"

- "Which vessel types experienced increasing delays during the last three months?"

## Classify Query Complexity

We propose four initial complexity levels:

| Level | Description | Example |
|---|---|---|
| Simple | Direct retrieval and filtering | "Which vessels arrive today?" |
| Medium | Aggregation, grouping, or simple relationships | "What was the average delay last month?" |
| Complex | Multiple entities, conditions, or OLAP dimensions | "Compare turnaround time by vessel type." |
| What-if / Reasoning | Multiple retrieval steps and reasoning over results | "What happens if vessel X arrives eight hours late?" |

This classification can later be used to measure model accuracy separately for different levels of query difficulty.

## Define Database Safety Requirements

The system should be **read-only by design**. A generated query should never be able to modify the underlying database.

Initial safety requirements:

- Use read-only database credentials.

- Block `INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `CREATE`, and other modification operations.

- Validate generated queries before execution.

- Apply minimum required database permissions.

- Limit query execution time and result size.

- Respect existing access restrictions for sensitive data.

- Ask for clarification when a request is too ambiguous to execute safely.

- Log the natural-language request and generated query for debugging and auditing.

These restrictions should be enforced by the application and database permissions, not only by instructions given to the language model.

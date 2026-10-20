# Used experiment questions

Five examples from the **18 October 2026** scored runs, one from each database. These are selected illustrations, not a representative sample or a new accuracy estimate. SQL below is copied from the original records without repair.

The models received the SQLite schema, question and supplied evidence. Reference SQL was used only for evaluation. Matching follows our [local comparator](README.md#what-is-compared).

| Question ID | Database | Qwen3-1.7B | Qwen2.5-Coder-3B-Instruct |
| --- | --- | --- | --- |
| 765 | superhero | Match | Match |
| 1312 | student_club | SQL error | Match |
| 206 | toxicology | Mismatch | Mismatch |
| 1254 | thrombosis_prediction | SQL error | Mismatch |
| 5 | california_schools | SQL error | Mismatch |

**Correct-result note:** For question **765**, both models returned the reference result (`127`). For question **1312**, only **Qwen2.5-Coder-3B-Instruct** returned the reference result (`Business`). Neither model matched the reference results for questions **206, 1254 or 5**. Here, a correct result means a matching query result table; the read-only queries leave the database state unchanged.

## 1. superhero — question 765

**Question:** How many heroes have stealth power?

**Supplied evidence:** stealth power refers to power_name = 'Stealth';

**Reference SQL**

```sql
SELECT COUNT(T1.hero_id) FROM hero_power AS T1 INNER JOIN superpower AS T2 ON T1.power_id = T2.id WHERE T2.power_name = 'Stealth'
```

**Qwen3-1.7B**

```sql
SELECT COUNT(*) FROM hero_power WHERE power_id = (SELECT id FROM superpower WHERE power_name = 'Stealth') AND hero_id IN (SELECT id FROM superhero);
```

**Qwen2.5-Coder-3B-Instruct**

Same SQL as the reference above.

**Observed:** Different SQL can produce the same result: all three queries return `127`.

## 2. student_club — question 1312

**Question:** What's Angela Sanders's major?

**Supplied evidence:** Angela Sanders is the full name; full name refers to first_name, last_name; major refers to major_name.

**Reference SQL**

```sql
SELECT T2.major_name FROM member AS T1 INNER JOIN major AS T2 ON T1.link_to_major = T2.major_id WHERE T1.first_name = 'Angela' AND T1.last_name = 'Sanders'
```

**Qwen3-1.7B**

```sql
SELECT major_name FROM major WHERE first_name = 'Angela' AND last_name = 'Sanders';
```

**Qwen2.5-Coder-3B-Instruct**

Same SQL as the reference above.

**Observed:** Qwen3 looks for member-name columns in `major`, where they do not exist. Coder uses the required join and returns `Business`.

## 3. toxicology — question 206

**Question:** What elements are in the TR004_8_9 bond atoms?

**Supplied evidence:** TR004_8_9 bond atoms refers to bond_id = 'TR004_8_9';

**Reference SQL**

```sql
SELECT DISTINCT T1.element FROM atom AS T1 INNER JOIN connected AS T2 ON T1.atom_id = T2.atom_id WHERE T2.bond_id = 'TR004_8_9'
```

**Qwen3-1.7B**

```sql
SELECT element FROM atom WHERE atom_id IN (SELECT atom_id FROM connected WHERE bond_id = 'TR004_8_9');
```

**Qwen2.5-Coder-3B-Instruct**

```sql
SELECT T1.element FROM atom AS T1 INNER JOIN connected AS T2 ON T1.atom_id = T2.atom_id WHERE T2.bond_id = 'TR004_8_9'
```

**Observed:** The reference returns one `c` row; both models return two. Our comparator preserves duplicate counts, so both fail. A set-based comparator would treat these particular outputs as equal; this illustrates why the scoring rule matters.

## 4. thrombosis_prediction — question 1254

**Question:** How many patients with at least one record indicating a normal Ig A level came to the hospital after 1990/1/1?

**Supplied evidence:** normal Ig A level refers to IGA > 80 AND IGA < 500; came to the hospital after 1990/1/1 refers to "First Date" > '1990-01-01';

**Reference SQL**

```sql
SELECT COUNT(DISTINCT T1.ID) 
 FROM Patient AS T1 INNER JOIN Laboratory AS T2 ON T1.ID = T2.ID WHERE T2.IGA > 80 AND T2.IGA < 500 AND T1."First Date" > '1990-01-01'
```

**Qwen3-1.7B**

```sql
SELECT COUNT(*) FROM Laboratory WHERE IGA > 80 AND IGA < 500 AND First Date > '1990-01-01' AND ID IN (SELECT ID FROM Patient WHERE ID IN (SELECT ID FROM Laboratory WHERE IGA > 80 AND IGA < 500 AND First Date > '1990-01-01'))
```

**Qwen2.5-Coder-3B-Instruct**

```sql
SELECT COUNT(T1.ID) FROM Patient AS T1 INNER JOIN Laboratory AS T2 ON T1.ID = T2.ID WHERE T2.IGA > 80 AND T2.IGA < 500 AND T1.`First Date` > '1990-01-01'
```

**Observed:** The reference counts 140 distinct patients. Coder counts joined records and returns 1,627. Qwen3 fails to parse the unquoted `First Date` field.

## 5. california_schools — question 5

**Question:** How many schools with an average score in Math greater than 400 in the SAT test are exclusively virtual?

**Supplied evidence:** Exclusively virtual refers to Virtual = 'F'

**Reference SQL**

```sql
SELECT COUNT(DISTINCT `T2`.`CDSCode`)
FROM `satscores` AS T1
JOIN `schools`  AS T2 ON T1.`cds` = T2.`CDSCode`
WHERE T2.`Virtual` = 'F'
  AND T1.`AvgScrMath` > 400 AND rtype = 'S'
```

**Qwen3-1.7B**

```sql
SELECT COUNT(*) FROM satscores WHERE rtype = 'SAT' AND AvgScrMath > 400 AND Virtual = 'F'
```

**Qwen2.5-Coder-3B-Instruct**

```sql
SELECT COUNT(T1.CDSCode) FROM schools AS T1 INNER JOIN satscores AS T2 ON T1.CDSCode = T2.cds WHERE T2.rtype = 'Math' AND T2.AvgScrMath > 400 AND T1.Virtual = 'F'
```

**Observed:** The reference returns 4 schools. Qwen3 uses `Virtual` in the wrong table; Coder executes but returns 0 after filtering `rtype` as `Math` rather than `S`.

## Source and reproduction

Questions and reference SQL are adapted excerpts from the [Arcwise-Plat release](https://github.com/uiuc-kang-lab/text_to_sql_benchmarks/blob/fe766045c55b6875a43b30e9ac7683df5582f8cf/data/arcwise_plat_full_with_diff.json) by the UIUC Kang Lab research team (Jin et al.), under [CC-BY-SA-4.0](utils/upstream_arcwise/LICENSE). Excerpts were selected and experimental annotations added. Model predictions come from our two original scored runs; they have not been re-scored with the upstream evaluator.

After following [setup-notes.md](setup-notes.md), enter `demo/` and choose any listed ID, for example:

```sh
caffeinate -i .local/venv/bin/python demo.py --model both --question-id 206
```

This performs fresh inference; outputs can differ from the historical examples. [usage-notes.md](usage-notes.md) explains the full demonstration.

# Epic KAN-18: Proposed System Architecture & Core Additions

This document details the features of our hybrid and multi-agent system architecture designed to overcome the bottlenecks of existing Text-to-SQL systems in enterprise port management databases, backed by metrics and academic evidence from the literature.

## KAN-19: Semantic Schema Enrichment
*   **Problem:** Unlike academic datasets, encrypted and abbreviated column names in enterprise databases are not understood by LLMs, which creates semantic schema complexity.
*   **Architectural Solution:** The database schema will not be presented to the model in its raw form; a semantic-enhanced schema enriched with conceptual schemas, data dictionaries, and sample values will be used.
*   **Academic Evidence & Metrics:**
    *   The *DoubleAgent* study proved that enriching encrypted enterprise schemas with a Knowledge Graph increases the model's Text-to-SQL accuracy from 10.9% to 43.6%.
    *   The *Prompting Strategies* research shows that adding natural language schema annotations to schemas increases the success rate from 43.3% to 56.7%.
    *   In the *SEA-SQL* model, supporting the schema with sample column values related to the question directly increases the LLM's data alignment.

## KAN-20: Historical-Query Retrieval & Case-Based Reasoning
*   **Problem:** The implicit business logic of port operations is not included in the schema; the model's zero-shot guessing of these rules causes hallucinations.
*   **Architectural Solution:** Successfully executed past query logs will be indexed in a Vector Database and brought via RAG as logical templates for new queries using "Case-Based Reasoning (CBR)".
*   **Academic Evidence & Metrics:**
    *   The *ADEPT-SQL* architecture retrieved historical query logs using a Question-SQL (QS) pool and reached 97% execution accuracy in enterprise databases, providing a 49% absolute improvement.
    *   The *CBR-to-SQL* study confirms that this approach provides immense sample efficiency even in Incomplete Database situations by separating the search for structural logic from entity alignment.
    *   Performing the sampling process with a dedicated ranking model, as in the *AID-SQL* approach, optimizes system success.

## KAN-21: Schema and Documentation RAG (Schema Pruning)
*   **Problem:** Enterprise databases are massive. For example, enterprise databases in the *BEAVER* dataset contain an average of 101.5 tables and 869.4 columns. Including the entire schema in the LLM's context window increases API costs and leads to context overload.
*   **Architectural Solution:** With "Schema Pre-Retrieval" and "Schema Pruning" mechanisms, only the Top-K tables and documentation matching the query will be filtered from the massive database and provided to the model.
*   **Academic Evidence & Metrics:**
    *   The *DoubleAgent* study shows that bringing only the most relevant (anchor) tables via vector search prevents context noise.
    *   The *SchemaRAG* framework produces SQL syntax-sensitive Schema-Aware vector embeddings using cross-attention and contrastive learning, increasing schema linking accuracy.

## KAN-22: Hybrid Architecture (SLM Fine-Tuning + RAG)
*   **Problem:** Massive monolithic LLMs cannot be used due to cost and hardware (CPU) constraints. However, RAG alone cannot solve the syntax errors of small models, while Fine-Tuning alone cannot adapt to dynamic schemas.
*   **Architectural Solution:** Small Language Models (SLMs) with 1B-3B parameters will be fine-tuned to the target SQL/MDX language using Low-Rank Adaptation (LoRA); simultaneously, a "synergistic fusion" will be created with the dynamic schema fed via RAG.
*   **Academic Evidence & Metrics:**
    *   It has been proven that while the base model accuracy was only around 5.9% in hybrid architectures integrating fine-tuning, RAG, and Knowledge Graph (KG), this synergistic fusion increased the accuracy rate to 87.5%.
    *   The *SQuaD-SQL* study demonstrates that training Small Language Models (SLMs) in the 1B-3B range with Parameter-Efficient Fine-Tuning (PEFT) methods like LoRA provides high efficiency on CPUs.

## KAN-23: Synthetic Text-to-SQL Data Generation
*   **Problem:** There is no ready-made "Natural Language - MDX/SQL" dataset available to train the target model specific to port operations (Domain Mismatch).
*   **Architectural Solution:** "Synthetic Training Data" will be produced using high-capacity LLMs over the existing enterprise schema, and the fine-tuning of the small model (SLM) will be done with this data.
*   **Academic Evidence & Metrics:**
    *   The "Structural Template Recomposition" architecture applied in the *BEAVER* research successfully synthesized high-fidelity synthetic data containing CTEs and nested queries.
    *   The *Sing-SQL* and *OmniSQL* studies confirm that in-domain synthetic data reflecting business logic is critical for target adaptation.

## KAN-24 & KAN-25: Clarification, Validation and Repair Loops
*   **Problem:** Users asking incomplete/ambiguous questions, or the model producing non-working invalid SQL or empty results.
*   **Architectural Solution:** If the question is ambiguous, the model will trigger a "Clarification" mechanism; if the generated SQL fails when executed in the database, it will self-correct in the background with an "Execute-Reflect-Correct" loop.
*   **Academic Evidence & Metrics:**
    *   The *Disambiguate first, parse later* article emphasizes the importance of resolving semantic ambiguities (ambiguity resolution) before generating SQL directly.
    *   "Dynamic Execution Adjustment" in the *SEA-SQL* study ensures that the generated query is executed via API and revised by the model according to the received error message (Execute-Reflect-Correct).
    *   The *Analytics Insight Engine* increases system robustness by using both syntactic and model-based evaluation feedback for SQL regeneration.

## KAN-26: Proposed System Architecture (Multi-Agent Workflow)
*   **Problem:** Loading all data fetching, query generation, and repair tasks onto a single Monolithic Model causes high CPU/RAM consumption and logical errors.
*   **Architectural Solution:** The system will be divided into a LangGraph-based "Agentic Workflow" architecture: Selector Agent (RAG filtering), Generator Agent (SQL construction with SLM), and Validator Agent (Error detection and Self-Correction).
*   **Academic Evidence & Metrics:**
    *   The most up-to-date systems in the literature solve intent classification, schema linking, SQL construction, and error correction tasks with Multi-Agent Workflows in a coordinated pipeline.
    *   As shown in the *SchemaRAG* model, the integration of autonomous complementary modules such as SchemaLinker, Schema-Aware Retriever (SAR), and Pareto-Optimal SQL Generator (POSG) maximizes enterprise system performance and hardware efficiency.

----------------------------------------------------------------------------------------------------------------

# Epic KAN-18: Proposed System Architecture & Core Additions

Bu doküman, kurumsal liman yönetimi veritabanlarında mevcut Text-to-SQL sistemlerinin dar boğazlarını aşmak üzere tasarlanan hibrit ve çoklu-ajan (multi-agent) sistem mimarimizin özelliklerini, literatürdeki metrikler ve akademik kanıtlarla detaylandırmaktadır.

## KAN-19: Semantic Schema Enrichment (Semantik Şema Zenginleştirme)
*   **Problem:** Akademik veri setlerinin aksine, kurumsal veritabanlarındaki şifreli ve kısaltılmış kolon isimleri LLM'ler tarafından anlaşılamamakta, bu da anlamsal şema karmaşıklığı (semantic schema complexity) yaratmaktadır.
*   **Mimari Çözüm:** Veritabanı şeması modele ham haliyle sunulmayacak; kavramsal şemalar, veri sözlükleri ve örnek değerler ile zenginleştirilmiş bir anlamsal katman (semantic-enhanced schema) kullanılacaktır.
*   **Akademik Kanıt & Metrikler:**
    *   *DoubleAgent* çalışmasında, şifreli kurumsal şemaları bir Bilgi Grafı (Knowledge Graph) ile zenginleştirmenin, modelin Text-to-SQL doğruluğunu %10.9'dan %43.6'ya çıkardığı kanıtlanmıştır.
    *   *Prompting Strategies* araştırması, şemalara doğal dilde meta açıklamalar (schema annotations) eklemenin başarı oranını %43.3'ten %56.7'ye yükselttiğini göstermektedir.
    *   *SEA-SQL* modelinde şemanın soruyla ilgili örnek kolon değerleriyle desteklenmesi, LLM'in veri hizalamasını doğrudan artırmaktadır.

## KAN-20: Historical-Query Retrieval & Case-Based Reasoning
*   **Problem:** Liman operasyonlarına ait örtük iş mantığı (implicit business logic) veritabanı şemasında yer almaz; modelin bu kuralları sıfırdan tahmin etmesi (zero-shot) halüsinasyonlara neden olur.
*   **Mimari Çözüm:** Geçmişte başarıyla çalıştırılmış sorgu logları, Vektör Veritabanında indekslenecek ve "Vakaya Dayalı Akıl Yürütme (Case-Based Reasoning - CBR)" ile yeni sorgulara mantıksal şablon olarak RAG üzerinden getirilecektir.
*   **Akademik Kanıt & Metrikler:**
    *   *ADEPT-SQL* mimarisi, Soru-SQL (QS) havuzu kullanarak tarihsel sorgu loglarını getirmiş ve kurumsal veritabanlarında %97 yürütme doğruluğuna (execution accuracy) ulaşarak %49 mutlak iyileşme sağlamıştır.
    *   *CBR-to-SQL* çalışması, bu yaklaşımın yapısal mantık arayışı ile varlık hizalamasını (entity alignment) ayırarak, veri kıtlığı (Incomplete Database) durumlarında dahi muazzam bir örneklem verimliliği sağladığını doğrular.
    *   Örneklem çekme işleminin *AID-SQL* yaklaşımındaki gibi özel bir sıralama modeli (ranking model) ile yapılması sistem başarısını optimize eder.

## KAN-21: Schema and Documentation RAG (Şema Budama)
*   **Problem:** Kurumsal veritabanları devasa boyutlardadır. Örneğin *BEAVER* veri setindeki kurumsal veritabanları ortalama 101.5 tablo ve 869.4 kolon içerir. Tüm şemayı LLM bağlamına (context window) dahil etmek API maliyetlerini artırır ve bağlam aşımına (context overload) yol açar.
*   **Mimari Çözüm:** "Şema Ön-Getirme (Schema Pre-Retrieval)" ve "Şema Budama (Schema Pruning)" mekanizmaları ile devasa veritabanından yalnızca sorguyla eşleşen Top-K tablo ve dokümantasyon filtrelenerek modele verilecektir.
*   **Akademik Kanıt & Metrikler:**
    *   *DoubleAgent* çalışması, vektör araması ile sadece en alakalı (anchor) tabloları getirmenin bağlam gürültüsünü engellediğini gösterir.
    *   *SchemaRAG* framework'ü, çapraz dikkat (cross-attention) ve zıtlık öğrenimi (contrastive learning) kullanarak SQL sözdizimine duyarlı Şema-Farkında (Schema-Aware) vektör temsilleri üretir ve şema eşleştirme doğruluğunu artırır.

## KAN-22: Hybrid Architecture (SLM Fine-Tuning + RAG)
*   **Problem:** Maliyet ve donanım (CPU) kısıtları nedeniyle devasa monolitik LLM'ler kullanılamaz. Ancak tek başına RAG küçük modellerin sözdizimi hatalarını çözemezken, tek başına Fine-Tuning dinamik şemalara adapte olamaz.
*   **Mimari Çözüm:** 1B-3B parametreli Küçük Dil Modelleri (SLM), Low-Rank Adaptation (LoRA) ile hedef SQL/MDX diline ince ayardan (Fine-Tuning) geçirilecek; eşzamanlı olarak RAG üzerinden beslenen dinamik şema ile "sinerjik bir füzyon" oluşturulacaktır.
*   **Akademik Kanıt & Metrikler:**
    *   İnce ayar, RAG ve Bilgi Grafı (KG) entegrasyonunu içeren hibrit mimarilerde baz modelin doğruluğu sadece %5.9 seviyelerindeyken, bu sinerjik füzyon ile doğruluk oranının %87.5 seviyelerine çıktığı kanıtlanmıştır.
    *   *SQuaD-SQL* çalışması, 1B-3B aralığındaki Küçük Dil Modellerinin (SLM) LoRA gibi parametre-verimli yöntemlerle (PEFT) eğitilmesinin CPU üzerinde yüksek verimlilik sağladığını göstermektedir.

## KAN-23: Synthetic Text-to-SQL Data Generation
*   **Problem:** Liman operasyonlarına özgü hedef modelin eğitilmesi için hazır "Doğal Dil - MDX/SQL" veri seti bulunmamaktadır (Domain Mismatch).
*   **Mimari Çözüm:** Yüksek kapasiteli LLM'ler kullanılarak mevcut kurumsal şema üzerinden "Sentetik Eğitim Verisi" üretilecek ve küçük modelin (SLM) ince ayarı bu verilerle yapılacaktır.
*   **Akademik Kanıt & Metrikler:**
    *   *BEAVER* araştırmasında uygulanan "Yapısal Şablon Yeniden Birleştirme (Structural Template Recomposition)" mimarisi, CTE ve iç içe geçmiş sorgular barındıran yüksek aslına uygunluğa (high-fidelity) sahip sentetik veriler sentezlemeyi başarmıştır.
    *   *Sing-SQL* ve *OmniSQL* çalışmaları, kurumsal iş mantığını (business logic) yansıtan alana özgü (in-domain) sentetik verilerin hedef adaptasyonda kritik olduğunu doğrular.

## KAN-24 & KAN-25: Clarification, Validation and Repair Loops
*   **Problem:** Kullanıcıların eksik/belirsiz sorular sorması veya modelin çalışmayan geçersiz (invalid) SQL yahut boş sonuç (empty result) üretmesi.
*   **Mimari Çözüm:** Soru belirsizse model "Açıklama İsteme (Clarification)" mekanizmasını tetikleyecek; üretilen SQL veritabanında çalıştırıldığında hata verirse "Çalıştır-Düşün-Düzelt" döngüsüyle arka planda kendi kendini onaracaktır.
*   **Akademik Kanıt & Metrikler:**
    *   *Disambiguate first, parse later* makalesi, doğrudan SQL üretmek yerine önce anlamsal belirsizliklerin (ambiguity resolution) çözülmesinin önemini vurgular.
    *   *SEA-SQL* çalışmasındaki "Dinamik Yürütme Ayarlaması (Dynamic Execution Adjustment)", üretilen sorgunun API üzerinden çalıştırılıp alınan hata mesajına göre model tarafından revize edilmesini (Execute-Reflect-Correct) sağlar.
    *   *Analytics Insight Engine*, hem sözdizimsel hem de model tabanlı değerlendirme geri bildirimlerini SQL rejenerasyonu (SQL regeneration) için kullanarak sistem dayanıklılığını artırır.
## KAN-26: Proposed System Architecture (Multi-Agent Workflow)
*   **Problem:** Veri getirme, sorgu üretme ve onarım işlemlerinin tamamının tek bir monolitik modele (Monolithic Model) yüklenmesi yüksek CPU/RAM tüketimine ve mantıksal hatalara yol açar.
*   **Mimari Çözüm:** Sistem LangGraph tabanlı "Modüler Çoklu-Ajan (Agentic Workflow)" mimarisine bölünecektir: Seçici Ajan (RAG filtrelemesi), Üretici Ajan (SLM ile SQL inşası) ve Doğrulayıcı Ajan (Hata tespiti ve Self-Correction).
*   **Akademik Kanıt & Metrikler:**
    *   Literatürdeki en güncel sistemler; niyet sınıflandırma, şema bağlama, SQL inşası ve hata düzeltme görevlerini koordine edilmiş bir iş hattında çoklu ajanlarla (Multi-Agent Workflows) çözmektedir.
    *   *SchemaRAG* modelinde gösterildiği üzere, Şema Bağlayıcı (SchemaLinker), Şema-Farkında Getirici (SAR) ve Optimum SQL Üretici (POSG) gibi birbirini tamamlayan otonom modüllerin entegrasyonu, kurumsal sistem performansını ve donanım verimliliğini maksimize eder.

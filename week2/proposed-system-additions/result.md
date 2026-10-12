# Epic KAN-18: Proposed System Architecture & Core Additions

> This document presents the theoretical foundation of our **Modular Multi-Agent** and **Hybrid (SLM + RAG + Fine-Tuning)** system architecture, designed to overcome the semantic and hardware bottlenecks experienced by existing Text-to-SQL systems in Enterprise Port Management databases. Each proposed architectural component is grounded in empirical findings and comparative analyses from the most recent literature.

---

## KAN-19: Semantic Schema Enrichment

> **Objective:** To transform cryptic physical column names into enterprise business concepts comprehensible to LLMs.

*   **Architectural Bottleneck (Problem):**
    Unlike traditional academic datasets, enterprise ERP and port systems possess cryptic naming conventions that are not directly understandable by humans. LLMs processing these schemas directly with a "zero-shot" approach creates semantic schema complexity and causes incorrect table/column matches.
*   **System Integration (Solution):**
    Instead of providing schemas to the model with their raw physical names, a **Semantic Layer** enriched with conceptual schemas, data dictionaries, and sample column values will be utilized.
*   **Academic Grounding & Literature Support:**
    *   As proven in the [DoubleAgent (NOVAS26_14)](Resources/NOVAS26_14.pdf) study, enriching cryptic enterprise schemas with an Enterprise Knowledge Graph increases the model's SQL generation accuracy from 10.9% to 43.6%.
    *   As stated in the [A Schema-Driven Prompt Engineering Approach](Resources/A_Schema-Driven_Prompt_Engineering_Approach_for_Data-Centric_LLM_Tasks.pdf) paper, guiding schemas with metadata and ontological references prevents conceptual confusion.
    *   This approach will be combined with the "schema annotations" principle from the [Prompting Strategies for Enterprise Text-to-SQL](Resources/NOVAS26_16.pdf) study to maximize the model's data alignment.

---

## KAN-20: Historical-Query Retrieval & Case-Based Reasoning

> **Objective:** To prevent the model from guessing enterprise business rules from scratch and to enable it to use past experiences as logical templates.

*   **Architectural Bottleneck (Problem):**
    Implicit business logic in port operations, such as "berth waiting time" or "active vessel tonnage", is not located at the DDL (Data Definition Language) level in the database schema. The model's attempt to derive these complex metrics by solely looking at table names leads to critical hallucinations.
*   **System Integration (Solution):**
    To resolve this ontological deficiency, our system will employ a **Case-Based Reasoning (CBR)** architecture. Successfully executed historical query logs will be indexed in a Vector Database (RAG) and presented to the model as logical templates (few-shot exemplars).
*   **Academic Grounding & Literature Support:**
    *   According to the [CBR-to-SQL](Resources/CBR-to-SQL-%20Rethinking%20Retrieval-based%20Text-to-SQL%20using%20Case-based%20Reasoning%20in%20the%20Healthcare%20Domain.pdf) paper, the CBR architecture provides immense sample efficiency even in Incomplete Database scenarios by splitting "structural logic retrieval" and "entity alignment" into two independent phases.
    *   The system will be based on the Question-SQL (QS) pool proposed in the [ADEPT-SQL](Resources/ADEPT-SQLHighPerformanceText2SQLApplication4RealWorldEnterpriseLevelDatabases.pdf) study.
    *   As emphasized in the [End-to-end Text-to-SQL Generation](Resources/End-to-end%20Text-to-SQL%20Generation%20within%20an%20Analytics%20Insight%20Engine.pdf) research, historical query logs will be parsed into complex sub-queries (CTEs) and fed into the system as an external knowledge set; this selection will be optimized with a dedicated "ranking model", similar to the [AID-SQL](Resources/AID-SQL_Adaptive_In-Context_Learning_of_Text-to-SQL_with_Difficulty-Aware_Instruction_and_Retrieval-Augmented_Generation.pdf) approach.

---

## KAN-21: Context-Aware Schema and Documentation RAG

> **Objective:** To prevent context overload and token costs by avoiding feeding the entire schema to the LLM in massive databases.

*   **Architectural Bottleneck (Problem):**
    Enterprise databases examined in the [BEAVER Benchmark](Resources/BEAVER-%20An%20Enterprise%20Benchmark%20for%20Text-to-SQL.pdf) dataset contain an average of 101.5 tables and 869.4 columns. Compressing the entire schema into a monolithic context window causes the model to get lost among irrelevant tables and leads to an exponential increase in API costs.
*   **System Integration (Solution):**
    By establishing "Schema Pre-Retrieval" and "Schema Pruning" mechanisms, only the Top-K tables matching the query and the documentation belonging to these tables will be filtered via RAG and provided to the model.
*   **Academic Grounding & Literature Support:**
    *   To overcome this bottleneck, the enterprise table retrieval mechanisms detailed in the [CSR-RAG](Resources/CSR-RAG-%20AnEfficient%20Retrieval%20System%20for%20Text-to-SQL%20on%20the%20Enterprise%20Scale.pdf) study will be utilized.
    *   Instead of traditional RAG, a context-aware bidirectional retrieval infrastructure proposed in the [Rethinking Schema Linking](Resources/Rethinking%20Schema%20Linking-%20A%20Context-Aware%20Bidirectional%20Retrieval%20Approach.pdf) paper will be built.
    *   To minimize the CPU processing load, strategies from the [AST-based Ranking and Schema Pruning](Resources/Improving%20Retrieval-augmented%20Text-to-SQL%20with%20AST-based%20Ranking%20and%20Schema%20Pruning.pdf) research will be deployed; utilizing SQL-aware vector representations based on "cross-attention" shown in the [SchemaRAG](Resources/SchemaRAGSchemaAwareRetrievalAugmentedGenerationFramework4Text2SQL.pdf.pdf) model, only the most relevant sub-schemas will be transferred to the model.

---

## KAN-22: Hybrid Architecture (SLM Fine-Tuning + RAG Synergy)

> **Objective:** To combine static (Fine-Tuning) and dynamic (RAG) methods to elevate small, CPU-deployable models to a level capable of high-quality enterprise generation.

*   **Architectural Bottleneck (Problem):**
    Using only Prompting (In-Context Learning) is structurally insufficient for small models in the 1B-3B range; while solely relying on Fine-Tuning causes the model to become static, failing to adapt to dynamic changes in the database schema.
*   **System Integration (Solution):**
    To ensure hardware (CPU) constraints and cost efficiency, small models will be trained on the domain-specific syntax using the Low-Rank Adaptation (LoRA) technique, and the missing up-to-date enterprise knowledge will be simultaneously fed via RAG.
*   **Academic Grounding & Literature Support:**
    *   Small Language Models (SLMs) with 1.5B - 3B parameters, proposed in the [SQuaD-SQL](Resources/SQuaD-SQL-%20Efficient%20Text-to-SQL%20with%20Small%20Language%20Models%20via%20LLM-Guided%20Knowledge%20Distillation.pdf) study, will be trained on the port domain in a parameter-efficient manner (PEFT) using the methods in the [Schema On The Inside](Resources/SchemaOnTheInsideATwoPhaseFineTuning%20Method4High-EfficiencyText2SQL%20At%20Scale.pdf) paper.
    *   To overcome the structural limitations of small models, the **"Synergistic Fusion of RAG and Fine-Tuning"** architecture, whose superiority has been mathematically proven in the [Unveiling the Power of LLMs](Resources/Unveiling_the_Power_of_Large_Language_Models_A_Comparative_Study_of_....pdf) and [Domain-Specific SQL Generation](Resources/Domain-specific%20SQL%20generation%20with%20LLMs.pdf) studies, will be adopted.

---

## KAN-23: Synthetic Text-to-SQL Data Generation

> **Objective:** To overcome the Domain Mismatch problem by synthetically generating a high-quality port-SQL dataset from scratch to train the target model.

*   **Architectural Bottleneck (Problem):**
    The absence of an off-the-shelf "Natural Language - MDX/SQL" training dataset specific to the port transportation domain creates a problem known in the literature as "Domain Mismatch", causing the model to fail in enterprise performance.
*   **System Integration (Solution):**
    "Synthetic Training Data" harboring complex analytical queries, CTEs, and sub-queries will be generated over the existing enterprise schema using high-capacity leading LLMs.
*   **Academic Grounding & Literature Support:**
    *   To overcome the data scarcity problem, enterprise "Synthetic Training Data" will be synthesized using large language models as stated in the [OmniSQL](Resources/OmniSQL-%20Synthesizing%20High-quality%20Text-to-SQL%20Data%20at%20Scale.pdf) and [Business Logic-Driven Text-to-SQL](Resources/Business%20Logic-Driven%20Text-to-SQL%20Data%20Synthesis%20for%20Business%20Intelligence.pdf) studies.
    *   During the generation process, the **Structural Template Recomposition** technique introduced in the BEAVER paper will be used, and similar to the [SING-SQL](Resources/SING-SQL-%20A%20Synthetic%20Data%20Generation%20Framework%20for%20In-Domain%20Text-to-SQL.pdf) approach, high-coverage, nested queries will be synthesized on our target database.

---

## KAN-24 & KAN-25: Clarification Mechanisms, Validation and Repair Loops

> **Objective:** To create a robust, self-correcting closed-loop system by filtering out user errors and model hallucinations.

*   **Architectural Bottleneck (Problem):**
    Incomplete user queries or invalid syntax/empty result SQL commands autonomously generated by the LLM lead to critical data errors and business interruptions in enterprise systems.
*   **System Integration (Solution):**
    If a query is semantically ambiguous, the model will ask the user for "clarification". If the generated SQL yields an error when executed in the database, the system will not return the error directly to the user but will self-correct in the background via an "Execute-Reflect-Correct" loop.
*   **Academic Grounding & Literature Support:**
    *   In cases of semantic ambiguities, the system follows the "resolve ambiguity first, parse later" principle from the [Disambiguate First, Parse Later](Resources/Disambiguate%20First,%20Parse%20Later-%20Generating%20Interpretations%20for%20Ambiguity%20Resolution.pdf) study. To conserve CPU resources, this process will be coordinated via SLMs as proven in the [Small Language Model Helps Resolve Semantic Ambiguity](Resources/Small%20Language%20Model%20Helps%20Resolve%20Semantic%20Ambiguity%20of%20LLM%20Prompt.pdf) paper.
    *   If the generated SQL fails in the database, the "Dynamic Execution Adjustment" from the [SEA-SQL](Resources/SEA-SQL-SemanticEnhancedText2SQLwith%20adaptiveRefinement.pdf) study and "Execution-based Feedback" algorithms from the [ExCoT](Resources/ExCoT-%20Optimizing%20Reasoning%20for%20Text-to-SQL%20with%20Execution%20Feedback.pdf) paper will be activated, enabling the model to self-correct.

---

## KAN-26: Proposed System Architecture (Multi-Agent Workflow)

> **Objective:** To maximize performance, speed, and transparency by distributing all designed solution algorithms to collaborative and autonomous agents.

*   **Architectural Bottleneck (Problem):**
    Assigning all data reading, schema filtering, SQL synthesizing, and error repair steps to a single Monolithic Model causes high error propagation, massive RAM consumption, and sluggishness.
*   **System Integration (Solution):**
    The system will be divided into the following autonomous and collaborative agents using the LangGraph infrastructure:
    1.  **Selector Agent:** RAG-based context-aware schema and historical query retrieval.
    2.  **Generator Agent:** MDX/SQL construction with a CPU-deployable small model fine-tuned with domain-specific synthetic data.
    3.  **Validator/Refiner Agent:** A supervisor mechanism that performs SQL execution tests and triggers the "Self-Correction" loop for syntax errors or semantic gaps.
*   **Academic Grounding & Literature Support:**
    *   As systematically proven in the [AI Agentic Workflow Implementations](Resources/Text_to_SQL_AI_Agentic_Workflow_Implementations_A_Systematic_Literature_Review.pdf) study, modern Text-to-SQL systems solve intent classification, schema linking, SQL construction, and error correction tasks in a coordinated Multi-Agent Workflow.
    *   As shown in the [SchemaRAG](Resources/SchemaRAGSchemaAwareRetrievalAugmentedGenerationFramework4Text2SQL.pdf.pdf) and [SQLFixAgent](Resources/SQLFixAgentTowardsSemanticAccurateText2SQL%20ParsingViaConsistency-Enhanced%20Multi-Agent%20Collaboration.pdf) models, the integration of complementary autonomous modules maximizes enterprise system performance and hardware efficiency. This modular decoupling ensures the flexibility and transparency of our system.

------------------------------------------------

# Epic KAN-18: Proposed System Architecture & Core Additions

> Bu dokümanda kurumsal liman yönetimi (Enterprise Port Management) veritabanlarında mevcut Text-to-SQL sistemlerinin yaşadığı anlamsal ve donanımsal darboğazları aşmak üzere tasarlanan **Modüler Çoklu-Ajan (Multi-Agent)** ve **Hibrit (SLM + RAG + Fine-Tuning)** sistem mimarimizin teorik altyapısı sunulmaktadır. Önerilen her bir mimari bileşen, en güncel literatürdeki ampirik bulgular ve kıyaslamalı analizler ışığında temellendirilmiştir.

---

## KAN-19: Semantic Schema Enrichment (Semantik Şema Zenginleştirme)

> **Amaç:** Anlamsız fiziksel kolon isimlerini, LLM'in anlayabileceği kurumsal iş kavramlarına dönüştürmek.

*   **Mimari Darboğaz (Problem):**
    Geleneksel akademik veri setlerinin aksine, kurumsal ERP ve liman sistemleri insan tarafından doğrudan anlaşılamayan, şifreli ve kısaltılmış kolon isimlendirmelerine (cryptic naming conventions) sahiptir. Büyük Dil Modellerinin (LLM) bu şemaları "zero-shot" mantığıyla doğrudan işlemesi, anlamsal şema karmaşıklığı (semantic schema complexity) yaratmakta ve yanlış tablo/kolon eşleşmelerine neden olmaktadır.
*   **Sistem Entegrasyonu (Çözüm):**
    Şemaların salt fiziksel isimleriyle modele verilmesi yerine; kavramsal şemalar (conceptual schemas), veri sözlükleri ve örnek kolon değerleriyle zenginleştirilmiş bir **Anlamsal Katman (Semantic Layer)** kullanılacaktır.
*   **Akademik Temellendirme & Literatür Desteği:**
    *   [DoubleAgent (NOVAS26_14)](Resources/NOVAS26_14.pdf) çalışmasında kanıtlandığı üzere, şifreli kurumsal şemaları bir Kurumsal Bilgi Grafı (Enterprise Knowledge Graph) ile zenginleştirmek, modelin SQL üretim doğruluğunu %10.9'dan %43.6'ya çıkarmaktadır.
    *   [A Schema-Driven Prompt Engineering Approach](Resources/A_Schema-Driven_Prompt_Engineering_Approach_for_Data-Centric_LLM_Tasks.pdf) makalesinde belirtildiği gibi, şemaların meta veriler ve ontolojik referanslarla yönlendirilmesi kavram karmaşasını engeller.
    *   Bu yaklaşım, [Prompting Strategies for Enterprise Text-to-SQL](Resources/NOVAS26_16.pdf) çalışmasındaki "schema annotations (şema açıklamaları)" prensibiyle harmanlanarak modelin veri hizalaması (data alignment) maksimize edilecektir.

---

## KAN-20: Historical-Query Retrieval & Case-Based Reasoning

> **Amaç:** Modelin kurumsal iş kurallarını sıfırdan tahmin etmesini engellemek ve geçmiş tecrübeleri şablon olarak kullanmasını sağlamak.

*   **Mimari Darboğaz (Problem):**
    Liman operasyonlarındaki "rıhtım bekleme süresi" veya "aktif gemi tonajı" gibi örtük iş mantıkları (implicit business logic) veritabanı şemasında DDL (Data Definition Language) seviyesinde yer almaz. Modelin bu kompleks metrikleri sadece tablo isimlerine bakarak türetmeye çalışması kritik halüsinasyonlara yol açar.
*   **Sistem Entegrasyonu (Çözüm):**
    Bu ontolojik eksikliği gidermek için sistemimiz, **Vakaya Dayalı Akıl Yürütme (Case-Based Reasoning - CBR)** mimarisini kullanacaktır. Geçmişte başarıyla çalıştırılmış sorgu logları, Vektör Veritabanında (RAG) indekslenecek ve mantıksal şablon (few-shot exemplar) olarak modele sunulacaktır.
*   **Akademik Temellendirme & Literatür Desteği:**
    *   [CBR-to-SQL](Resources/CBR-to-SQL-%20Rethinking%20Retrieval-based%20Text-to-SQL%20using%20Case-based%20Reasoning%20in%20the%20Healthcare%20Domain.pdf) makalesine göre; CBR mimarisi, "yapısal mantık arayışı" ile "varlık hizalamasını (entity alignment)" iki bağımsız faza bölerek veri kıtlığı (Incomplete Database) durumlarında dahi muazzam bir örneklem verimliliği sağlar.
    *   Sistem, [ADEPT-SQL](Resources/ADEPT-SQLHighPerformanceText2SQLApplication4RealWorldEnterpriseLevelDatabases.pdf) çalışmasında önerilen Soru-SQL (QS) havuzunu baz alacaktır.
    *   [End-to-end Text-to-SQL Generation](Resources/End-to-end%20Text-to-SQL%20Generation%20within%20an%20Analytics%20Insight%20Engine.pdf) araştırmasında vurgulandığı gibi, tarihsel sorgu logları karmaşık alt sorgulara (CTE) ayrılarak dış bilgi seti (external knowledge set) olarak sisteme beslenecek; bu seçim [AID-SQL](Resources/AID-SQL_Adaptive_In-Context_Learning_of_Text-to-SQL_with_Difficulty-Aware_Instruction_and_Retrieval-Augmented_Generation.pdf) yaklaşımındaki gibi özel bir "sıralama modeli (ranking model)" ile optimize edilecektir.

---

## KAN-21: Context-Aware Schema and Documentation RAG

> **Amaç:** Devasa veritabanlarında tüm şemayı LLM'e vermekten kaçınarak bağlam aşımını (context overload) ve token maliyetlerini engellemek.

*   **Mimari Darboğaz (Problem):**
    [BEAVER Benchmark](Resources/BEAVER-%20An%20Enterprise%20Benchmark%20for%20Text-to-SQL.pdf) veri setinde incelenen kurumsal veritabanları ortalama 101.5 tablo ve 869.4 kolon içerir. Tüm şemanın monolitik bir bağlam penceresine (context window) sıkıştırılması, modelin ilgisiz tablolar arasında kaybolmasına ve API maliyetlerinin eksponansiyel artmasına sebep olur.
*   **Sistem Entegrasyonu (Çözüm):**
    "Şema Ön-Getirme (Schema Pre-Retrieval)" ve "Şema Budama (Schema Pruning)" mekanizmaları kurularak devasa veritabanından yalnızca sorguyla eşleşen Top-K tablo ve bu tablolara ait dokümantasyonlar RAG üzerinden filtrelenerek modele verilecektir.
*   **Akademik Temellendirme & Literatür Desteği:**
    *   Bu darboğazı aşmak için, [CSR-RAG](Resources/CSR-RAG-%20AnEfficient%20Retrieval%20System%20for%20Text-to-SQL%20on%20the%20Enterprise%20Scale.pdf) çalışmasında detaylandırılan kurumsal tablo getirme (table retrieval) mekanizmaları kullanılacaktır.
    *   Geleneksel RAG yerine, [Rethinking Schema Linking](Resources/Rethinking%20Schema%20Linking-%20A%20Context-Aware%20Bidirectional%20Retrieval%20Approach.pdf) makalesinde önerilen bağlama duyarlı iki yönlü getirme (context-aware bidirectional retrieval) altyapısı inşa edilecektir.
    *   CPU işlem yükünü minimize etmek için [AST-based Ranking and Schema Pruning](Resources/Improving%20Retrieval-augmented%20Text-to-SQL%20with%20AST-based%20Ranking%20and%20Schema%20Pruning.pdf) araştırmasındaki stratejiler devreye alınacak; [SchemaRAG](Resources/SchemaRAGSchemaAwareRetrievalAugmentedGenerationFramework4Text2SQL.pdf.pdf) modelinde gösterilen "çapraz dikkat (cross-attention)" tabanlı SQL-farkında vektör temsilleriyle yalnızca en ilgili alt-şemalar (sub-schemas) modele aktarılacaktır.

---

## KAN-22: Hybrid Architecture (SLM Fine-Tuning + RAG Synergy)

> **Amaç:** CPU üzerinde çalışabilen küçük modelleri, yüksek kaliteli kurumsal üretim yapabilecek seviyeye çıkarmak için statik (Fine-Tuning) ve dinamik (RAG) yöntemleri birleştirmek.

*   **Mimari Darboğaz (Problem):**
    Sadece Prompting (In-Context Learning) kullanmak 1B-3B aralığındaki küçük modeller için yapısal olarak yetersiz kalırken; sadece İnce Ayar (Fine-Tuning) yapmak modelin statikleşmesine ve veritabanı şemasındaki dinamik değişikliklere adapte olamamasına yol açmaktadır.
*   **Sistem Entegrasyonu (Çözüm):**
    Donanım (CPU) kısıtlarımızı ve maliyet verimliliğimizi sağlamak adına, küçük modeller Low-Rank Adaptation (LoRA) tekniğiyle alana özgü sözdizimine eğitilecek ve eksik kalan kurumsal güncel bilgi eşzamanlı olarak RAG üzerinden beslenecektir.
*   **Akademik Temellendirme & Literatür Desteği:**
    *   [SQuaD-SQL](Resources/SQuaD-SQL-%20Efficient%20Text-to-SQL%20with%20Small%20Language%20Models%20via%20LLM-Guided%20Knowledge%20Distillation.pdf) çalışmasında önerilen 1.5B - 3B parametreli Küçük Dil Modelleri (SLM), [Schema On The Inside](Resources/SchemaOnTheInsideATwoPhaseFineTuning%20Method4High-EfficiencyText2SQL%20At%20Scale.pdf) makalesindeki yöntemlerle parametre-verimli (PEFT) olarak liman domainine eğitilecektir.
    *   Küçük modellerin yapısal kısıtlarını aşmak için, [Unveiling the Power of LLMs](Resources/Unveiling_the_Power_of_Large_Language_Models_A_Comparative_Study_of_....pdf) ve [Domain-Specific SQL Generation](Resources/Domain-specific%20SQL%20generation%20with%20LLMs.pdf) çalışmalarında üstünlüğü matematiksel olarak kanıtlanmış olan **"RAG ve İnce Ayarın Sinerjik Füzyonu (Synergistic Fusion)"** mimarisi benimsenecektir.

---

## KAN-23: Synthetic Text-to-SQL Data Generation

> **Amaç:** Alan Uyuşmazlığı (Domain Mismatch) problemini aşarak, hedef modeli eğitecek yüksek kaliteli liman-SQL veri setini sıfırdan sentetik olarak üretmek.

*   **Mimari Darboğaz (Problem):**
    Liman taşımacılığı alanına özgü hazır bir "Doğal Dil - MDX/SQL" eğitim veri setinin bulunmaması, literatürde "Alan Uyuşmazlığı" olarak bilinen sorunu doğurmakta ve modelin kurumsal performansta başarısız olmasına neden olmaktadır.
*   **Sistem Entegrasyonu (Çözüm):**
    Yüksek kapasiteli öncü LLM'ler kullanılarak mevcut kurumsal şema üzerinden karmaşık analitik sorular, CTE ve alt sorgular barındıran "Sentetik Eğitim Verisi" üretilecektir.
*   **Akademik Temellendirme & Literatür Desteği:**
    *   Veri kıtlığı problemini aşmak için, [OmniSQL](Resources/OmniSQL-%20Synthesizing%20High-quality%20Text-to-SQL%20Data%20at%20Scale.pdf) ve [Business Logic-Driven Text-to-SQL](Resources/Business%20Logic-Driven%20Text-to-SQL%20Data%20Synthesis%20for%20Business%20Intelligence.pdf) çalışmalarında belirtildiği üzere büyük dil modelleri kullanılarak kurumsal "Sentetik Eğitim Verisi" sentezlenecektir.
    *   Üretim sürecinde, BEAVER makalesinde tanıtılan **Yapısal Şablon Yeniden Birleştirme (Structural Template Recomposition)** tekniği kullanılacak ve [SING-SQL](Resources/SING-SQL-%20A%20Synthetic%20Data%20Generation%20Framework%20for%20In-Domain%20Text-to-SQL.pdf) yaklaşımına benzer şekilde hedef veritabanımız (target database) üzerinde yüksek kapsama sahip (high-coverage), iç içe geçmiş (nested) sorgular sentezlenecektir.

---

## KAN-24 & KAN-25: Clarification Mechanisms, Validation and Repair Loops

> **Amaç:** Kullanıcı hatalarını ve model halüsinasyonlarını filtreleyerek dayanıklı (robust), kendi kendini onaran kapalı devre bir sistem yaratmak.

*   **Mimari Darboğaz (Problem):**
    Kullanıcı sorgularındaki eksiklikler veya LLM'in otonom olarak ürettiği çalışmayan (invalid syntax) / boş sonuç (empty result) döndüren SQL komutları, kurumsal sistemlerde kritik veri hatalarına ve iş kesintilerine yol açar.
*   **Sistem Entegrasyonu (Çözüm):**
    Sorgu anlamsal olarak belirsizse model kullanıcıdan "açıklama (clarification)" isteyecektir. Üretilen SQL veritabanında çalıştırıldığında hata verirse sistem doğrudan kullanıcıya hata dönmek yerine arka planda "Çalıştır-Düşün-Düzelt (Execute-Reflect-Correct)" döngüsüyle kendi kendini onaracaktır.
*   **Akademik Temellendirme & Literatür Desteği:**
    *   Anlamsal belirsizlikler durumunda sistem, [Disambiguate First, Parse Later](Resources/Disambiguate%20First,%20Parse%20Later-%20Generating%20Interpretations%20for%20Ambiguity%20Resolution.pdf) çalışmasındaki "Önce belirsizliği çöz, sonra ayrıştır" prensibini izler. CPU kaynaklarını korumak için bu işlem [Small Language Model Helps Resolve Semantic Ambiguity](Resources/Small%20Language%20Model%20Helps%20Resolve%20Semantic%20Ambiguity%20of%20LLM%20Prompt.pdf) makalesinde kanıtlandığı gibi SLM'ler üzerinden koordine edilecektir.
    *   Oluşturulan SQL veritabanında başarısız olursa, [SEA-SQL](Resources/SEA-SQL-SemanticEnhancedText2SQLwith%20adaptiveRefinement.pdf) çalışmasındaki "Dinamik Yürütme Ayarlaması" ve [ExCoT](Resources/ExCoT-%20Optimizing%20Reasoning%20for%20Text-to-SQL%20with%20Execution%20Feedback.pdf) makalesindeki "Çalıştırma Tabanlı Geri Bildirim (Execution-based Feedback)" algoritmaları devreye girerek modelin kendi kendini onarması sağlanacaktır.

---

## KAN-26: Proposed System Architecture (Multi-Agent Workflow)

> **Amaç:** Tasarlanan tüm çözüm algoritmalarını işbirlikçi ve otonom ajanlara dağıtarak performansı, hızı ve şeffaflığı maksimize etmek.

*   **Mimari Darboğaz (Problem):**
    Veri okuma, şema filtreleme, SQL sentezleme ve hata onarımı adımlarının tamamının tek bir monolitik modele (Monolithic Model) yaptırılması, yüksek hata yayılımına (error propagation), devasa RAM tüketimine ve yavaşlığa neden olur.
*   **Sistem Entegrasyonu (Çözüm):**
    Sistem LangGraph altyapısı kullanılarak şu otonom ve işbirlikçi ajanlara (Collaborative Agents) bölünecektir:
    1.  **Selector Agent:** RAG tabanlı bağlama duyarlı şema ve tarihsel sorgu getirme.
    2.  **Generator Agent:** Alana özgü sentetik verilerle fine-tune edilmiş, CPU'da çalışan küçük model ile MDX/SQL inşası.
    3.  **Validator/Refiner Agent:** SQL yürütme testini yapıp sözdizimi hatalarında veya anlamsal boşluklarda "Self-Correction" döngüsünü tetikleyen denetleyici mekanizma.
*   **Akademik Temellendirme & Literatür Desteği:**
    *   [AI Agentic Workflow Implementations](Resources/Text_to_SQL_AI_Agentic_Workflow_Implementations_A_Systematic_Literature_Review.pdf) çalışmasında sistematik olarak kanıtlandığı üzere, modern Text-to-SQL sistemleri niyet sınıflandırma, şema bağlama, SQL inşası ve hata düzeltme görevlerini koordine edilmiş bir çoklu-ajan iş hattında (Multi-Agent Workflows) çözmektedir.
    *   [SchemaRAG](Resources/SchemaRAGSchemaAwareRetrievalAugmentedGenerationFramework4Text2SQL.pdf.pdf) ve [SQLFixAgent](Resources/SQLFixAgentTowardsSemanticAccurateText2SQL%20ParsingViaConsistency-Enhanced%20Multi-Agent%20Collaboration.pdf) modellerinde gösterildiği üzere, birbirini tamamlayan otonom modüllerin entegrasyonu kurumsal sistem performansını ve donanım verimliliğini maksimize eder. Bu modüler ayrıştırma, sistemimizin esnekliğini ve şeffaflığını garanti altına almaktadır.

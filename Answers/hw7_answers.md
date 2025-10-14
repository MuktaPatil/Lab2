
# 🏗️ Architecture and Techniques Used

For this assignment, I designed a **modular Retrieval-Augmented Generation (RAG)** system with **Streamlit** for an GUI. The goal was to build a bot that could automatically identify, rank, and analyze legally significant news stories for law firms using AI models from **OpenAI** and **Anthropic**.

----------

### 1. Data Processing and Representation

I started by structuring the incoming CSV data into a consistent format using a custom `NewsItem` dataclass. This helped me standardize fields like company name, title, description, and date across different input formats.

Then, I created a `NewsEmbedder` class that uses **SentenceTransformer (‘all-MiniLM-L6-v2’)** to generate embeddings for each article. These embeddings allow the system to measure semantic similarity between articles and queries, which is essential for retrieving contextually relevant information later.

----------

### 2. Domain-Aware Relevance Scoring

Since this system is focused on **legal news**, I developed a custom `LegalRelevanceScorer`. It uses a weighted keyword dictionary with terms like “litigation”, “settlement”, “FTC”, and “class action”, each assigned different importance scores.

I also applied two additional adjustments:

-   **Financial institution boost**: slightly increases scores for financial-sector topics (banking, securities, etc.).
    
-   **Recency boost**: reduces the score for older news to prioritize recent developments.
    

This hybrid approach (semantic embeddings + rule-based scoring) gives me a more accurate legal relevance metric.

----------

### 3. Retrieval-Augmented Generation (RAG) Layer

I implemented a `NewsRAGSystem` that combines the embeddings from SentenceTransformer with my custom legal relevance scores. When a user enters a topic or when the bot searches for the most significant news, it:

1.  Embeds the query text.
    
2.  Computes **cosine similarity** between the query and all stored embeddings.
    
3.  Combines similarity (semantic closeness) with the relevance score to rank results.
    

This ensures that both **semantic meaning** and **legal importance** influence which articles are retrieved.

----------

### 4. LLM Analysis Layer

To generate insights, I built an `LLMQueryEngine` that supports both **OpenAI GPT-4o** and **Anthropic Claude** models. Depending on user selection, the engine formats a prompt with:

-   A concise system instruction (as a legal news analyst).
    
-   A context block containing the top-ranked news articles.
    
-   A user query asking the LLM to analyze or rank their significance.
    

The output includes the LLM’s analysis along with token usage details for transparency.

----------

### 5. Streamlit Integration (UI Layer)

Finally, I wrapped everything into a **Streamlit app** . The UI includes:

-   A **sidebar** to choose models and configure the number of articles analyzed.
    
-   Three **main tabs**:
    
    -   “Most Interesting” (auto-detects top legal news)
        
    -   “Search by Topic” (retrieves contextually relevant results)
        
    -   “Browse All” (filters and sorts the dataset manually)
        
I also included **spinners** for progress feedback and **expanders** for viewing article details cleanly. This is mainly for me since the app is slower and I wanted to know the progress at each stage and debug as required

----------

### ⚙️ Why These Techniques

-   **RAG architecture**: Combines factual retrieval with interpretive LLM reasoning, reducing hallucination and improving accuracy.
    
-   **SentenceTransformer embeddings**: lightweight, fast, and highly effective for semantic similarity.
    
-   **Rule-based legal scoring**: adds domain awareness that pure embeddings can miss.

    
-   **Dual LLM support (OpenAI + Anthropic)**: makes the system easy to benchmark across vendors.


# 🧪 Evaluation and Testing


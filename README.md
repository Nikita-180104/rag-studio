# GroundLens AI: Production RAG Studio

An enterprise-grade, domain-specific Retrieval-Augmented Generation (RAG) system featuring high-precision document chunking, hybrid keyword/vector search, Cross-Encoder re-ranking, and double-layer grounding guardrails to eliminate hallucinations. 

This repository contains a decoupled **FastAPI backend** running on Python 3.13 and a **Vite + React frontend** styled with Tailwind CSS.

---

## 🏗️ Project Architecture & Layout

```text
rag-studio/
├── backend/                  # FastAPI Application
│   ├── data/                 # Raw PDF/Markdown docs, SQLite cache, and Chroma DB
│   ├── scripts/              # Evaluation and CI/CD Quality Gate scripts
│   ├── src/
│   │   ├── api.py            # API server routing and rate-limiting
│   │   ├── config.py         # Pydantic Settings management
│   │   ├── embedding/        # local BGE Embeddings initialization
│   │   ├── generation/       # LLM generation pipelines, prompt templates, and guardrails
│   │   ├── ingestion/        # Document loaders and recursive chunkers
│   │   ├── retrieval/        # Hybrid ensemble retrievers and Cross-Encoder re-rankers
│   │   └── utils/            # Cache manager and standard error types
│   ├── requirements.txt      # Python dependencies list
│   └── test_rag_pipeline.py  # End-to-end local validation script
│
├── frontend/                 # Vite + React Client
│   ├── src/
│   │   ├── components/       # UI Chat elements, citation cards, and telemetry panels
│   │   ├── App.jsx           # State coordinator and API dispatcher
│   │   └── index.css         # Tailwind v4 styles
│   └── package.json          # Node dependencies list
│
└── README.md                 # Project documentation
```

---

## 🛠️ Technology Stack

### Backend
* **Core Framework**: FastAPI, Uvicorn, Pydantic v2
* **RAG Orchestration**: LangChain
* **LLM Engine**: Google Gemini API (`gemini-2.5-flash`)
* **Local Embeddings**: `BAAI/bge-small-en` (Hugging Face via SentenceTransformers on CPU)
* **Re-ranking Engine**: `cross-encoder/ms-marco-MiniLM-L-6-v2` (SentenceTransformers on CPU)
* **Vector Store**: Chroma DB (Local persistent directory)
* **Hybrid Search**: Reciprocal Rank Fusion (RRF) blending Sparse BM25 and Dense vector similarity
* **Caching**: Local SQLite persistent cache (stores grounded queries to bypass LLM costs on repeat requests)
* **Rate Limiting**: SlowAPI (IP-based, restricted to 5 requests/minute)

### Frontend
* **Build Tool**: Vite
* **UI Library**: React (Functional components + hooks)
* **Styling**: Tailwind CSS v4 (Glassmorphism design, custom animations, dark-theme layout)
* **Icons**: Lucide React
* **API Client**: Axios

---

## 🚀 Getting Started

### 1. Prerequisites
Ensure you have the following installed on your machine:
* Python 3.10+ (Python 3.13 recommended)
* Node.js v18+ and npm
* A Google Gemini API Key

---

### 2. Backend Setup
1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Create and activate a Python virtual environment:
   ```bash
   python -m venv venv
   # On Windows (PowerShell):
   .\venv\Scripts\Activate.ps1
   # On macOS/Linux:
   source venv/bin/activate
   ```
3. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Create a `.env` file inside the `backend/` directory and configure your credentials (see `backend/.env.example` as a reference):
   ```env
   GOOGLE_API_KEY=your_gemini_api_key_here
   VECTOR_DB_PROVIDER=chroma
   CHROMA_DB_DIR=d:/RAG/backend/data/chroma
   MIN_RELEVANCE_SCORE=-10.0
   ENVIRONMENT=development
   TRANSFORMERS_NO_TF=1
   ```
5. Start the FastAPI development server:
   ```bash
   uvicorn src.api:app --reload --port 8000
   ```

---

### 3. Frontend Setup
1. Open a new terminal and navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install npm packages:
   ```bash
   npm install
   ```
3. Start the Vite React development server:
   ```bash
   npm run dev
   ```
4. Open your browser and navigate to `http://localhost:5173`.

---

## 📂 Custom Document Ingestion

To ingest and search your own custom documents:

1. Place your `.txt`, `.pdf`, or `.md` files in the **`backend/data/`** directory.
2. Ingest and index the documents by running the main CLI entry point:
   ```bash
   cd backend
   $env:PYTHONPATH="src"
   python src/main.py
   ```
3. Close the CLI interactive loop (type `exit`) and restart your Uvicorn backend server to reload the newly generated BM25 index in RAM.
4. Click **`CLEAR CACHE`** in the top navbar of your Web UI and ask a question about your new document.

---

## 🧪 CI/CD Quality Gate & Evaluation
The codebase includes offline evaluation tools to prevent semantic regressions before code merges:

1. Run the offline evaluation pipeline to compute Ragas metrics using Gemini as the LLM judge:
   ```bash
   cd backend
   $env:PYTHONPATH="src"
   python scripts/evaluate_rag.py
   ```
   This will output `backend/data/eval_results.json` containing `faithfulness` and `answer_correctness` ratios.

2. Run the Quality Gate check to assert compliance against baseline thresholds:
   ```bash
   python scripts/ci_quality_gate.py
   ```
   *(Requires `faithfulness >= 0.85` and `answer_correctness >= 0.80` to pass)*

---
title: RAG Backend API
emoji: 🔍
colorFrom: blue
colorTo: purple
sdk: docker
app_port: 7860
---

# RAG Backend API Space

This Hugging Face Space hosts the high-performance production backend API for the **Project Antigravity RAG Studio**. 

It runs inside a Docker container serving a FastAPI web app with local semantic indexing, Cross-Encoder re-ranking, and double-layer factual grounding guardrails.

## 🛠️ Configuration & Secrets

Before launching the Space, make sure to add the following **Secret** inside the Space settings page:

* **`GOOGLE_API_KEY`**: Your Google Gemini API Developer Key (required to invoke `gemini-2.5-flash-lite` for grounding evaluations and answer generation).

## 🚀 API Endpoints Exposed

* **`GET /health`**: Health bar telemetry showing system status.
* **`POST /query`**: Core RAG retrieval and synthesis pipeline.
* **`POST /cache/clear`**: Database cache flushing.

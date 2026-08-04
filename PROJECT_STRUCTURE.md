# Portfolio Q&A Bot — Project Structure

```
portfolio-qa-bot/
│
├── backend/
│   ├── ingest.py          ← Step 1: Load your docs → chunk → embed → save to vector DB
│   ├── qa_chain.py        ← Step 2: RAG chain (retriever + LLM + memory)
│   ├── app.py             ← Step 3: FastAPI server exposing /chat endpoint
│   └── requirements.txt
│
├── frontend/
│   └── src/
│       └── App.jsx        ← Chat UI (React)
│       └── main.jsx
│       └── index.css
│
├── data/
│   └── portfolio.txt      ← YOUR resume/portfolio info goes here
│
└── .env                   ← API keys (never commit this)
```

## How data flows

User types question
       ↓
React UI → POST /chat → FastAPI
                            ↓
                     qa_chain.py
                      ↓         ↓
               Retriever    Conversation Memory
               (ChromaDB)   (last N messages)
                      ↓
                 Relevant chunks
                      ↓
              LLM (OpenAI/Gemini)
                      ↓
               Answer + sources
                            ↓
                React UI ← FastAPI

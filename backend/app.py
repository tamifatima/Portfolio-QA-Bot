"""
=============================================================
  app.py  —  Step 3: FastAPI Backend Server
=============================================================

PURPOSE:
  This is the web server that sits between your React frontend
  and the RAG chain. It exposes two HTTP endpoints:

    POST /chat   → receives a question, returns an answer
    POST /reset  → clears conversation memory (fresh start)
    GET  /health → simple check to confirm server is running

HOW IT WORKS:
  1. When the server starts, it calls build_qa_chain() ONCE
     to load ChromaDB and initialize the LLM. This is expensive
     so we do it once and reuse the chain for all requests.

  2. Each POST /chat request:
     a) receives {"question": "...", "session_id": "..."}
     b) calls chain.invoke({"question": ...})
     c) returns {"answer": "...", "sources": [...]}

  3. CORS middleware allows the React frontend (running on
     localhost:5173) to call this server (localhost:8000).

HOW TO RUN:
  cd backend
  uvicorn app:app --reload --port 8000
=============================================================
"""

import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

# Our RAG chain builder from qa_chain.py
from qa_chain import build_qa_chain

load_dotenv()

# ─── FASTAPI APP SETUP ────────────────────────────────────────────────────────
#
# FastAPI is a modern Python web framework.
# It auto-generates API docs at http://localhost:8000/docs
#
app = FastAPI(
    title="Portfolio Q&A Bot API",
    description="RAG-powered chatbot for Tahreem's portfolio",
    version="1.0.0"
)

# ─── CORS MIDDLEWARE ─────────────────────────────────────────────────────────
#
# CORS (Cross-Origin Resource Sharing) is a browser security policy.
# Without this, your React app (port 5173) cannot call this server (port 8000)
# because they are on different "origins".
#
# allow_origins=["http://localhost:5173"] → only allow React dev server
# In production, replace with your deployed frontend URL.
#
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",     # React dev server (Vite default)
        "http://localhost:3000",     # Create React App default
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],             # allow GET, POST, OPTIONS, etc.
    allow_headers=["*"],             # allow all headers
)

# ─── GLOBAL STATE ─────────────────────────────────────────────────────────────
#
# We build the chain ONCE when the server starts, not on every request.
# This is important because loading ChromaDB and initializing models takes
# a few seconds. We store chain and memory as module-level globals.
#
print("🚀 Starting up — loading RAG chain...")
qa_chain, memory = build_qa_chain()
print("✅ Server ready!")


# ─── REQUEST / RESPONSE SCHEMAS ──────────────────────────────────────────────
#
# Pydantic models define the shape of request and response JSON.
# FastAPI uses these for automatic validation and documentation.
#
class ChatRequest(BaseModel):
    """What the frontend sends to /chat"""
    question: str                         # the user's question (required)
    session_id: Optional[str] = "default" # for future multi-user support


class SourceDocument(BaseModel):
    """A single source chunk returned with the answer"""
    content: str      # the actual text of the chunk
    source: str       # which file it came from (e.g. "data/portfolio.txt")


class ChatResponse(BaseModel):
    """What /chat sends back to the frontend"""
    answer: str                           # the LLM's answer
    sources: list[SourceDocument]         # which chunks were used


class ResetResponse(BaseModel):
    message: str


# ─── ENDPOINTS ───────────────────────────────────────────────────────────────

@app.get("/health")
def health_check():
    """
    Simple health check endpoint.
    The frontend can ping this to confirm the backend is running.
    """
    return {"status": "ok", "message": "Portfolio Q&A Bot is running!"}


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Main chat endpoint.

    Flow:
      1. Validate the question isn't empty
      2. Call qa_chain.invoke() — this triggers the full RAG pipeline:
           a) Condense question using chat history
           b) Retrieve top-4 relevant chunks from ChromaDB
           c) Build prompt: [system prompt] + [chunks] + [question]
           d) Call OpenAI API to generate answer
           e) Memory automatically saves this exchange
      3. Extract answer and source documents
      4. Return structured response

    The chain.invoke() call is the heart of the whole application.
    Everything else (ingest.py, qa_chain.py) was preparation for this moment.
    """

    # Guard: reject empty questions
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    try:
        # ── INVOKE THE RAG CHAIN ──────────────────────────────────────────
        #
        # chain.invoke() takes a dict with "question" key.
        # The chain itself reads "chat_history" from memory automatically.
        #
        # result is a dict with keys:
        #   "answer"            → the LLM's text response
        #   "source_documents"  → list of Document objects (the retrieved chunks)
        #   "chat_history"      → the conversation so far
        #
        result = qa_chain.invoke({"question": request.question})

        # ── EXTRACT ANSWER ────────────────────────────────────────────────
        answer = result.get("answer", "I couldn't find an answer to that.")

        # ── EXTRACT SOURCE DOCUMENTS ──────────────────────────────────────
        #
        # source_documents is a list of LangChain Document objects.
        # Each has:
        #   doc.page_content → the chunk text
        #   doc.metadata     → {"source": "path/to/file.txt"}
        #
        # We deduplicate by content to avoid returning the same chunk twice
        # (can happen if the same chunk was retrieved multiple times).
        #
        raw_sources = result.get("source_documents", [])
        seen_contents = set()
        sources = []

        for doc in raw_sources:
            content = doc.page_content.strip()
            if content not in seen_contents:
                seen_contents.add(content)
                sources.append(SourceDocument(
                    content=content,
                    source=doc.metadata.get("source", "portfolio.txt")
                ))

        return ChatResponse(answer=answer, sources=sources)

    except Exception as e:
        # Log the error server-side, return a friendly message to the user
        print(f"❌ Error in /chat: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Something went wrong: {str(e)}"
        )


@app.post("/reset", response_model=ResetResponse)
async def reset_memory():
    """
    Clears the conversation memory.
    Call this when the user clicks "New Chat" in the frontend.

    memory.clear() wipes the ConversationBufferWindowMemory,
    so the next message starts a fresh conversation with no history.
    """
    memory.clear()
    return ResetResponse(message="Conversation memory cleared!")


# ─── DEV ENTRYPOINT ──────────────────────────────────────────────────────────
#
# This block only runs when you execute: python app.py directly.
# In production, use: uvicorn app:app --host 0.0.0.0 --port 8000
#
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)

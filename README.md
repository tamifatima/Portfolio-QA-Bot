# 🤖 Portfolio Q&A Bot
**RAG-powered chatbot built with LangChain + ChromaDB + FastAPI + React**

Ask questions about Tahreem's skills, projects, and experience — the bot answers from your actual portfolio data using Retrieval-Augmented Generation.

---

## 🏗️ Architecture (How it all fits together)

```
┌─────────────────────────────────────────────────────────┐
│                     RAG PIPELINE                         │
│                                                         │
│  data/portfolio.txt                                     │
│         │                                               │
│         ▼                                               │
│   [ ingest.py ]  ──────────────────────────────────┐   │
│   1. Load .txt files                                │   │
│   2. Split into 500-char chunks                     │   │
│   3. Embed with OpenAI ada-002                      │   │
│   4. Store in ChromaDB (./chroma_db/)               │   │
│                                                     │   │
│                        ┌────────────────────────────┘   │
│                        ▼                                │
│   [ qa_chain.py ]   ChromaDB                           │
│   - Retriever:      finds top-4 relevant chunks        │
│   - Memory:         remembers last 5 exchanges         │
│   - LLM:            gpt-4o-mini generates the answer   │
│                                                         │
│   [ app.py ]                                           │
│   FastAPI server — POST /chat, POST /reset, GET /health │
│                        │                                │
│                        │  HTTP JSON                     │
│                        ▼                                │
│   [ App.jsx ]                                          │
│   React chat UI — sends questions, shows answers        │
└─────────────────────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
portfolio-qa-bot/
│
├── backend/
│   ├── ingest.py         ← Run once to build vector DB
│   ├── qa_chain.py       ← RAG chain (retriever + LLM + memory)
│   ├── app.py            ← FastAPI server
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx       ← Full chat UI
│   │   └── main.jsx      ← React entry point
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
│
├── data/
│   └── portfolio.txt     ← YOUR data goes here
│
├── .env.example          ← Copy to .env and add your API key
└── README.md
```

---

## ⚙️ Setup Instructions

### Prerequisites
- Python 3.10+
- Node.js 18+
- An OpenAI API key → https://platform.openai.com/api-keys

---

### Step 1 — Clone and set up environment variables

```bash
# Copy the example env file
cp .env.example .env

# Edit .env and add your actual OpenAI key
# OPENAI_API_KEY=sk-...
```

---

### Step 2 — Set up the Python backend

```bash
cd backend

# Create a virtual environment (keeps dependencies isolated)
python -m venv venv

# Activate it
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

# Install all Python dependencies
pip install -r requirements.txt
```

---

### Step 3 — Edit your portfolio data

Open `data/portfolio.txt` and replace the content with YOUR actual information:
- Your name, education, CGPA
- Your skills (languages, frameworks, tools)
- Each project (name, description, tech stack, role)
- Your work experience
- Contact info

The more detail you add, the better the bot answers.

---

### Step 4 — Run ingestion (build the vector database)

```bash
# Make sure you're in the backend/ folder with venv active
python ingest.py
```

You should see output like:
```
📂 Loading documents from ../data/ ...
   ✅ Loaded 1 document(s)

✂️  Splitting into chunks ...
   ✅ Created 34 chunks

🔢 Embedding chunks and saving to ChromaDB ...
   ✅ Saved 34 vectors to ./chroma_db

🎉 Ingestion complete! You can now run app.py
```

This creates a `chroma_db/` folder in `backend/`. Don't delete it!

---

### Step 5 — Start the FastAPI backend

```bash
# In backend/ with venv active
uvicorn app:app --reload --port 8000
```

You should see:
```
🚀 Starting up — loading RAG chain...
✅ QA chain ready!
INFO: Uvicorn running on http://0.0.0.0:8000
```

Test it's working: http://localhost:8000/health  
API docs (auto-generated): http://localhost:8000/docs

---

### Step 6 — Start the React frontend

Open a **new terminal**:

```bash
cd frontend

# Install Node dependencies
npm install

# Start the Vite dev server
npm run dev
```

Open http://localhost:5173 — your bot is live! 🎉

---

## 💬 Example Questions to Try

- "What projects has Tahreem built?"
- "What is ShieldHer?"
- "What are her skills in mobile development?"
- "Tell me about her education and CGPA"
- "What was her role at Nexen?"
- "Has she worked with AI or ML?"

---

## 🔧 Customization Tips

### Change the LLM model
In `qa_chain.py`, change:
```python
model="gpt-4o-mini"    # cheaper, faster
model="gpt-4o"         # smarter, more expensive
```

### Change how many chunks are retrieved
In `qa_chain.py`:
```python
search_kwargs={"k": 4}   # retrieve top 4 chunks
# increase to 6 for longer, more detailed answers
# decrease to 2 for faster, cheaper responses
```

### Change memory length
In `qa_chain.py`:
```python
k=5   # remember last 5 exchanges
# set to 10 for longer conversations
# set to 0 to disable memory
```

### Add more document types
In `ingest.py`, change the DirectoryLoader to also load PDFs:
```python
from langchain_community.document_loaders import PyPDFLoader
# Add your resume.pdf to data/ and use DirectoryLoader with glob="**/*.pdf"
```

---

## 📊 Cost Estimate (OpenAI)

| Operation | Model | Cost |
|-----------|-------|------|
| Ingestion (one-time) | text-embedding-ada-002 | ~$0.0001 |
| Each chat message | gpt-4o-mini | ~$0.0003 |
| 100 questions | gpt-4o-mini | ~$0.03 |

Essentially free for personal use.

---

## 🚀 Deploying to Production

**Backend**: Deploy to Railway, Render, or AWS EC2
- Add your OPENAI_API_KEY as an environment variable
- Upload the `chroma_db/` folder with it
- Run: `uvicorn app:app --host 0.0.0.0 --port 8000`

**Frontend**: Deploy to Vercel
- Change `API_BASE` in `App.jsx` to your deployed backend URL
- Run: `npm run build` → deploy the `dist/` folder

---

## 🧠 Key Concepts Summary

| Concept | What it does | Where in code |
|---------|-------------|---------------|
| **Chunking** | Splits text into digestible pieces | `ingest.py` → `RecursiveCharacterTextSplitter` |
| **Embedding** | Converts text → searchable numbers | `ingest.py` → `OpenAIEmbeddings` |
| **Vector DB** | Stores + retrieves chunks by similarity | `ChromaDB` → `chroma_db/` folder |
| **Retriever** | Finds top-k relevant chunks for a query | `qa_chain.py` → `vectorstore.as_retriever()` |
| **Memory** | Remembers conversation history | `qa_chain.py` → `ConversationBufferWindowMemory` |
| **RAG Chain** | Combines retriever + memory + LLM | `qa_chain.py` → `ConversationalRetrievalChain` |
| **API Server** | HTTP bridge between frontend and chain | `app.py` → `FastAPI` |
| **Chat UI** | User interface for the bot | `App.jsx` → React + fetch() |

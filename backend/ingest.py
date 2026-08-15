"""
=============================================================
  ingest.py  —  Step 1 of RAG Pipeline
=============================================================

PURPOSE:
  This script is run ONCE (or whenever you update your portfolio data).
  It does three things:
    1. LOAD   → reads your portfolio text file(s)
    2. CHUNK  → splits the text into small overlapping pieces
    3. EMBED  → converts each chunk into a vector (list of numbers)
               and saves everything into ChromaDB (a local vector database)

After running this script, ChromaDB will have a folder called "chroma_db/"
containing all your portfolio info in a searchable vector format.

HOW TO RUN:
  cd backend
  python ingest.py
=============================================================
"""

import os

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv(*args, **kwargs):
        return False

# LangChain document loaders — read files from disk
from langchain_community.document_loaders import TextLoader, DirectoryLoader

# Splits long text into smaller overlapping chunks
from langchain.text_splitter import RecursiveCharacterTextSplitter

# OpenAI embedding model — converts text → vectors
try:
    from langchain_openai import OpenAIEmbeddings
except ImportError:
    OpenAIEmbeddings = None

# ChromaDB vector store — stores and retrieves vectors
from langchain_chroma import Chroma

from fallbacks import LocalEmbeddings

# ─── Load environment variables from .env file ───────────────────────────────
# .env contains: OPENAI_API_KEY=sk-...
load_dotenv()


def ingest_documents():
    """
    Main ingestion function.
    Call this once to build your vector database from your portfolio data.
    """

    # ─── STEP 1: LOAD DOCUMENTS ──────────────────────────────────────────────
    #
    # DirectoryLoader scans the /data folder and loads every .txt file.
    # Each file becomes a "Document" object with:
    #   - page_content  → the raw text
    #   - metadata      → {"source": "path/to/file.txt"}
    #
    print("📂 Loading documents from ../data/ ...")

    loader = DirectoryLoader(
        path="../data",           # folder to scan
        glob="**/*.txt",          # only load .txt files
        loader_cls=TextLoader,    # use TextLoader for plain text files
        loader_kwargs={"encoding": "utf-8"}
    )

    documents = loader.load()
    print(f"   ✅ Loaded {len(documents)} document(s)")

    # ─── STEP 2: CHUNK DOCUMENTS ─────────────────────────────────────────────
    #
    # LLMs have a context window limit (e.g. 8k tokens).
    # We can't pass your entire portfolio text at once, so we split it
    # into smaller overlapping chunks.
    #
    # chunk_size=500   → each chunk is ~500 characters
    # chunk_overlap=50 → consecutive chunks share 50 characters
    #                    (overlap prevents losing context at boundaries)
    #
    # RecursiveCharacterTextSplitter tries to split at:
    #   "\n\n" first (paragraph) → "\n" (line) → " " (word) → "" (char)
    # This keeps natural text boundaries wherever possible.
    #
    print("\n✂️  Splitting into chunks ...")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separators=["\n\n", "\n", " ", ""]  # priority order of split points
    )

    chunks = splitter.split_documents(documents)
    print(f"   ✅ Created {len(chunks)} chunks")
    print(f"   Example chunk:\n   '{chunks[0].page_content[:200]}...'")

    # ─── STEP 3: EMBED AND STORE IN CHROMADB ─────────────────────────────────
    #
    # Embedding = converting text into a list of ~1536 numbers (a vector).
    # Texts with similar meaning produce similar vectors.
    # This is what makes semantic search possible.
    #
    # OpenAIEmbeddings uses the "text-embedding-ada-002" model by default.
    # It calls the OpenAI API to get embeddings — costs fractions of a cent.
    #
    # Chroma.from_documents() does two things:
    #   a) calls embeddings.embed_documents(chunks) to get vectors
    #   b) saves chunks + vectors to disk at persist_directory
    #
    print("\n🔢 Embedding chunks and saving to ChromaDB ...")

    api_key = os.getenv("OPENAI_API_KEY")
    if api_key and OpenAIEmbeddings is not None:
        try:
            embeddings = OpenAIEmbeddings(
                model=os.getenv("EMBEDDING_MODEL", "text-embedding-ada-002"),
                openai_api_key=api_key
            )
        except Exception as exc:
            print(f"   ⚠️ OpenAI embeddings unavailable: {exc}")
            embeddings = LocalEmbeddings()
    else:
        print("   ⚠️ OPENAI_API_KEY not set; using local embeddings fallback")
        embeddings = LocalEmbeddings()

    try:
        vectorstore = Chroma.from_documents(
            documents=chunks,
            embedding=embeddings,
            persist_directory="./chroma_db"   # saves DB to disk in this folder
        )
    except Exception as exc:
        print(f"   ⚠️ Chroma embedding failed: {exc}")
        print("   🔁 Falling back to local embeddings and local Chroma storage")
        embeddings = LocalEmbeddings()
        vectorstore = Chroma.from_documents(
            documents=chunks,
            embedding=embeddings,
            persist_directory="./chroma_db"
        )

    print(f"   ✅ Saved {vectorstore._collection.count()} vectors to ./chroma_db")
    print("\n🎉 Ingestion complete! You can now run app.py")


# ─── Entry point ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    ingest_documents()

"""
=============================================================
  qa_chain.py  —  Step 2 of RAG Pipeline
=============================================================

PURPOSE:
  This file builds the RAG (Retrieval-Augmented Generation) chain.
  It wires together three components:

    [User question]
          ↓
    RETRIEVER  →  searches ChromaDB for the 4 most relevant chunks
          ↓
    PROMPT     →  formats question + chunks + chat history into a prompt
          ↓
    LLM        →  generates an answer using the context
          ↓
    [Answer + source documents]

  It also manages CONVERSATION MEMORY so the bot remembers
  earlier messages in the same session (e.g. "What was the
  first project you mentioned?").

KEY CONCEPT — WHY RAG?
  Without RAG: LLM only knows what it was trained on. It knows
  nothing about Tahreem's specific resume or projects.

  With RAG: Before answering, we search the vector DB for relevant
  chunks and inject them into the prompt. Now the LLM answers
  specifically from YOUR data.
=============================================================
"""

import os
from dotenv import load_dotenv

# ChatOpenAI = the LLM (gpt-4o-mini is fast and cheap, good for demos)
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

# Chroma = our vector database (built by ingest.py)
from langchain_chroma import Chroma

# ConversationalRetrievalChain = LangChain's built-in RAG + memory chain
from langchain.chains import ConversationalRetrievalChain

# ConversationBufferWindowMemory = keeps the last K message pairs in memory
from langchain.memory import ConversationBufferWindowMemory

# PromptTemplate = lets us write a custom system prompt
from langchain.prompts import PromptTemplate

load_dotenv()


# ─── CUSTOM PROMPT ───────────────────────────────────────────────────────────
#
# This is the instruction we send to the LLM along with the retrieved context.
# {context}  → filled with the retrieved chunks from ChromaDB
# {question} → filled with the user's actual question
#
# We tell the LLM to ONLY use the provided context (not hallucinate),
# stay in character as a portfolio assistant, and be concise.
#
QA_PROMPT_TEMPLATE = """You are Tahreem's personal portfolio assistant. 
You answer questions about Tahreem's skills, projects, education, and experience
based ONLY on the information provided below.

If the answer is not in the context, say: 
"I don't have that specific information, but feel free to reach out to Tahreem directly!"

Be friendly, professional, and concise. You're representing Tahreem to potential 
recruiters and collaborators.

Context from portfolio:
{context}

Question: {question}

Answer:"""

QA_PROMPT = PromptTemplate(
    template=QA_PROMPT_TEMPLATE,
    input_variables=["context", "question"]
)


def build_qa_chain():
    """
    Builds and returns the full RAG chain.
    Called once when the FastAPI server starts.

    Returns:
        chain   → ConversationalRetrievalChain (call chain.invoke() to query)
        memory  → the memory object (so we can reset it per session if needed)
    """

    # ─── 1. LOAD THE VECTOR STORE ────────────────────────────────────────────
    #
    # We load the ChromaDB that was built by ingest.py.
    # We need to use the SAME embedding model used during ingestion,
    # because the query vector must be in the same space as the stored vectors.
    #
    print("🔍 Loading ChromaDB vector store...")

    embeddings = OpenAIEmbeddings(
        model="text-embedding-ada-002",
        openai_api_key=os.getenv("OPENAI_API_KEY")
    )

    vectorstore = Chroma(
        persist_directory="./chroma_db",   # must match ingest.py
        embedding_function=embeddings
    )

    # ─── 2. CREATE THE RETRIEVER ─────────────────────────────────────────────
    #
    # The retriever is a search interface on top of the vector store.
    # When given a query, it:
    #   a) embeds the query into a vector
    #   b) finds the k most similar vectors in ChromaDB (cosine similarity)
    #   c) returns the corresponding text chunks
    #
    # k=4 means we retrieve the top 4 most relevant chunks.
    # More chunks = more context but also more tokens (and cost).
    #
    retriever = vectorstore.as_retriever(
        search_type="similarity",   # cosine similarity search
        search_kwargs={"k": 4}      # return top 4 chunks
    )

    # ─── 3. SET UP CONVERSATION MEMORY ───────────────────────────────────────
    #
    # ConversationBufferWindowMemory stores the last k=5 conversation turns.
    # A "turn" = one user message + one AI response.
    #
    # memory_key="chat_history"  → the chain will look for this key in memory
    # return_messages=True       → returns as Message objects (required for
    #                              ConversationalRetrievalChain)
    #
    memory = ConversationBufferWindowMemory(
        k=5,                          # remember last 5 exchanges
        memory_key="chat_history",    # must match what the chain expects
        return_messages=True,         # return as HumanMessage/AIMessage objects
        output_key="answer"           # tell memory which output to store
    )

    # ─── 4. INITIALIZE THE LLM ───────────────────────────────────────────────
    #
    # gpt-4o-mini: fast, cheap (~$0.00015 per 1k input tokens), good quality
    # temperature=0.3: low temperature = more factual, less creative
    #                  (0 = deterministic, 1 = very creative)
    #
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.3,
        openai_api_key=os.getenv("OPENAI_API_KEY")
    )

    # ─── 5. BUILD THE CONVERSATIONAL RETRIEVAL CHAIN ─────────────────────────
    #
    # ConversationalRetrievalChain combines:
    #   - A "condense question" step: rewrites the user's question using
    #     chat history (e.g. "tell me more about it" → "tell me more about OUTS")
    #   - A retrieval step: fetches relevant chunks from ChromaDB
    #   - A QA step: passes chunks + question to the LLM to generate an answer
    #
    # combine_docs_chain_kwargs → passes our custom QA_PROMPT to the QA step
    # return_source_documents=True → also return the chunks used (for citations)
    #
    chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=retriever,
        memory=memory,
        return_source_documents=True,            # return which chunks were used
        combine_docs_chain_kwargs={"prompt": QA_PROMPT},
        verbose=False                             # set True to see chain logs
    )

    print("✅ QA chain ready!")
    return chain, memory

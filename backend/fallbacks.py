import hashlib
import math
import re

from langchain_core.embeddings import Embeddings


class LocalEmbeddings(Embeddings):
    """Deterministic local embedding fallback for demo/offline use."""

    def _embed(self, text: str):
        tokens = re.findall(r"\w+", text.lower())
        vector = [0.0] * 128

        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:2], "big") % len(vector)
            vector[index] += 1.0

        norm = math.sqrt(sum(value * value for value in vector))
        if norm:
            return [value / norm for value in vector]
        return vector

    def embed_documents(self, texts):
        return [self._embed(text) for text in texts]

    def embed_query(self, text):
        return self._embed(text)


class LocalMemory:
    """Simple in-memory store that mimics the reset/clear API used by the app."""

    def __init__(self):
        self.chat_history = []

    def clear(self):
        self.chat_history.clear()

    def add_exchange(self, question: str, answer: str):
        self.chat_history.append(("user", question))
        self.chat_history.append(("assistant", answer))

    def get_history(self):
        return self.chat_history


class LocalQAChain:
    """Simple retrieval-based QA chain for use when the OpenAI API is unavailable."""

    def __init__(self, vectorstore, memory):
        self.vectorstore = vectorstore
        self.memory = memory

    def invoke(self, inputs):
        question = inputs.get("question", "")
        documents = self.vectorstore.similarity_search(question, k=4)

        if documents:
            answer = self._answer_from_documents(question, documents)
        else:
            answer = "I don’t have that specific information in the current portfolio context."

        self.memory.add_exchange(question, answer)
        return {
            "answer": answer,
            "source_documents": documents,
            "chat_history": self.memory.get_history(),
        }

    def _answer_from_documents(self, question, documents):
        q_terms = set(re.findall(r"\w+", question.lower()))
        if not q_terms:
            return "Please ask a question about the portfolio."

        scored = []
        for document in documents:
            text = document.page_content.lower()
            score = sum(1 for term in q_terms if term in text)
            scored.append((score, document))

        best_score, best_document = max(scored, key=lambda item: item[0])
        if best_score == 0:
            return "I don’t have that specific information in the current portfolio context."

        excerpt = best_document.page_content.strip()
        if len(excerpt) > 500:
            excerpt = excerpt[:497] + "..."
        return f"Based on the portfolio context, {excerpt}"

"""Vector Store wrapper using FAISS and embeddings"""

import os
from langchain_community.vectorstores import FAISS
from src.config.config import Config

class VectorStore:
    def __init__(self, persist_dir: str = "faiss_index"):
        self.persist_dir = persist_dir
        self.db = None
        self.embeddings = self._load_embeddings()

    def _load_embeddings(self):
        """
        Load embeddings model.
        Priority:
        1. BGE-small via sentence-transformers (free, local,
           works with any LLM including Groq)
        2. OpenAI embeddings (if OPENAI_API_KEY set)
        3. Google embeddings (if GEMINI_API_KEY set)
        """
        try:
            from langchain_community.embeddings import (
                HuggingFaceEmbeddings
            )
            return HuggingFaceEmbeddings(
                model_name="BAAI/bge-small-en-v1.5",
                model_kwargs={"device": "cpu"},
                encode_kwargs={"normalize_embeddings": True},
            )
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(
                "HuggingFace embeddings failed (%s). "
                "Falling back to OpenAI embeddings.", e
            )
            try:
                from langchain_openai import OpenAIEmbeddings
                return OpenAIEmbeddings()
            except Exception:
                from langchain_google_genai import (
                    GoogleGenerativeAIEmbeddings
                )
                return GoogleGenerativeAIEmbeddings(
                    model="models/embedding-001"
                )

    def create_vectorstore(self, chunks):
        self.db = FAISS.from_documents(chunks, self.embeddings)
        self.save_local(self.persist_dir)

    def get_retriever(self):
        if self.db is None:
            if os.path.exists(self.persist_dir):
                self.load_local(self.persist_dir)
            else:
                raise ValueError("Vector store not initialized and no saved index found.")
        return self.db.as_retriever()

    def save_local(self, path: str):
        if self.db is not None:
            self.db.save_local(path)

    def load_local(self, path: str):
        self.db = FAISS.load_local(path, self.embeddings, allow_dangerous_deserialization=True)

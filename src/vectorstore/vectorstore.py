"""Vector Store wrapper using FAISS and embeddings"""

import os
from langchain_community.vectorstores import FAISS
from src.config.config import Config

class VectorStore:
    def __init__(self, persist_dir: str = "faiss_index"):
        self.persist_dir = persist_dir
        
        # Resolve embeddings dynamically based on active model config
        gemini_key = Config.get_gemini_key()
        openai_key = Config.get_openai_key()
        groq_key = Config.get_groq_key()

        if not gemini_key and not openai_key and not groq_key:
            from langchain_core.embeddings import Embeddings
            class MockEmbeddings(Embeddings):
                def embed_documents(self, texts):
                    return [[0.1] * 1536 for _ in texts]
                def embed_query(self, text):
                    return [0.1] * 1536
            self.embeddings = MockEmbeddings()
        elif Config.USE_GEMINI and gemini_key:
            from langchain_google_genai import GoogleGenerativeAIEmbeddings
            os.environ["GOOGLE_API_KEY"] = gemini_key
            self.embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=gemini_key)
        elif openai_key:
            from langchain_openai import OpenAIEmbeddings
            os.environ["OPENAI_API_KEY"] = openai_key
            self.embeddings = OpenAIEmbeddings()
        else:
            from langchain_core.embeddings import Embeddings
            class MockEmbeddings(Embeddings):
                def embed_documents(self, texts):
                    return [[0.1] * 1536 for _ in texts]
                def embed_query(self, text):
                    return [0.1] * 1536
            self.embeddings = MockEmbeddings()
            
        self.db = None

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

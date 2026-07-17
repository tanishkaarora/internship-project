"""Configuration for Insight Copilot"""

import os
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

class Config:
    # API Keys — supports both local .env, Streamlit Cloud secrets, and session state
    @staticmethod
    def get_openai_key() -> str:
        if "openai_api_key" in st.session_state and st.session_state["openai_api_key"]:
            return st.session_state["openai_api_key"]
        try:
            return st.secrets["OPENAI_API_KEY"]
        except Exception:
            return os.getenv("OPENAI_API_KEY", "")

    @staticmethod
    def get_groq_key() -> str:
        """Alternative free LLM — use if OpenAI costs are a concern"""
        if "groq_api_key" in st.session_state and st.session_state["groq_api_key"]:
            return st.session_state["groq_api_key"]
        try:
            return st.secrets["GROQ_API_KEY"]
        except Exception:
            return os.getenv("GROQ_API_KEY", "")

    @staticmethod
    def get_gemini_key() -> str:
        """Gemini API Key from session state, secrets or environment"""
        if "gemini_api_key" in st.session_state and st.session_state["gemini_api_key"]:
            return st.session_state["gemini_api_key"]
        try:
            return st.secrets["GEMINI_API_KEY"]
        except Exception:
            return os.getenv("GEMINI_API_KEY", "")

    # Model — switch between OpenAI, Groq, and Gemini
    USE_GEMINI = os.getenv("USE_GEMINI", "false").lower() == "true"
    USE_GROQ = os.getenv("USE_GROQ", "false").lower() == "true"
    LLM_MODEL = "gemini-1.5-flash" if USE_GEMINI else ("groq:llama-3.1-8b-instant" if USE_GROQ else "openai:gpt-4o-mini")

    # Document Processing
    CHUNK_SIZE = 600
    CHUNK_OVERLAP = 80

    # Analytics
    MAX_ROWS_IN_MEMORY = 100_000  # warn user if CSV exceeds this
    TOP_N_DEFAULT = 5             # default for "top N" queries

    @classmethod
    def get_llm(cls):
        gemini_key = cls.get_gemini_key()
        groq_key = cls.get_groq_key()
        openai_key = cls.get_openai_key()

        if not gemini_key and not groq_key and not openai_key:
            from src.utils.mock_llm import MockChatModel
            return MockChatModel()

        if cls.USE_GEMINI and gemini_key:
            from langchain_google_genai import ChatGoogleGenerativeAI
            os.environ["GEMINI_API_KEY"] = gemini_key
            os.environ["GOOGLE_API_KEY"] = gemini_key
            return ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=gemini_key)
        elif cls.USE_GROQ and groq_key:
            from langchain.chat_models import init_chat_model
            os.environ["GROQ_API_KEY"] = groq_key
            return init_chat_model("groq:llama-3.1-8b-instant")
        elif openai_key:
            from langchain.chat_models import init_chat_model
            os.environ["OPENAI_API_KEY"] = openai_key
            return init_chat_model(cls.LLM_MODEL)
        else:
            # Fallback to whatever key is present
            from langchain.chat_models import init_chat_model
            if gemini_key:
                from langchain_google_genai import ChatGoogleGenerativeAI
                return ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=gemini_key)
            elif groq_key:
                os.environ["GROQ_API_KEY"] = groq_key
                return init_chat_model("groq:llama-3.1-8b-instant")
            else:
                os.environ["OPENAI_API_KEY"] = openai_key
                return init_chat_model(cls.LLM_MODEL)


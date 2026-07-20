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
    # Auto-detect which LLM to use based on available keys.
    # Explicit env var takes priority.
    # If USE_GEMINI/USE_GROQ not set, auto-detect from keys.
    _use_gemini_env = os.getenv("USE_GEMINI", "").lower()
    _use_groq_env   = os.getenv("USE_GROQ",   "").lower()
    _gemini_key_set = bool(os.getenv("GEMINI_API_KEY", "").strip())
    _groq_key_set   = bool(os.getenv("GROQ_API_KEY",  "").strip())

    if _use_groq_env == "true":
        # Explicit override: use Groq
        USE_GEMINI = False
        USE_GROQ   = True
    elif _use_gemini_env == "true":
        # Explicit override: use Gemini
        USE_GEMINI = True
        USE_GROQ   = False
    elif _groq_key_set:
        # Groq key found in .env — use it automatically
        USE_GEMINI = False
        USE_GROQ   = True
    elif _gemini_key_set:
        # Gemini key found in .env — use it automatically
        USE_GEMINI = True
        USE_GROQ   = False
    else:
        # No keys found — MockChatModel fallback
        USE_GEMINI = False
        USE_GROQ   = False
    LLM_MODEL = "gemini-1.5-flash" if USE_GEMINI else ("groq:llama-3.1-8b-instant" if USE_GROQ else "openai:gpt-4o-mini")

    # Document Processing
    CHUNK_SIZE = 600
    CHUNK_OVERLAP = 80

    # Analytics
    MAX_ROWS_IN_MEMORY = 100_000  # warn user if CSV exceeds this
    TOP_N_DEFAULT = 5             # default for "top N" queries

    @classmethod
    def get_llm(cls):
        if cls.USE_GROQ:
            groq_key = cls.get_groq_key()
            if not groq_key:
                raise ValueError(
                    "GROQ_API_KEY not found. "
                    "Add it to your .env file: "
                    "GROQ_API_KEY=your_key_here"
                )
            from langchain_groq import ChatGroq
            os.environ["GROQ_API_KEY"] = groq_key
            return ChatGroq(
                model="llama-3.1-8b-instant",
                groq_api_key=groq_key,
                temperature=0.3,
                max_tokens=1024,
            )
        elif cls.USE_GEMINI:
            gemini_key = cls.get_gemini_key()
            if not gemini_key:
                raise ValueError(
                    "GEMINI_API_KEY not found. "
                    "Add it to your .env file: "
                    "GEMINI_API_KEY=your_key_here"
                )
            from langchain_google_genai import ChatGoogleGenerativeAI
            os.environ["GEMINI_API_KEY"] = gemini_key
            os.environ["GOOGLE_API_KEY"]  = gemini_key
            return ChatGoogleGenerativeAI(
                model="gemini-1.5-flash",
                google_api_key=gemini_key,
                temperature=0.3,
                max_tokens=1024,
            )
        else:
            from src.utils.mock_llm import MockChatModel
            return MockChatModel()


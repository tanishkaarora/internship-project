"""Configuration for Insight Copilot"""

import os
import streamlit as st
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

class ConfigMeta(type):
    def get_session_state_val(cls, key, default=None):
        try:
            if key in st.session_state:
                return st.session_state[key]
        except Exception:
            pass
        return default

    @property
    def USE_GROQ(cls) -> bool:
        # Check active session state settings toggles first
        if cls.get_session_state_val("use_groq_toggle") and cls.get_groq_key():
            return True
        if cls.get_session_state_val("use_groq_toggle") is False:
            pass

        # Check explicit overrides
        use_groq_env = os.getenv("USE_GROQ", "").lower()
        use_gemini_env = os.getenv("USE_GEMINI", "").lower()
        if use_groq_env == "true":
            return True
        if use_gemini_env == "true":
            return False

        # Check key availability
        groq_key = cls.get_groq_key()
        gemini_key = cls.get_gemini_key()
        if groq_key and not use_gemini_env == "true":
            return True
        return False

    @property
    def USE_GEMINI(cls) -> bool:
        if cls.USE_GROQ:
            return False

        use_gemini_env = os.getenv("USE_GEMINI", "").lower()
        if use_gemini_env == "true":
            return True
        use_groq_env = os.getenv("USE_GROQ", "").lower()
        if use_groq_env == "true":
            return False

        gemini_key = cls.get_gemini_key()
        if gemini_key:
            return True
        return False

    @property
    def LLM_MODEL(cls) -> str:
        if cls.USE_GEMINI:
            return "gemini-1.5-flash"
        elif cls.USE_GROQ:
            return "groq:llama-3.1-8b-instant"
        else:
            return "openai:gpt-4o-mini"


@st.cache_resource
def _get_cached_llm(use_groq: bool, use_gemini: bool, groq_key: str, gemini_key: str):
    if use_groq:
        if not groq_key:
            raise ValueError(
                "GROQ_API_KEY not found. "
                "Add it to your .env file: "
                "GROQ_API_KEY=your_key_here"
            )
        from langchain_groq import ChatGroq
        return ChatGroq(
            model="llama-3.1-8b-instant",
            groq_api_key=groq_key,
            temperature=0.3,
            max_tokens=1024,
        )
    elif use_gemini:
        if not gemini_key:
            raise ValueError(
                "GEMINI_API_KEY not found. "
                "Add it to your .env file: "
                "GEMINI_API_KEY=your_key_here"
            )
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            google_api_key=gemini_key,
            temperature=0.3,
            max_tokens=1024,
        )
    else:
        from src.utils.mock_llm import MockChatModel
        return MockChatModel()


class Config(metaclass=ConfigMeta):
    # API Keys — supports both local .env, Streamlit Cloud secrets, and session state
    @staticmethod
    def get_openai_key() -> str:
        try:
            if "openai_api_key" in st.session_state and st.session_state["openai_api_key"]:
                return st.session_state["openai_api_key"]
        except Exception:
            pass
        try:
            return st.secrets["OPENAI_API_KEY"]
        except Exception:
            return os.getenv("OPENAI_API_KEY", "")

    @staticmethod
    def get_groq_key() -> str:
        """Alternative free LLM — use if OpenAI costs are a concern"""
        try:
            if "groq_api_key" in st.session_state and st.session_state["groq_api_key"]:
                return st.session_state["groq_api_key"]
        except Exception:
            pass
        try:
            return st.secrets["GROQ_API_KEY"]
        except Exception:
            return os.getenv("GROQ_API_KEY", "")

    @staticmethod
    def get_gemini_key() -> str:
        """Gemini API Key from session state, secrets or environment"""
        try:
            if "gemini_api_key" in st.session_state and st.session_state["gemini_api_key"]:
                return st.session_state["gemini_api_key"]
        except Exception:
            pass
        try:
            return st.secrets["GEMINI_API_KEY"]
        except Exception:
            return os.getenv("GEMINI_API_KEY", "")

    # Document Processing
    CHUNK_SIZE = 600
    CHUNK_OVERLAP = 80

    # Analytics
    MAX_ROWS_IN_MEMORY = 100_000  # warn user if CSV exceeds this
    TOP_N_DEFAULT = 5             # default for "top N" queries

    @classmethod
    def get_llm(cls):
        return _get_cached_llm(
            use_groq=cls.USE_GROQ,
            use_gemini=cls.USE_GEMINI,
            groq_key=cls.get_groq_key(),
            gemini_key=cls.get_gemini_key()
        )



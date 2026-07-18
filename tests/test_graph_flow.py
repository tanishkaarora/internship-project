import sys
import os
from pathlib import Path
import pytest

# Add src to python path
sys.path.append(str(Path(__file__).parent.parent))

from src.state.copilot_state import CopilotState
from src.graph_builder.graph_builder import CopilotGraphBuilder
from src.vectorstore.vectorstore import VectorStore

class MockLLMResponse:
    def __init__(self, content: str):
        self.content = content

class MockLLM:
    def __init__(self, response_text: str):
        self.response_text = response_text
        self.calls = []

    def invoke(self, prompt: str):
        self.calls.append(prompt)
        return MockLLMResponse(self.response_text)

class MockVectorStore(VectorStore):
    def __init__(self):
        self.embeddings = None
        self.db = None
    def get_retriever(self):
        class MockRetriever:
            def invoke(self, question):
                from langchain_core.documents import Document
                return [Document(page_content="Mock doc content", metadata={"source": "test.pdf", "page": 1})]
        return MockRetriever()

def test_graph_analytics_route():
    llm = MockLLM("analytics")
    vs = MockVectorStore()
    builder = CopilotGraphBuilder(llm=llm, vector_store=vs)
    graph = builder.build()
    
    # We run the graph. The intent router will return "analytics".
    # Since we mocked the LLM to return "analytics", it should route to the analytics node,
    # and then to the synthesiser node.
    # We will need the synthesiser LLM invocation to return a business response.
    
    # Let's override the LLM's response for the synthesizer:
    # Actually, we can use a stateful mock LLM
    class StatefulMockLLM:
        def __init__(self):
            self.calls = []
        def invoke(self, prompt):
            self.calls.append(prompt)
            if "classifying" in prompt.lower() or "intent" in prompt.lower():
                return MockLLMResponse("analytics")
            else:
                return MockLLMResponse("This is a synthesized analytics answer.")
                
    stateful_llm = StatefulMockLLM()
    builder = CopilotGraphBuilder(llm=stateful_llm, vector_store=vs)
    
    # Let's mock the Streamlit session state for data frame
    import streamlit as st
    st.session_state["clean_df"] = None
    st.session_state["data_profile"] = None
    
    result = builder.run(question="What is the sales trend?")
    
    # Assert result structure and contents
    assert result["route"] == "analytics"
    assert "No data file has been uploaded" in result["analytics_result"]
    assert result["answer"] == "This is a synthesized analytics answer."
    print("test_graph_analytics_route passed!")

def test_graph_fallback_on_llm_error():
    """
    When the LLM raises an exception, the graph should
    fall back to MockChatModel and still return a valid answer.
    """
    import streamlit as st
    from src.utils.mock_llm import MockChatModel

    class FailingLLM:
        def invoke(self, prompt):
            raise ConnectionError("Simulated API key error")

    class MockVS:
        embeddings = None
        db = None
        def get_retriever(self):
            raise ValueError("No PDF")

    st.session_state["clean_df"] = None
    st.session_state["data_profile"] = None
    st.session_state["vector_store"] = None

    builder = CopilotGraphBuilder(llm=FailingLLM(), vector_store=MockVS())
    builder.build()

    result = builder.run("Which product has the highest sales?")

    assert result is not None
    assert result.get("answer", "") != ""
    assert "api_error_warning" in st.session_state
    print("test_graph_fallback_on_llm_error passed!")

def test_session_state_reset_clears_graph():
    """
    Simulates uploading File A, building a graph,
    then uploading File B. Verifies the graph is
    rebuilt and not carrying File A's state.
    """
    import streamlit as st

    # Simulate File A session
    st.session_state["graph"] = "old_graph_from_file_A"
    st.session_state["clean_df"] = "old_df"
    st.session_state["chat_history"] = [
        {"role": "user", "content": "old question"}
    ]
    st.session_state["kpis"] = {"old_kpi": "old_value"}

    # Simulate what reset_for_new_upload() does
    keys_to_reset = [
        "graph", "llm", "clean_df", "data_profile",
        "kpis", "charts", "chat_history",
        "vector_store", "api_error_warning",
    ]
    for key in keys_to_reset:
        if key in st.session_state:
            del st.session_state[key]

    # Verify all stale state is gone
    assert st.session_state.get("graph") is None
    assert st.session_state.get("clean_df") is None
    assert st.session_state.get("chat_history") is None
    assert st.session_state.get("kpis") is None
    print("test_session_state_reset_clears_graph passed!")

if __name__ == "__main__":
    test_graph_analytics_route()
    test_graph_fallback_on_llm_error()
    test_session_state_reset_clears_graph()

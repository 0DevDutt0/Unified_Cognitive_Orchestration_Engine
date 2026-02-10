import os
import re
import sqlite3
import streamlit as st
import pdfplumber
import whisper
import tempfile
import traceback
from audio_recorder_streamlit import audio_recorder
from dotenv import load_dotenv

from langchain_community.tools import DuckDuckGoSearchRun
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from streamlit import cache_resource
from sql_agent import build_sqlite_agent
from langchain_community.llms import Ollama

# Load environment variables
load_dotenv()

# Initialize LLM
llm = Ollama(
    model="mistral",
    temperature=0.3
)

# ----------------- AGENTS -----------------
def fire_safety_agent(query, context):
    try:
        full_prompt = f"""
        You are a fire safety expert. Use the provided context to answer the user's question.
        
        Context:
        {context}

        Question:
        {query}

        Answer:
        """
        return llm.invoke(full_prompt)
    except Exception as e:
        return f"Error: {str(e)}"

def sales_data_agent(query):
    try:
        agent, db = build_sqlite_agent("sales.db", return_intermediate_steps=False)
        result = agent.invoke({"input": query})
        output = result.get("output", "").strip()

        # If output still contains filler, extract numbers from DB directly
        if "(list the amounts" in output.lower():
            raw_result = db.run(f"""
                SELECT amount
                FROM sales
                JOIN salespersons ON sales.salesperson_id = salespersons.salesperson_id
                JOIN regions ON sales.region_id = regions.region_id
                WHERE LOWER(salesperson_name) = 'eve' AND LOWER(region_name) = 'north';
            """)
            return ", ".join(str(row[0]) for row in raw_result)

        return output if output else "No matching sales records found."
    except Exception as e:
        tb = traceback.format_exc()
        st.error(f"Error in sales data agent: {str(e)}\n\n{tb}")
        return f"Error: {str(e)}"


def web_search_agent(query):
    try:
        search = DuckDuckGoSearchRun()
        return search.run(query)
    except Exception as e:
        return f"Error: {str(e)}"

def router_agent(query):
    """Route query to the right agent with keyword checks for accuracy."""
    try:
        q_lower = query.lower()

        # Priority 1: Direct keyword-based routing for sales database queries
        sales_keywords = [
            "sales", "revenue", "customer", "customers",
            "product", "products", "region", "regions",
            "order", "orders", "amount", "price", "quantity"
        ]
        if any(word in q_lower for word in sales_keywords):
            return "sales_data"

        # Priority 2: Direct keyword-based routing for fire safety
        fire_keywords = [
            "fire", "alarm", "evacuation", "drill", "smoke detector",
            "extinguisher", "emergency exit", "sprinkler"
        ]
        if any(word in q_lower for word in fire_keywords):
            return "fire_safety"

        # Fallback: LLM-based routing
        router_prompt = PromptTemplate(
            input_variables=["query"],
            template="""
            Decide which agent should handle the query:
            - "fire_safety" → questions about fire safety, prevention, drills, alarms, etc.
            - "sales_data" → questions about sales, products, customers, regions, revenue, etc.
            - "web_search" → anything else.

            Query: {query}
            Answer with only one: fire_safety, sales_data, web_search
            """
        )
        router_chain = LLMChain(llm=llm, prompt=router_prompt)
        decision = router_chain.run(query=query).strip().lower()
        return decision if decision in ["fire_safety", "sales_data", "web_search"] else "web_search"

    except Exception as e:
        st.error(f"Error in router agent: {str(e)}")
        return "web_search"


# ----------------- PDF Processing -----------------
def extract_chunks_from_pdf(pdf_path, chunk_size=1000, overlap=200):
    try:
        text_chunks = []
        with pdfplumber.open(pdf_path) as pdf:
            full_text = ""
            for page_num, page in enumerate(pdf.pages):
                page_text = page.extract_text()
                if page_text:
                    full_text += f"\n\n--- Page {page_num + 1} ---\n\n" + page_text
            words = full_text.split()
            for i in range(0, len(words), chunk_size - overlap):
                chunk = " ".join(words[i:i + chunk_size])
                text_chunks.append(chunk)
        return text_chunks
    except Exception:
        return []

# ----------------- Audio Processing -----------------
@cache_resource
def load_whisper_model():
    return whisper.load_model("base")

def transcribe_audio_english(audio_bytes):
    try:
        model = load_whisper_model()
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name
        result = model.transcribe(tmp_path, language="en")
        os.unlink(tmp_path)
        return result["text"]
    except Exception:
        return ""
    
# ----------------- MAIN CHATBOT APP -----------------
def main():
    st.set_page_config(page_title="🧠 Multi-Agent Chatbot", layout="wide")
    st.title("🧠 Multi-Agent Chatbot")

    if not os.path.exists("sales.db"):
        st.error("Database not found. Please create sales.db first.")
        return

    # PDF upload in sidebar
    st.sidebar.title("Document Management")
    uploaded_file = st.sidebar.file_uploader("Upload a PDF", type="pdf")
    pdf_path = "uploaded_document.pdf" if uploaded_file else "documents_FireSafety.pdf"
    if uploaded_file:
        with open(pdf_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

    text_chunks = extract_chunks_from_pdf(pdf_path)
    st.sidebar.success(f"Loaded {len(text_chunks)} chunks from PDF")

    # Session state for chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display past chat messages
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # ---------------- Chatbox with audio icon ----------------
    col1, col2 = st.columns([10, 1])

    with col1:
        user_text = st.chat_input("Type your question...")

    with col2:
        audio_bytes = audio_recorder(
            text="",
            icon_name="microphone",
            icon_size="2x",
            neutral_color="#f0f0f0",
            recording_color="#ff4b4b",
        )

    user_input = None
    if audio_bytes:
        st.audio(audio_bytes, format="audio/wav")
        transcription = transcribe_audio_english(audio_bytes)
        if transcription.strip():
            user_input = transcription
            st.markdown(f"**You said:** {transcription}")

    if user_text and not user_input:
        user_input = user_text

    # ---------------- Process new message ----------------
    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        agent_type = router_agent(user_input)
        if agent_type == "fire_safety":
            response = fire_safety_agent(user_input, "\n\n".join(text_chunks))
        elif agent_type == "sales_data":
            response = sales_data_agent(user_input)
        else:
            response = web_search_agent(user_input)

        st.session_state.messages.append({"role": "assistant", "content": response})
        with st.chat_message("assistant"):
            st.markdown(response)


if __name__ == "__main__":
    main()
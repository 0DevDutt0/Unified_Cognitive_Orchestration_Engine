import os
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain.agents import create_sql_agent
from langchain_community.utilities.sql_database import SQLDatabase
from langchain_groq import ChatGroq
from langchain.agents.agent_types import AgentType
from streamlit import cache_resource
import whisper
import tempfile

llm = ChatGroq(
    temperature=0,
    model_name="llama3-70b-8192",
    groq_api_key="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"
)

def build_sqlite_agent(db_path, return_intermediate_steps=False):
    db = SQLDatabase.from_uri(f"sqlite:///{db_path}")
    toolkit = SQLDatabaseToolkit(db=db, llm=llm)

    system_prefix = """
    You are a SQLite data expert.
    Always look up the data in the database.
    Always return only the exact answer to the question, without placeholders like (list the amounts...).
    If multiple values match, list them all separated by commas or in a table.
    Do not explain the SQL query unless explicitly asked.
    """

    agent = create_sql_agent(
        llm=llm,
        toolkit=toolkit,
        agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        verbose=True,
        return_intermediate_steps=return_intermediate_steps,
        prefix=system_prefix
    )
    return agent, db



@cache_resource
def load_whisper_model():
    return whisper.load_model("base")


def transcribe_audio(audio_bytes):
    model = load_whisper_model()
    # Save audio bytes to temporary file
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name
    result = model.transcribe(tmp_path)
    os.unlink(tmp_path)  # Delete temporary file
    return result["text"]
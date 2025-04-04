import streamlit as st
import requests
import json
import uuid
from sqlalchemy import create_engine, text

# FastAPI backend URL
BACKEND_URL = "https://techstack-uedv.onrender.com/generate"

# PostgreSQL connection
DATABASE_URL = "postgresql://technographics_dataset_user:6ygabdgGyylCn0v8WNXn42kBQLQptFHm@dpg-cvnmb0je5dus738lc100-a.oregon-postgres.render.com/technographics_dataset"
engine = create_engine(DATABASE_URL)

# Function to fetch chat history from PostgreSQL
def fetch_chat_history(session_id):
    with engine.connect() as conn:
        result = conn.execute(
            text("""
                SELECT message_type, message_content, timestamp
                FROM chat_history
                WHERE session_id = :session_id
                ORDER BY sequence ASC
            """),
            {"session_id": session_id}
        ).fetchall()
        return [{"type": row[0], "content": row[1], "timestamp": row[2]} for row in result]

# Function to fetch all session IDs
def fetch_all_sessions():
    with engine.connect() as conn:
        result = conn.execute(text("SELECT DISTINCT session_id FROM chat_history ORDER BY session_id ASC")).fetchall()
        return [row[0] for row in result]

# Streamlit app
st.set_page_config(page_title="TechStack Scout", layout="wide")

# Sidebar with session options and project info
with st.sidebar:
    st.title("TechStack Scout")
    st.write(
        "TechStack Scout is an AI-powered tool that **automates data collection** on company tech stacks. "
        "It scrapes web sources, processes data using **LLMs (GPT-4 via LangChain)**, and provides structured insights. "
        "Sales teams can query CRM, communication tools, and more using this chatbot."
    )

    # Fetch all sessions
    session_list = fetch_all_sessions()

    # Initialize session state
    if "session_list" not in st.session_state:
        st.session_state.session_list = session_list

    # Create a new session button
    if st.button("➕ Create New Session"):
        new_session_id = str(uuid.uuid4())  # Generate unique session ID
        st.session_state.session_id = new_session_id
        st.session_state.messages = []  # Start fresh chat

        # Add new session to the dropdown list dynamically
        st.session_state.session_list.append(new_session_id)
        st.rerun()

    # Session selector
    session_id = st.selectbox("Select a session:", st.session_state.session_list, index=len(st.session_state.session_list) - 1)

    # Store selected session in session state and load history
    if session_id and ("session_id" not in st.session_state or st.session_state.session_id != session_id):
        st.session_state.session_id = session_id
        st.session_state.messages = fetch_chat_history(session_id)  # Auto-load history
        st.rerun()

    st.write(f"**Active Session ID:** `{st.session_state.session_id}`" if "session_id" in st.session_state else "**No Active Session**")

# Title
st.title("TechStack Scout Chat")

# Display chat history
if "messages" in st.session_state:
    for message in st.session_state.messages:
        with st.chat_message(message["type"]):
            st.write(f"{message['content']}  \n*({message['timestamp']})*")

# Chat input
user_query = st.chat_input("Type your message here...")

if user_query and "session_id" in st.session_state:
    # Display user message
    with st.chat_message("human"):
        st.write(user_query)

    # Add user message to session state
    st.session_state.messages.append({"type": "human", "content": user_query, "timestamp": "now"})

    # Send request to FastAPI backend
    try:
        response = requests.post(
            BACKEND_URL,
            json={"user_query": user_query, "session_id": st.session_state.session_id},
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()

        # Parse the response
        result = response.json()
        ai_response = result["response"]

        # Display AI response
        with st.chat_message("ai"):
            st.write(ai_response)

        # Add AI response to session state
        st.session_state.messages.append({"type": "ai", "content": ai_response, "timestamp": "now"})

    except requests.exceptions.RequestException as e:
        st.error(f"Error communicating with backend: {e}")

# Clear chat button
if st.button("🗑️ Clear Chat"):
    st.session_state.messages = []
    st.rerun()

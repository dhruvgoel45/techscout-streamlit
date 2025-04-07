import streamlit as st
import requests
import json
import uuid
from sqlalchemy import create_engine, text

# Set page config as the first Streamlit command
st.set_page_config(page_title="TechStack Scout", layout="wide")

# Custom CSS for animations and styling
st.markdown("""
    <style>
    /* Fade-in animation for tabs and containers */
    .fade-in {
        animation: fadeIn 0.5s ease-in;
    }
    @keyframes fadeIn {
        0% { opacity: 0; }
        100% { opacity: 1; }
    }
    /* Hover effect for buttons */
    .stButton>button {
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        transform: scale(1.05);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    /* Box styling for tools and companies */
    .tool-box, .company-box {
        border: 1px solid #ddd;
        padding: 10px;
        border-radius: 5px;
        background-color: #f9f9f9;
        animation: fadeIn 0.5s ease-in;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    .tool-box:hover, .company-box:hover {
        transform: scale(1.02);
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    </style>
""", unsafe_allow_html=True)

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

# Function to fetch all session details
def fetch_all_sessions():
    with st.spinner("Loading sessions..."):
        with engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT session_id, title 
                    FROM session_details 
                    ORDER BY created_at ASC
                """)
            ).fetchall()
            return [{"session_id": row[0], "title": row[1]} for row in result]

# Function to fetch 10 random companies
def fetch_random_companies():
    with st.spinner("Fetching random companies..."):
        with engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT company_id, name, description, company_size, state, country, city, zip_code, address, url
                    FROM companies
                    ORDER BY RANDOM()
                    LIMIT 10
                """)
            ).fetchall()
            return [
                {
                    "company_id": row[0], "name": row[1], "description": row[2], "company_size": row[3],
                    "state": row[4], "country": row[5], "city": row[6], "zip_code": row[7], "address": row[8], "url": row[9]
                } for row in result
            ]

# Function to search companies by name
def search_companies(search_term):
    with st.spinner("Searching companies..."):
        with engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT company_id, name, description, company_size, state, country, city, zip_code, address, url
                    FROM companies
                    WHERE name ILIKE :search_term
                    ORDER BY name
                    LIMIT 10
                """),
                {"search_term": f"%{search_term}%"}
            ).fetchall()
            return [
                {
                    "company_id": row[0], "name": row[1], "description": row[2], "company_size": row[3],
                    "state": row[4], "country": row[5], "city": row[6], "zip_code": row[7], "address": row[8], "url": row[9]
                } for row in result
            ]

# Function to fetch 10 random tools
def fetch_random_tools():
    with st.spinner("Fetching random tools..."):
        with engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT tool_id, name, type
                    FROM tools
                    ORDER BY RANDOM()
                    LIMIT 10
                """)
            ).fetchall()
            return [{"tool_id": row[0], "name": row[1], "type": row[2]} for row in result]

# Function to search tools by name
def search_tools(search_term):
    with st.spinner("Searching tools..."):
        with engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT tool_id, name, type
                    FROM tools
                    WHERE name ILIKE :search_term
                    ORDER BY name
                    LIMIT 10
                """),
                {"search_term": f"%{search_term}%"}
            ).fetchall()
            return [{"tool_id": row[0], "name": row[1], "type": row[2]} for row in result]

# Function to fetch companies using a specific tool
def fetch_companies_by_tool(tool_id):
    with st.spinner("Loading companies using this tool..."):
        with engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT c.company_id, c.name, c.description, c.company_size, c.state, c.country, c.city, c.zip_code, c.address, c.url
                    FROM companies c
                    JOIN company_tools ct ON c.company_id = ct.company_id
                    WHERE ct.tool_id = :tool_id
                    ORDER BY c.name
                    LIMIT 10
                """),
                {"tool_id": tool_id}
            ).fetchall()
            return [
                {
                    "company_id": row[0], "name": row[1], "description": row[2], "company_size": row[3],
                    "state": row[4], "country": row[5], "city": row[6], "zip_code": row[7], "address": row[8], "url": row[9]
                } for row in result
            ]

# Function to fetch tools for a specific company
def fetch_company_tools(company_id):
    with st.spinner("Loading tools..."):
        with engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT t.name, t.type
                    FROM tools t
                    JOIN company_tools ct ON t.tool_id = ct.tool_id
                    WHERE ct.company_id = :company_id
                """),
                {"company_id": company_id}
            ).fetchall()
            return [{"name": row[0], "type": row[1]} for row in result]

# Tabs for Chat, Companies, and Tools
tab1, tab2, tab3 = st.tabs(["Chat", "Companies", "Tools"])

# Chat Tab
with tab1:
    with st.sidebar:
        st.title("TechStack Scout")
        st.write(
            "TechStack Scout is an AI-powered tool that **automates data collection** on company tech stacks. "
            "It scrapes web sources, processes data using **LLMs (GPT-4 via LangChain)**, and provides structured insights. "
            "Sales teams can query CRM, communication tools, and more using this chatbot."
        )

        session_list = fetch_all_sessions()
        if "session_list" not in st.session_state:
            st.session_state.session_list = session_list if session_list else [{"session_id": str(uuid.uuid4()), "title": "New Session"}]
        elif not st.session_state.session_list:
            st.session_state.session_list = [{"session_id": str(uuid.uuid4()), "title": "New Session"}]

        if st.button("➕ Create New Session"):
            new_session_id = str(uuid.uuid4())
            st.session_state.session_id = new_session_id
            st.session_state.messages = []
            with engine.connect() as conn:
                conn.execute(
                    text("INSERT INTO session_details (session_id, title) VALUES (:session_id, :title)"),
                    {"session_id": new_session_id, "title": "New Session"}
                )
                conn.commit()
            st.session_state.session_list.append({"session_id": new_session_id, "title": "New Session"})
            st.rerun()

        session_options = [f"{s['title']} ({s['session_id'][:8]}...)" for s in st.session_state.session_list]
        default_index = len(session_options) - 1 if session_options else 0
        selected_index = st.selectbox(
            "Select a session:",
            range(len(session_options)),
            format_func=lambda i: session_options[i],
            index=default_index,
            key="session_selector"
        )
        
        if selected_index is not None and session_options:
            selected_session = st.session_state.session_list[selected_index]
            session_id = selected_session["session_id"]
        else:
            session_id = st.session_state.session_list[0]["session_id"]
            selected_session = st.session_state.session_list[0]

        if session_id and ("session_id" not in st.session_state or st.session_state.session_id != session_id):
            st.session_state.session_id = session_id
            st.session_state.messages = fetch_chat_history(session_id)
            st.rerun()

        st.write(f"**Active Session:** `{selected_session['title']}` (`{session_id[:8]}...`)")

    st.title("TechStack Scout Chat")

    if "messages" not in st.session_state:
        st.session_state.messages = fetch_chat_history(session_id)

    for message in st.session_state.messages:
        with st.chat_message(message["type"]):
            st.write(f"{message['content']}  \n*({message['timestamp']})*")

    user_query = st.chat_input("Type your message here...")
    if user_query and "session_id" in st.session_state:
        with st.chat_message("human"):
            st.write(user_query)
        st.session_state.messages.append({"type": "human", "content": user_query, "timestamp": "now"})
        with st.spinner("Generating response..."):
            try:
                response = requests.post(
                    BACKEND_URL,
                    json={"user_query": user_query, "session_id": st.session_state.session_id},
                    headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()
                result = response.json()
                ai_response = result["response"]
                with st.chat_message("ai"):
                    st.write(ai_response)
                st.session_state.messages.append({"type": "ai", "content": ai_response, "timestamp": "now"})
                if len([m for m in st.session_state.messages if m["type"] == "human"]) == 1:
                    for session in st.session_state.session_list:
                        if session["session_id"] == st.session_state.session_id:
                            session["title"] = user_query
                            break
                    st.rerun()
            except requests.exceptions.RequestException as e:
                st.error(f"Error communicating with backend: {e}")

    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.rerun()

# Companies Tab (formerly Dashboard)
with tab2:
    st.title("Company Explorer")
    st.write("Explore details and tools used by companies. Search or browse random selections.")

    # Search functionality for companies
    st.subheader("Search for a Company")
    search_term = st.text_input("Enter company name", key="company_search")
    if search_term:
        search_results = search_companies(search_term)
        if search_results:
            st.write(f"Found {len(search_results)} matching companies:")
            cols = st.columns(5)
            for i, company in enumerate(search_results):
                with cols[i % 5]:
                    if st.button(company["name"], key=f"search_company_{company['company_id']}"):
                        if "selected_companies" not in st.session_state:
                            st.session_state.selected_companies = {}
                        if company["company_id"] not in st.session_state.selected_companies:
                            st.session_state.selected_companies[company["company_id"]] = company
        else:
            st.write("No companies found matching your search. Try a different name.")

    # Random companies section
    if "random_companies" not in st.session_state:
        st.session_state.random_companies = fetch_random_companies()
    if "selected_companies" not in st.session_state:
        st.session_state.selected_companies = {}

    st.subheader("Random Companies")
    cols = st.columns(5)
    for i, company in enumerate(st.session_state.random_companies):
        with cols[i % 5]:
            if st.button(company["name"], key=f"random_company_{company['company_id']}"):
                if company["company_id"] not in st.session_state.selected_companies:
                    st.session_state.selected_companies[company["company_id"]] = company

    if st.button("🔄 Refresh Random Companies"):
        with st.spinner("Refreshing companies..."):
            st.session_state.random_companies = fetch_random_companies()
            st.rerun()

    # Display tabs for selected companies
    if st.session_state.selected_companies:
        st.subheader("Selected Companies")
        company_tabs = st.tabs([company["name"] for company in st.session_state.selected_companies.values()])
        
        for tab, company in zip(company_tabs, st.session_state.selected_companies.values()):
            with tab:
                st.markdown(f"<div class='fade-in'><h3>{company['name']}</h3></div>", unsafe_allow_html=True)
                with st.container():
                    st.write(f"**Description**: {company['description'] or 'No description available'}")
                    st.write(f"**Company Size**: {company['company_size'] or 'Unknown Size'}")
                    st.write(f"**Location**: {company['city'] or 'Unknown City'}, {company['state'] or 'Unknown State'}, {company['country'] or 'Unknown Country'}")
                    st.write(f"**Zip Code**: {company['zip_code'] or 'Unknown Zip'}")
                    st.write(f"**Address**: {company['address'] or 'Unknown Address'}")
                    if company['url']:
                        st.write(f"**Website**: [{company['url']}]({company['url']})")
                    else:
                        st.write("**Website**: Unknown URL")

                tools = fetch_company_tools(company["company_id"])
                if tools:
                    st.write("### Tools Used")
                    # Get unique tool types and create filter options
                    tool_types = sorted(set(tool["type"] for tool in tools))
                    filter_type = st.selectbox(
                        "Filter tools by type",
                        ["All"] + tool_types,
                        key=f"filter_{company['company_id']}"
                    )
                    # Filter tools based on selected type
                    filtered_tools = tools if filter_type == "All" else [tool for tool in tools if tool["type"] == filter_type]
                    
                    num_cols = 3
                    for i in range(0, len(filtered_tools), num_cols):
                        cols = st.columns(num_cols)
                        for j, tool in enumerate(filtered_tools[i:i+num_cols]):
                            with cols[j]:
                                st.markdown(
                                    f"""
                                    <div class='tool-box'>
                                        <strong>{tool['name']}</strong><br>
                                        Type: {tool['type']}
                                    </div>
                                    """,
                                    unsafe_allow_html=True
                                )
                else:
                    st.write("No tools found for this company.")
                
                if st.button("Close Tab", key=f"close_company_{company['company_id']}"):
                    del st.session_state.selected_companies[company["company_id"]]
                    st.rerun()

# Tools Tab
with tab3:
    st.title("Tool Explorer")
    st.write("Explore tools and the companies using them. Search or browse random selections.")

    # Search functionality for tools
    st.subheader("Search for a Tool")
    tool_search_term = st.text_input("Enter tool name", key="tool_search")
    if tool_search_term:
        search_results = search_tools(tool_search_term)
        if search_results:
            st.write(f"Found {len(search_results)} matching tools:")
            cols = st.columns(5)
            for i, tool in enumerate(search_results):
                with cols[i % 5]:
                    if st.button(tool["name"], key=f"search_tool_{tool['tool_id']}"):
                        if "selected_tools" not in st.session_state:
                            st.session_state.selected_tools = {}
                        if tool["tool_id"] not in st.session_state.selected_tools:
                            st.session_state.selected_tools[tool["tool_id"]] = tool
        else:
            st.write("No tools found matching your search. Try a different name.")

    # Random tools section
    if "random_tools" not in st.session_state:
        st.session_state.random_tools = fetch_random_tools()
    if "selected_tools" not in st.session_state:
        st.session_state.selected_tools = {}

    st.subheader("Random Tools")
    cols = st.columns(5)
    for i, tool in enumerate(st.session_state.random_tools):
        with cols[i % 5]:
            if st.button(tool["name"], key=f"random_tool_{tool['tool_id']}"):
                if tool["tool_id"] not in st.session_state.selected_tools:
                    st.session_state.selected_tools[tool["tool_id"]] = tool

    if st.button("🔄 Refresh Random Tools"):
        with st.spinner("Refreshing tools..."):
            st.session_state.random_tools = fetch_random_tools()
            st.rerun()

    # Display companies for selected tools
    if st.session_state.selected_tools:
        st.subheader("Selected Tools")
        tool_tabs = st.tabs([tool["name"] for tool in st.session_state.selected_tools.values()])
        
        for tab, tool in zip(tool_tabs, st.session_state.selected_tools.values()):
            with tab:
                st.markdown(f"<div class='fade-in'><h3>{tool['name']} ({tool['type']})</h3></div>", unsafe_allow_html=True)
                companies = fetch_companies_by_tool(tool["tool_id"])
                if companies:
                    st.write("### Companies Using This Tool")
                    num_cols = 3
                    for i in range(0, len(companies), num_cols):
                        cols = st.columns(num_cols)
                        for j, company in enumerate(companies[i:i+num_cols]):
                            with cols[j]:
                                if st.button(
                                    company["name"],
                                    key=f"company_from_tool_{company['company_id']}_{tool['tool_id']}",
                                    help="Click to view company details"
                                ):
                                    if "selected_companies" not in st.session_state:
                                        st.session_state.selected_companies = {}
                                    if company["company_id"] not in st.session_state.selected_companies:
                                        st.session_state.selected_companies[company["company_id"]] = company
                                st.markdown(
                                    f"""
                                    <div class='company-box'>
                                        <strong>{company['name']}</strong><br>
                                        Size: {company['company_size'] or 'Unknown'}
                                    </div>
                                    """,
                                    unsafe_allow_html=True
                                )
                else:
                    st.write("No companies found using this tool.")

                if st.button("Close Tab", key=f"close_tool_{tool['tool_id']}"):
                    del st.session_state.selected_tools[tool["tool_id"]]
                    st.rerun()

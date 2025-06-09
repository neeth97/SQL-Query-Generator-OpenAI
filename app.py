from dotenv import load_dotenv
import os
import glob
import sqlite3
import json
import re
import streamlit as st
import openai

# Load environment variables
load_dotenv()

# Configure OpenAI key
openai.api_key = os.getenv("OPENAI_API_KEY")


def get_openai_response(question: str, prompt: str) -> str:
    """Send a question + prompt to OpenAI and return the raw text response."""
    resp = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": question},
        ],
        temperature=0,
    )
    return resp.choices[0].message.content.strip()


def read_sql_query(sql: str, db_path: str) -> list[tuple]:
    """Execute SQL against the given SQLite database and return all rows."""
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute(sql)
        return cur.fetchall()
    finally:
        conn.close()


def get_db_schema(db_path: str) -> str:
    """Return a one-line description of tables and columns in the SQLite DB."""
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cur.fetchall()]
        parts = []
        for tbl in tables:
            cur.execute(f"PRAGMA table_info('{tbl}')")
            cols = [col[1] for col in cur.fetchall()]
            parts.append(f"{tbl}({', '.join(cols)})")
        return "; ".join(parts)
    finally:
        conn.close()


# Base prompt for SQL generation
base_prompt = """
You are an expert in converting English questions into SQL queries for sales data analysis.
You have access to multiple SQLite databases; here are their schemas:
{schemas}

For any user question, write SQL statement that returns the desired result by querying or 
joining these tables as necessary. Return only the SQL string, without any additional text or markdown.
"""

# Build a path relative to this script's location
base_dir = os.path.dirname(__file__)
db_dir = os.path.join(base_dir, "data", "sql_db")

# Discover all .db files in the relative data/sql_db directory
db_files = glob.glob(os.path.join(db_dir, "*.db"))
if not db_files:
    st.error(f"No SQLite database files (*.db) found in {db_dir}.")
    st.stop()

# Build the schema string for all DBs
schemas = "\n".join(f"{os.path.basename(db)}: {get_db_schema(db)}" for db in db_files)
full_prompt = base_prompt.format(schemas=schemas)

# Streamlit UI
st.set_page_config(page_title="Auto Multi-DB SQL Retriever")
st.header("📊 OpenAI-Powered Multi-DB SQL Query")

question = st.text_input("Enter your question in plain English:")

if st.button("Run Query"):
    if not question.strip():
        st.warning("Please enter a question.")
    else:
        # 1. Ask OpenAI to decide DBs and generate SQL per DB
        response = get_openai_response(question, full_prompt)
        st.markdown("**OpenAI response (raw JSON):**")
        st.code(response, language="json")

        # 2. Extract JSON (fenced or raw) and parse
        json_str = None

        # try a fenced ```json block first
        fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", response, re.DOTALL)
        if fenced:
            json_str = fenced.group(1)
        else:
            # fallback to any {...} in the text
            direct = re.search(r"(\{.*?\})", response, re.DOTALL)
            if direct:
                json_str = direct.group(1)

        # if we still have nothing, assume the whole response is JSON
        if not json_str:
            json_str = response

        try:
            queries = json.loads(json_str)
        except json.JSONDecodeError as e:
            st.error(f"Failed to parse JSON from OpenAI: {e}")
        else:
            # 3. Execute each SQL on its respective DB
            for db_name, sql in queries.items():
                db_path = next(
                    (p for p in db_files if os.path.basename(p) == db_name), None
                )
                if not db_path:
                    st.error(f"Database '{db_name}' not found locally.")
                    continue

                with st.expander(f"Results from `{db_name}`", expanded=True):
                    try:
                        rows = read_sql_query(sql, db_path)
                        if rows:
                            for row in rows:
                                st.write(row)
                        else:
                            st.info("No rows returned.")
                    except Exception as e:
                        st.error(f"Error running query on '{db_name}': {e}")

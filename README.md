# Auto Multi-DB SQL Retriever

A simple Streamlit app that lets you ask plain-English questions and automatically generates and runs SQL queries across one or more SQLite databases built from CSV files.

## Features

- **CSV → SQLite**  
  Converts every CSV in `data/csv/` into its own SQLite database in `data/sql_db/` using `create_sql_db.py`
  
- **Natural-language SQL**  
  Uses OpenAI to translate your question into SQL for the relevant DB(s)
  
- **Interactive UI**  
  Streamlit interface to enter questions, view generated SQL, and see query results instantly.

  <img width="757" alt="Screenshot 2025-06-09 at 1 36 18 PM" src="https://github.com/user-attachments/assets/dc002be1-457f-4968-afbd-f4d2da9675d5" />

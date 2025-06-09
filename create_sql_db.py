import os
import glob
import sqlite3
import pandas as pd

# Paths
# Build paths relative to this script's location
base_dir = os.path.dirname(__file__)
csv_folder = os.path.join(base_dir, "data", "csv")
db_folder = os.path.join(base_dir, "data", "sql_db")


# Helper: map pandas dtypes to SQLite types
def sqlite_type(dtype):
    if pd.api.types.is_integer_dtype(dtype):
        return "INTEGER"
    elif pd.api.types.is_float_dtype(dtype):
        return "REAL"
    elif pd.api.types.is_bool_dtype(dtype):
        return "INTEGER"  # store booleans as INTEGER (0/1)
    else:
        # for anything else (including datetimes), fall back to TEXT
        return "TEXT"


# Find all CSV files
csv_files = glob.glob(os.path.join(csv_folder, "*.csv"))

# # Print all CSV file names found
# print("CSV files found:")
# for path in csv_files:
#     print(f" - {os.path.basename(path)}")

for csv_path in csv_files:
    # Derive names
    base_name = os.path.splitext(os.path.basename(csv_path))[0]
    db_path = os.path.join(db_folder, f"{base_name}.db")
    table_name = base_name  # use same base name for the table

    # Load CSV into DataFrame
    df = pd.read_csv(csv_path)

    # Connect to (or create) a separate SQLite DB for this CSV
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # Build CREATE TABLE statement with inferred column types
    col_types = {col: sqlite_type(dtype) for col, dtype in df.dtypes.items()}
    cols_decl = ", ".join(f"'{col}' {typ}" for col, typ in col_types.items())
    create_sql = f"CREATE TABLE IF NOT EXISTS '{table_name}' ({cols_decl});"
    cur.execute(create_sql)

    # Prepare INSERT statement
    cols = df.columns.tolist()
    placeholders = ", ".join("?" for _ in cols)
    cols_list = ", ".join(f"'{c}'" for c in cols)
    insert_sql = f"INSERT INTO '{table_name}' ({cols_list}) VALUES ({placeholders});"

    # Bulk-insert all rows
    cur.executemany(insert_sql, df.itertuples(index=False, name=None))
    conn.commit()

    # # Display top 5 rows for verification
    # print(f"\nTop 5 rows in '{table_name}' (DB: {db_path}):")
    # print(cols)
    # cur.execute(f"SELECT * FROM '{table_name}' LIMIT 5;")
    # for row in cur.fetchall():
    #     print(row)

    # # After inserting data, print the column types for this table
    # print(f"\nColumn types in '{table_name}' (DB: {db_path}):")
    # cur.execute(f"PRAGMA table_info('{table_name}');")
    # # PRAGMA table_info returns rows of:
    # # (cid, name, type, notnull, dflt_value, pk)
    # for cid, name, col_type, notnull, dflt_value, pk in cur.fetchall():
    #     print(f" - {name}: {col_type}")

    # Close connection
    conn.close()

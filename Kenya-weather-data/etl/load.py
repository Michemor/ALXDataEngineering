"""
Loading the data to Neone
"""
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from pathlib import Path
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import MetaData, Table
from sqlalchemy.dialects.postgresql import insert


env_path = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(dotenv_path=env_path)


def get_engine():
    """
    Create a SQLAlchemy engine using the database URL from the environment variables.
    """
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise ValueError("DATABASE_URL is not set in the environment variables.")
    return create_engine(
        db_url,
        pool_pre_ping=True,
        pool_recycle=300,
        )

def init_schema(engine):
    """
    Initialize the database schema by executing the SQL commands in the schema.sql file.
    """
    with engine.begin() as connection, open("db/schema.sql") as f:
        connection.execute(text(f.read()))
    print("Database schema initialized successfully.")

def load_to_database(engine, df, table_name, if_exists='append'):
    """
    Load a DataFrame to the specified table in the database.
    If the table exists, it will be replaced.
    """
    df.to_sql(table_name, con=engine, if_exists=if_exists, index=False)
    print(f"Data loaded to table '{table_name}' successfully.")


def upsert_to_database(engine, df, table_name, conflict_columns, batch_size=500):
    """
    Upsert a DataFrame to the specified table in the database.
    If a record with the same unique columns exists, it will be updated; otherwise, it will be inserted.
    Batches inserts to minimize round trips to the database.
    """
    metadata = MetaData()
    table = Table(table_name, metadata, autoload_with=engine)
    records = df.to_dict(orient='records')

    with engine.begin() as conn:
        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]
            stmt = insert(table).values(batch)
            update_cols = {c.name: c for c in stmt.excluded if c.name not in conflict_columns}
            stmt = stmt.on_conflict_do_update(index_elements=conflict_columns, set_=update_cols)
            conn.execute(stmt)
    print(f"Data upserted to table '{table_name}' successfully.")
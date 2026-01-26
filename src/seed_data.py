import psycopg2
import uuid
import random
import datetime
import json
from typedb.driver import TypeDB, SessionType, TransactionType

# Mock Data Generation
def generate_embedding(dim=1536):
    """Generates a random normalized vector for dummy embedding."""
    vec = [random.random() for _ in range(dim)]
    # Simple normalization (not strictly necessary for dummy data but good practice)
    magnitude = sum(x**2 for x in vec) ** 0.5
    return [x/magnitude for x in vec]

DEMO_DOCUMENTS = [
    {
        "title": "Project Riemann Architecture Overview",
        "content": "Project Riemann aims to build a Palantir-style ontology system using TypeDB and PostgreSQL. This document outlines the hybrid architecture where structured relationships live in TypeDB and unstructured content including vectors live in Postgres.",
        "summary": "Architecture overview of Project Riemann.",
        "author": "Alice Engineer",
        "email": "alice@riemann.ai"
    },
    {
        "title": "Q1 2026 Roadmap",
        "content": "The roadmap for Q1 2026 includes integrating LlamaIndex for natural language queries, setting up Airflow pipelines for data ingestion, and building a visualization dashboard using TypeDB Studio. We also plan to optimize pgvector indexing.",
        "summary": "Q1 2026 development roadmap.",
        "author": "Alice Engineer",
        "email": "alice@riemann.ai"
    }
]

def insert_data():
    print("--- Starting Data Seeding ---")
    
    # 1. Connect to PostgreSQL
    pg_conn = psycopg2.connect(
        host="localhost", port="5432", database="airflow", user="airflow", password="airflow"
    )
    pg_conn.autocommit = True
    pg_cursor = pg_conn.cursor()

    # 2. Connect to TypeDB
    driver = TypeDB.core_driver("127.0.0.1:1729")
    
    try:
        # Prepare TypeDB Session
        with driver.session("riemann_db", SessionType.DATA) as session:
            
            for doc in DEMO_DOCUMENTS:
                # Generate IDs
                external_ref_id = str(uuid.uuid4()) # ID linking both systems
                doc_uuid = str(uuid.uuid4()) # Postgres Primary Key
                created_at = datetime.datetime.now()
                embedding = generate_embedding()
                
                print(f"Processing Document: '{doc['title']}'")

                # --- A. Insert into PostgreSQL (System of Record) ---
                print(f"  -> Inserting into PostgreSQL...")
                pg_query = """
                    INSERT INTO documents_sor (id, external_ref_id, title, content, summary, created_at, embedding)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """
                pg_cursor.execute(pg_query, (
                    doc_uuid, 
                    external_ref_id, 
                    doc['title'], 
                    doc['content'], 
                    doc['summary'], 
                    created_at, 
                    embedding
                ))

                # --- B. Insert into TypeDB (Ontology Layer) ---
                print(f"  -> Inserting into TypeDB...")
                with session.transaction(TransactionType.WRITE) as tx:
                    # 1. Insert or Get Person (Author)
                    # Simple check-and-insert logic using 'insert' for simplicity in TQL
                    # Note: In production, you might match first to avoid duplicates, but 'insert' allows variable binding.
                    
                    tql_insert = f"""
                    insert
                    $p isa person, 
                        has name "{doc['author']}", 
                        has email "{doc['email']}",
                        has identifier "{doc['email']}";
                    
                    $d isa document,
                        has title "{doc['title']}",
                        has summary "{doc['summary']}",
                        has external-ref "{external_ref_id}",
                        has identifier "{external_ref_id}",
                        has created-at {created_at.strftime('%Y-%m-%dT%H:%M:%S')};
                    
                    (author: $p, authored-document: $d) isa authorship;
                    """
                    
                    tx.query.insert(tql_insert)
                    tx.commit()
                print("  -> Done.")

    except Exception as e:
        print(f"Error seeding data: {e}")
    finally:
        pg_cursor.close()
        pg_conn.close()
        driver.close()
        print("--- Data Seeding Completed ---")

if __name__ == "__main__":
    insert_data()

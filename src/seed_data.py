import psycopg2
import uuid
import random
import datetime
import json
from typedb.driver import TypeDB, SessionType, TransactionType

import hashlib

# Mock Data Generation
def generate_deterministic_uuid(content):
    """Generates a consistent UUID based on content string."""
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, content))

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
                # Generate Deterministic IDs
                # We use the title as the unique seed for the Document ID
                external_ref_id = generate_deterministic_uuid(doc['title']) 
                doc_uuid = generate_deterministic_uuid(doc['title'] + "_pg_id")
                
                created_at = datetime.datetime.now()
                embedding = generate_embedding()
                
                print(f"Processing Document: '{doc['title']}'")

                # --- A. Insert into PostgreSQL (Upsert / Idempotent) ---
                print(f"  -> Inserting into PostgreSQL (Upsert)...")
                pg_query = """
                    INSERT INTO documents_sor (id, external_ref_id, title, content, summary, created_at, embedding)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (external_ref_id) 
                    DO UPDATE SET 
                        title = EXCLUDED.title,
                        content = EXCLUDED.content,
                        summary = EXCLUDED.summary,
                        metadata = EXCLUDED.metadata;
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

                # --- B. Insert into TypeDB (Idempotent Pattern) ---
                print(f"  -> Inserting into TypeDB (Upsert)...")
                with session.transaction(TransactionType.WRITE) as tx:
                    # TQL Upsert Logic:
                    # 1. Match Author (or insert if not exists) - Simplified by just inserting and relying on logic, 
                    # but for true idempotency we should match.
                    # Since TypeQL 'insert' just adds, running it twice creates duplicates.
                    # We need 'match ... insert ...' or check existence.
                    
                    # Pattern: Match existing person? No, just match attributes.
                    # Ideally: match $p isa person, has email "..."; insert ... (this extends)
                    # To "get or create":
                    # insert $p isa person...; won't dedupe.
                    
                    # Robust "Get or Create" in TypeDB Python driver:
                    # 1. Check if Person exists
                    
                    tql_check_person = f'match $p isa person, has email "{doc["email"]}"; get $p;'
                    person_iterator = tx.query.get(tql_check_person)
                    person_exists = any(True for _ in person_iterator)
                    
                    if not person_exists:
                        # Create Person
                         tx.query.insert(f'''
                            insert $p isa person, 
                                has name "{doc['author']}", 
                                has email "{doc['email']}", 
                                has identifier "{doc['email']}";
                        ''')
                        
                    # 2. Check if Document exists
                    tql_check_doc = f'match $d isa document, has external-ref "{external_ref_id}"; get $d;'
                    doc_iterator = tx.query.get(tql_check_doc)
                    doc_exists = any(True for _ in doc_iterator)
                    
                    if not doc_exists:
                        # Create Document
                        tx.query.insert(f'''
                            insert $d isa document,
                                has title "{doc['title']}",
                                has summary "{doc['summary']}",
                                has external-ref "{external_ref_id}",
                                has identifier "{external_ref_id}",
                                has created-at {created_at.strftime('%Y-%m-%dT%H:%M:%S')};
                        ''')

                    # 3. Ensure Relation Logic (Idempotent)
                    # We match both nodes and ensure relation
                    tql_relation = f"""
                    match
                        $p isa person, has email "{doc['email']}";
                        $d isa document, has external-ref "{external_ref_id}";
                        not {{ (author: $p, authored-document: $d) isa authorship; }};
                    insert
                        (author: $p, authored-document: $d) isa authorship;
                    """
                    tx.query.insert(tql_relation)
                    
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

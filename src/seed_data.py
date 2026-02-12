import psycopg2
import uuid
import random
import datetime
import json
from typedb.driver import TypeDB, TransactionType, Credentials, DriverOptions
import traceback

# Mock Data Generation
def generate_deterministic_uuid(content):
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, content))

def generate_embedding(dim=1536):
    vec = [random.random() for _ in range(dim)]
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
    
    pg_conn = None
    pg_cursor = None
    
    try:
        # 1. Connect to PostgreSQL
        print("Connecting to PostgreSQL...")
        pg_conn = psycopg2.connect(
            host="localhost", port="5432", database="airflow", user="airflow", password="airflow"
        )
        pg_conn.autocommit = True
        pg_cursor = pg_conn.cursor()

        # 2. Connect to TypeDB
        print("Connecting to TypeDB...")
        with TypeDB.driver("http://localhost:1729", Credentials("admin", "password"), DriverOptions(False, None)) as driver:
            
            if not driver.databases.contains("riemann_db"):
                print("Database 'riemann_db' not found. Creating...")
                driver.databases.create("riemann_db")
            
            with driver.transaction("riemann_db", TransactionType.WRITE) as tx:
                
                for doc in DEMO_DOCUMENTS:
                    external_ref_id = generate_deterministic_uuid(doc['title']) 
                    doc_uuid = generate_deterministic_uuid(doc['title'] + "_pg_id")
                    created_at = datetime.datetime.now()
                    embedding = generate_embedding()
                    
                    print(f"Processing Document: {doc['title']}")

                    pg_query = """
                        INSERT INTO documents_sor (id, external_ref_id, title, content, summary, created_at, embedding)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (external_ref_id) 
                        DO UPDATE SET 
                            title = EXCLUDED.title,
                            content = EXCLUDED.content,
                            summary = EXCLUDED.summary;
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

                    print(f"  -> Inserting into TypeDB (Upsert)...")
                    
                    tql_check_p = f'match $p isa person, has email "{doc["email"]}";'
                    p_iter = tx.query(tql_check_p).resolve()
                    p_exists = False
                    for _ in p_iter:
                        p_exists = True
                        break
                    
                    if not p_exists:
                        print(f"     Creating Person: {doc['author']}")
                        tx.query(f'''
                            insert $p isa person, 
                                has full-name "{doc['author']}", 
                                has email "{doc['email']}", 
                                has identifier "{doc['email']}";
                        ''').resolve()
                        
                    tql_check_d = f'match $d isa document, has external-ref "{external_ref_id}";'
                    d_iter = tx.query(tql_check_d).resolve()
                    d_exists = False
                    for _ in d_iter:
                        d_exists = True
                        break
                    
                    if not d_exists:
                        print(f"     Creating Document Node: {doc['title']}")
                        dt_str = created_at.strftime('%Y-%m-%dT%H:%M:%S')
                        tx.query(f'''
                            insert $d isa document,
                                has title "{doc['title']}",
                                has summary "{doc['summary']}",
                                has external-ref "{external_ref_id}",
                                has identifier "{external_ref_id}",
                                has created-at {dt_str};
                        ''').resolve()

                    tql_rel_check = f"""
                    match
                        $p isa person, has email "{doc['email']}";
                        $d isa document, has external-ref "{external_ref_id}";
                        (author: $p, authored-document: $d) isa authorship;
                    """
                    r_iter = tx.query(tql_rel_check).resolve()
                    r_exists = False
                    for _ in r_iter:
                        r_exists = True
                        break

                    if not r_exists:
                        print("     Linking Author and Document...")
                        tql_rel = f"""
                        match
                            $p isa person, has email "{doc['email']}";
                            $d isa document, has external-ref "{external_ref_id}";
                        insert
                            (author: $p, authored-document: $d) isa authorship;
                        """
                        tx.query(tql_rel).resolve()
                    
                tx.commit()
                print("  -> TypeDB Transaction Committed.")
                
    except Exception as e:
        print(f"Error seeding data: {e}")
        traceback.print_exc()
    finally:
        if pg_cursor: pg_cursor.close()
        if pg_conn: pg_conn.close()
        print("--- Data Seeding Completed ---")

if __name__ == "__main__":
    insert_data()

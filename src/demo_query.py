import psycopg2
from typedb.driver import TypeDB, SessionType, TransactionType

def hybrid_query_demo(author_name: str):
    print(f"\n❓ QUERY: 'Find all documents written by {author_name} and show me their content.'\n")
    
    # ---------------------------------------------------------
    # Step 1: Semantic Search in TypeDB (The "Brain")
    # ---------------------------------------------------------
    print("🧠 [Step 1] Asking TypeDB for document IDs...")
    
    ext_refs = []
    
    try:
        driver = TypeDB.core_driver("127.0.0.1:1729")
        with driver.session("riemann_db", SessionType.DATA) as session:
            with session.transaction(TransactionType.READ) as tx:
                # TypeQL: Match person by name, find their authored documents, get external-refs
                query = f"""
                match 
                    $p isa person, has name "{author_name}";
                    $d isa document, has external-ref $ref;
                    (author: $p, authored-document: $d) isa authorship;
                get $ref;
                """
                iterator = tx.query.get(query)
                
                for result in iterator:
                    ref = result.get("ref").as_attribute().get_value()
                    ext_refs.append(ref)
                    print(f"    -> Found Entity: Document (Ref: {ref})")
                    
    except Exception as e:
        print(f"TypeDB Error: {e}")
        return

    if not ext_refs:
        print("    -> No documents found for this author.")
        return

    # ---------------------------------------------------------
    # Step 2: Content Retrieval in PostgreSQL (The "Library")
    # ---------------------------------------------------------
    print(f"\n📚 [Step 2] Fetching content context from PostgreSQL for {len(ext_refs)} documents...")
    
    try:
        pg_conn = psycopg2.connect(
            host="localhost", port="5432", database="airflow", user="airflow", password="airflow"
        )
        cursor = pg_conn.cursor()
        
        # SQL: Select content where ref_id is in the list we got from TypeDB
        # Using ANY(%s) for array parameter
        sql = "SELECT title, content, created_at FROM documents_sor WHERE external_ref_id = ANY(%s)"
        cursor.execute(sql, (ext_refs,))
        
        rows = cursor.fetchall()
        
        print("\n✅ [Result] Final Answer Construction:\n")
        for row in rows:
            title, content, created_at = row
            print(f"📄 Document: {title}")
            print(f"   Date: {created_at}")
            print(f"   Content snippet: \"{content[:100]}...\"")
            print("-" * 50)
            
        pg_conn.close()

    except Exception as e:
        print(f"Postgres Error: {e}")

if __name__ == "__main__":
    hybrid_query_demo("Alice Engineer")

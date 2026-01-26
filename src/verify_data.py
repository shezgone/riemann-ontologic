import psycopg2
from typedb.driver import TypeDB, SessionType, TransactionType

def verify_data():
    print("=== VERIFICATION REPORT ===\n")

    # 1. Check PostgreSQL
    print("[1] PostgreSQL Data (documents_sor):")
    try:
        pg_conn = psycopg2.connect(
            host="localhost", port="5432", database="airflow", user="airflow", password="airflow"
        )
        cursor = pg_conn.cursor()
        cursor.execute("SELECT external_ref_id, title, left(content, 30) || '...', created_at FROM documents_sor")
        rows = cursor.fetchall()
        print(f"Found {len(rows)} rows:")
        for row in rows:
            print(f"  - ID: {row[0]} | Title: {row[1]} | Content: {row[2]}")
        pg_conn.close()
    except Exception as e:
        print(f"Postgres Error: {e}")

    print("\n------------------------------------------------\n")

    # 2. Check TypeDB
    print("[2] TypeDB Knowledge Graph Data:")
    try:
        driver = TypeDB.core_driver("127.0.0.1:1729")
        with driver.session("riemann_db", SessionType.DATA) as session:
            with session.transaction(TransactionType.READ) as tx:
                
                # Query: Find all people who authored documents
                print("Querying: Match (Person)-[Authorship]->(Document)...")
                query = """
                match 
                    $p isa person, has name $name;
                    $d isa document, has title $title, has external-ref $ref;
                    (author: $p, authored-document: $d) isa authorship;
                get $name, $title, $ref;
                """
                iterator = tx.query.get(query)
                
                count = 0
                for result in iterator:
                    count += 1
                    name = result.get("name").as_attribute().get_value()
                    title = result.get("title").as_attribute().get_value()
                    ref = result.get("ref").as_attribute().get_value()
                    print(f"  - Relation Found: Author '{name}' wrote '{title}' (ExtRef: {ref})")
                
                if count == 0:
                    print("  No relations found.")

    except Exception as e:
        print(f"TypeDB Error: {e}")
    finally:
        driver.close()

    print("\n=== END REPORT ===")

if __name__ == "__main__":
    verify_data()

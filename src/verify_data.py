import psycopg2
from typedb.driver import TypeDB, TransactionType, Credentials, DriverOptions
import traceback

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
        with TypeDB.driver("http://localhost:1729", Credentials("admin", "password"), DriverOptions(False, None)) as driver:
            with driver.transaction("riemann_db", TransactionType.READ) as tx:
                
                # Query: Find all people who authored documents
                print("Querying: Match (Person)-[Authorship]->(Document)...")
                # Syntax note: 'get' is optional/implicit in 3.0 match query if we access vars from map
                query = """
                match 
                    $p isa person, has full-name $name;
                    $d isa document, has title $title, has external-ref $ref;
                    (author: $p, authored-document: $d) isa authorship;
                """
                iterator = tx.query(query).resolve()
                
                count = 0
                for result in iterator:
                    count += 1
                    # Accessing variables from the ConceptMap
                    # Note: get("name") returns a Concept which we cast/inspect
                    name_attr = result.get("name")
                    title_attr = result.get("title")
                    ref_attr = result.get("ref")
                    
                    if name_attr and title_attr and ref_attr:
                        name = name_attr.as_attribute().get_value()
                        title = title_attr.as_attribute().get_value()
                        ref = ref_attr.as_attribute().get_value()
                        print(f"  - Relation Found: Author '{name}' wrote '{title}' (ExtRef: {ref})")
                    else:
                        print("  - Result found but attributes missing?")
                
                if count == 0:
                    print("  No relations found.")

    except Exception as e:
        print(f"TypeDB Error: {e}")
        traceback.print_exc()

    print("\n=== END REPORT ===")

if __name__ == "__main__":
    verify_data()

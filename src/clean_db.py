import psycopg2
from typedb.driver import TypeDB, SessionType, TransactionType

def clean_databases():
    print("🧹 Cleaning up databases (Full Reset)...")

    # 1. Clean PostgreSQL
    try:
        conn = psycopg2.connect(
            host="localhost", port="5432", database="airflow", user="airflow", password="airflow"
        )
        conn.autocommit = True
        cursor = conn.cursor()
        print("  -> Truncating PostgreSQL 'documents_sor' table...")
        cursor.execute("TRUNCATE TABLE documents_sor;")
        conn.close()
    except Exception as e:
        print(f"  [Warn] Postgres Clean Error: {e}")

    # 2. Clean TypeDB
    try:
        driver = TypeDB.core_driver("127.0.0.1:1729")
        # To strictly clean data without dropping schema, we match all entities and delete them.
        # But simpler for a reset is to drop and recreate the DB, or match all root things.
        # Let's try deleting the database and re-creating it using our manage_ontology script logic implicitly
        # or just delete all data instances.
        
        if driver.databases.contains("riemann_db"):
            print("  -> Deleting TypeDB 'riemann_db' to remove all data and schema...")
            driver.databases.get("riemann_db").delete()
            print("  -> Database deleted. (Schema needs to be re-loaded)")
        
        driver.close()
    except Exception as e:
        print(f"  [Warn] TypeDB Clean Error: {e}")

    print("✨ Databases Cleaned.")

if __name__ == "__main__":
    clean_databases()

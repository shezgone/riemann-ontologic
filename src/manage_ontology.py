from typedb.driver import TypeDB, SessionType, TransactionType
from typing import Text

def load_schema(db_name: str, server_addr: str = "127.0.0.1:1729"):
    # 1. Connect to TypeDB Server
    print(f"Connecting to TypeDB at {server_addr}...")
    with TypeDB.core_driver(server_addr) as driver:
        # 2. Create Database if strictly needed (some drivers auto-create, but good to be explicit)
        if driver.databases.contains(db_name):
            print(f"Database '{db_name}' already exists. Recreating...")
            driver.databases.get(db_name).delete()
        
        driver.databases.create(db_name)
        print(f"Created database '{db_name}'")

        # 3. Load Schema File
        with open("src/schema/base_ontology.tql", "r") as f:
            schema_tql = f.read()

        # 4. Define Schema in a Session
        print("Defining schema...")
        with driver.session(db_name, SessionType.SCHEMA) as session:
            with session.transaction(TransactionType.WRITE) as tx:
                tx.query.define(schema_tql)
                tx.commit()
        
        print("Schema defined successfully!")

def main():
    try:
        load_schema(db_name="riemann_db")
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure TypeDB is running on port 1729 (check docker-compose).")

if __name__ == "__main__":
    main()

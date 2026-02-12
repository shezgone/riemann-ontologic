from typedb.driver import TypeDB, TransactionType, Credentials, DriverOptions
from typing import Text
import traceback

def load_schema(db_name: str, server_addr: str = "http://localhost:1729"):
    # 1. Connect to TypeDB Server
    print(f"Connecting to TypeDB at {server_addr}...")
    with TypeDB.driver(server_addr, Credentials("admin", "password"), DriverOptions(False, None)) as driver:
        # 2. Create Database
        if driver.databases.contains(db_name):
            print(f"Database '{db_name}' already exists. Recreating...")
            driver.databases.get(db_name).delete()
        
        driver.databases.create(db_name)
        print(f"Created database '{db_name}'")

        # 3. Load Schema File
        with open("src/schema/base_ontology.tql", "r") as f:
            schema_tql = f.read()

        # Debugging with manual string
        # schema_tql = "define person sub entity;"

        # 4. Define Schema
        print("Defining schema...")
        with driver.transaction(db_name, TransactionType.SCHEMA) as tx:
            tx.query(schema_tql).resolve()
            tx.commit()
        
        print("Schema defined successfully!")

def main():
    try:
        load_schema(db_name="riemann_db")
    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()

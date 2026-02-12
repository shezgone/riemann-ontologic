from typing import Any, List
from llama_index.core import QueryBundle
from llama_index.core.retrievers import BaseRetriever
from llama_index.core.schema import NodeWithScore, TextNode
from typedb.driver import TypeDB, TransactionType, Credentials, DriverOptions
import psycopg2

class TypeDBHybridRetriever(BaseRetriever):
    """
    Custom Retriever for LlamaIndex that combines:
    1. TypeDB (Graph Search) - For structural/relational queries
    2. PostgreSQL (Vector Search) - For semantic similarity (TODO: Implement hybrid merging)
    
    This implementation currently focuses on the 'Graph' part:
    It takes a natural language query, converts it to TypeQL (via LLM - simplified here as direct logic for demo),
    executes it, and fetches the content from Postgres.
    """

    def __init__(self, typedb_host="http://localhost:1729", pg_host="localhost", db_name="riemann_db"):
        self.typedb_host = typedb_host
        self.pg_host = pg_host
        self.db_name = db_name
        super().__init__()

    def _retrieve(self, query_bundle: QueryBundle) -> List[NodeWithScore]:
        query_str = query_bundle.query_str
        nodes = []

        # --- Phase 1: NL to Graph Query (Simulation) ---
        # In a real app, we would use an LLM here to generate TypeQL.
        # For this prototype, we will implement a simple heuristic to detect intent.
        
        print(f"🕵️‍♀️ [Retriever] Analyzing Query: '{query_str}'")
        
        target_author = None
        if "Alice" in query_str:
            target_author = "Alice Engineer"
        
        ext_refs = []
        
        if target_author:
            print(f"   -> Detected Intent: Find documents by Author '{target_author}'")
            # Execute TypeQL
            try:
                with TypeDB.driver(self.typedb_host, Credentials("admin", "password"), DriverOptions(False, None)) as driver:
                    with driver.transaction(self.db_name, TransactionType.READ) as tx:
                        tql = f"""
                        match 
                            $p isa person, has full-name "{target_author}";
                            $d isa document, has external-ref $ref;
                            (author: $p, authored-document: $d) isa authorship;
                        get $ref;
                        """
                        print(f"   -> Executing TypeQL: {tql.strip().replace(chr(10), ' ')}")
                        iterator = tx.query.get(tql)
                        for result in iterator:
                            ref = result.get("ref").as_attribute().get_value()
                            ext_refs.append(ref)
            except Exception as e:
                print(f"Error in TypeDB: {e}")

        # --- Phase 2: Fetch Content from Postgres ---
        if ext_refs:
            print(f"   -> Found {len(ext_refs)} linked documents. Fetching content from Postgres...")
            try:
                pg_conn = psycopg2.connect(
                    host=self.pg_host, port="5432", database="airflow", user="airflow", password="airflow"
                )
                cursor = pg_conn.cursor()
                sql = "SELECT title, content FROM documents_sor WHERE external_ref_id = ANY(%s)"
                cursor.execute(sql, (ext_refs,))
                rows = cursor.fetchall()
                
                for row in rows:
                    title, content = row
                    # Create a TextNode for LlamaIndex to process
                    node = TextNode(text=f"Title: {title}\nContent: {content}")
                    # Score is 1.0 because it's an exact graph match
                    nodes.append(NodeWithScore(node=node, score=1.0))
                
                pg_conn.close()
            except Exception as e:
                print(f"Error in Postgres: {e}")
        else:
            print("   -> No graph matches found. (Falling back to pure vector search could happen here)")

        return nodes

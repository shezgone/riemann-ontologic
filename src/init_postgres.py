import psycopg2
import os

def init_postgres_schema():
    # Connection details from docker-compose/env
    conn = psycopg2.connect(
        host="localhost",
        port="5432",
        database="airflow", # Using 'airflow' DB as defined in docker-compose for simplicity initially, or should created a separate one? 
                            # The docker-compose created 'airflow' database. We can use a separate schema or table within it, 
                            # or strictly we should have created a separate DB 'riemann_data'. 
                            # For now, let's use the default DB but creating a dedicated table.
        user="airflow",
        password="airflow"
    )
    conn.autocommit = True
    cursor = conn.cursor()

    try:
        print("Initializing PostgreSQL Schema...")

        # 1. Enable pgvector extension
        print("Enabling pgvector extension...")
        cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")

        # 2. Create Documents Table (System of Record)
        # Stores the Heavy Text and Embeddings
        print("Creating table: documents_sor")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS documents_sor (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                external_ref_id VARCHAR(255) UNIQUE NOT NULL, -- Logical ID linking to TypeDB
                title TEXT,
                content TEXT,
                summary TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                metadata JSONB,
                embedding vector(1536) -- OpenAI embedding dimension (default)
            );
        """)

        # 3. Create Index for Vector Search
        # IVFFlat index for approximate nearest neighbor search
        print("Creating vector index...")
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS documents_embedding_idx 
            ON documents_sor 
            USING ivfflat (embedding vector_cosine_ops)
            WITH (lists = 100);
        """)
        
        print("PostgreSQL Schema initialized successfully!")

    except Exception as e:
        print(f"Error initializing Postgres: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    init_postgres_schema()

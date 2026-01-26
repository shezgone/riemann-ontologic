import psycopg2

def show_content_snippet():
    try:
        conn = psycopg2.connect(
            host="localhost", port="5432", database="airflow", user="airflow", password="airflow"
        )
        cursor = conn.cursor()
        
        print("🔍 Querying 'documents_sor' table (Limit 5)...")
        print("-" * 60)
        
        # Query to get ID, Title, and a substring of Content
        cursor.execute("""
            SELECT 
                external_ref_id, 
                title, 
                substring(content from 1 for 50) as content_preview 
            FROM documents_sor 
            LIMIT 5;
        """)
        
        rows = cursor.fetchall()
        
        print(f"{'External Ref ID':<38} | {'Title':<35} | {'Content Preview'}")
        print("-" * 100)
        
        for row in rows:
            ref_id, title, preview = row
            print(f"{ref_id:<38} | {title[:35]:<35} | {preview}...")

        conn.close()

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    show_content_snippet()

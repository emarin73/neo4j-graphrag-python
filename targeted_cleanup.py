
import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

LABELS_TO_DELETE = [
    "__KGBuilder__",
    "__Entity__", 
    "Chunk",
    "Section",
    "Ordinance",
    "Chapter",
    "Title",
    "Topic",
    "Zone",
    "Actor",
    "Obligation",
    "Prohibition",
    "Penalty",
    "Term",
    "Measurement"
]

def targeted_delete():
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    try:
        driver.verify_connectivity()
        print(f"Connecting to {NEO4J_URI}...")
        
        with driver.session() as session:
            for label in LABELS_TO_DELETE:
                print(f"Deleting nodes with label: :{label}...")
                
                # Delete in batches to avoid transaction timeouts on large datasets causes
                query = f"""
                CALL {{
                    MATCH (n:`{label}`)
                    WITH n LIMIT 10000
                    DETACH DELETE n
                    RETURN count(n) as deleted
                }}
                RETURN deleted
                """
                
                total_deleted = 0
                while True:
                    result = session.run(query)
                    deleted = result.single()["deleted"]
                    total_deleted += deleted
                    print(f"  - Batch deleted: {deleted}")
                    if deleted == 0:
                        break
                
                print(f"  Total deleted for :{label}: {total_deleted}")
                
            print("\nCleanup complete.")
            
            # Post-cleanup count
            count = session.run("MATCH (n) RETURN count(n) as c").single()["c"]
            print(f"Remaining nodes in database: {count}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        driver.close()

if __name__ == "__main__":
    targeted_delete()

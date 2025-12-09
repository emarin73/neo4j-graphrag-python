
import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

LABELS_TO_DELETE = [
    "Ordinance", "Section", "Zone", "Topic", "Jurisdiction", "SchemaVersion", "__Entity__", "__KGBuilder__"
]

def cleanup_invalid_build():
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    try:
        driver.verify_connectivity()
        print("Cleaning up invalid build data...")
        
        with driver.session() as session:
            for label in LABELS_TO_DELETE:
                # Delete nodes created in the last run (likely have ID=None or created recently)
                # Since we want a clean slate for the "Weston" build, and we know the previous run was broken:
                print(f"Deleting all {label} nodes...")
                session.run(f"MATCH (n:{label}) DETACH DELETE n")
            
            print("Cleanup complete. Ready for rebuild.")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        driver.close()

if __name__ == "__main__":
    cleanup_invalid_build()

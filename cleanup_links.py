
import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

def clear_links():
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    try:
        driver.verify_connectivity()
        with driver.session() as session:
            print("Cleaning old GOVERNED_BY links...")
            
            # Delete all GOVERNED_BY relationships
            query = """
            MATCH ()-[r:GOVERNED_BY]->()
            DELETE r
            RETURN count(r) as deleted
            """
            deleted = session.run(query).single()["deleted"]
            print(f"Deleted {deleted} old links.")
            
            print("Now you should re-run the linker.")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        driver.close()

if __name__ == "__main__":
    clear_links()

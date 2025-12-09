
import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

def check_chunks():
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    try:
        driver.verify_connectivity()
        with driver.session() as session:
            print("Checking Chunks...")
            count = session.run("MATCH (c:Chunk) RETURN count(c) as cnt").single()["cnt"]
            print(f"Total Chunks: {count}")
            
            if count > 0:
                print("\nSample Chunk Text (Limit 3):")
                res = session.run("MATCH (c:Chunk) RETURN c.text LIMIT 3")
                for r in res:
                    print(f"--- Chunk ---\n{r['c.text'][:200]}...\n")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        driver.close()

if __name__ == "__main__":
    check_chunks()

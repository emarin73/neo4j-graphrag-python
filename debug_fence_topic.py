
import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

def debug_fence_topic():
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    try:
        driver.verify_connectivity()
        with driver.session() as session:
            # Check what connects to "Fences and Walls"
            print("Relationships into 'Fences and Walls':")
            query = """
            MATCH (t:Topic {name: 'Fences and Walls'})<-[r]-(n)
            RETURN type(r), labels(n), properties(n)
            LIMIT 10
            """
            result = list(session.run(query))
            for row in result:
                props = row[2]
                name = props.get('name') or props.get('code') or props.get('title')
                print(f"  [{row[1][0]}] '{name}' -[{row[0]}]-> Topic")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        driver.close()

if __name__ == "__main__":
    debug_fence_topic()

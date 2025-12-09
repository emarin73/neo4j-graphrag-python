
import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

def verify():
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    try:
        driver.verify_connectivity()
        print("Connected to Neo4j.")
        
        with driver.session() as session:
            # Query 1: Count nodes
            result = session.run("MATCH (n) RETURN count(n) as count")
            count = result.single()["count"]
            print(f"Total Nodes: {count}")
            
            # Query 2: Node types
            result = session.run("MATCH (n) RETURN labels(n) as labels, count(*) as count ORDER BY count DESC")
            print("\nNode Types:")
            for record in result:
                print(f"  {record['labels']}: {record['count']}")
                
            # Query 3: Relationship types
            result = session.run("MATCH ()-[r]->() RETURN type(r) as type, count(*) as count ORDER BY count DESC")
            print("\nRelationship Types:")
            for record in result:
                print(f"  {record['type']}: {record['count']}")
                
    except Exception as e:
        print(f"Error: {e}")
    finally:
        driver.close()

if __name__ == "__main__":
    verify()

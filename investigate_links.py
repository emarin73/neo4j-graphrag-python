
import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

def investigate_links():
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    try:
        driver.verify_connectivity()
        with driver.session() as session:
            # Check relationships for Parcel
            print("Relationships on Parcel nodes:")
            result = session.run("MATCH (p:Parcel)-[r]->(n) RETURN type(r) as rel_type, labels(n) as target_labels, count(*) as count LIMIT 20")
            for record in result:
                print(f"  Parcel -[{record['rel_type']}]-> {record['target_labels']}: {record['count']}")
                
            # Check properties of Zoning nodes (if any exist)
            print("\nZoning Node Properties:")
            result = session.run("MATCH (z:Zoning) RETURN properties(z) as props LIMIT 1")
            record = result.single()
            if record:
                print(f"  {record['props']}")
            else:
                print("  No Zoning nodes found.")
                
            # Check properties of Zone nodes (from previous/partial builds?)
            # Or LandUse nodes which might be relevant
            print("\nLandUse Node Properties:")
            result = session.run("MATCH (l:LandUse) RETURN properties(l) as props LIMIT 1")
            record = result.single()
            if record:
                print(f"  {record['props']}")
                
    except Exception as e:
        print(f"Error: {e}")
    finally:
        driver.close()

if __name__ == "__main__":
    investigate_links()


import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

def inspect_parcel():
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    try:
        driver.verify_connectivity()
        with driver.session() as session:
            # Get one parcel and its keys
            result = session.run("MATCH (p:Parcel) RETURN properties(p) as props LIMIT 1")
            record = result.single()
            if record:
                print("Parcel Properties:")
                for key, value in record["props"].items():
                    print(f"  {key}: {value}")
            else:
                print("No Parcel nodes found.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        driver.close()

if __name__ == "__main__":
    inspect_parcel()

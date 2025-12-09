
import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

def inspect_nodes():
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    try:
        driver.verify_connectivity()
        with driver.session() as session:
            # Inspect Topic
            print("1. Topic Node Properties:")
            result = session.run("MATCH (t:Topic) RETURN keys(t), properties(t) LIMIT 1")
            for r in result:
                print(f"  Keys: {r[0]}")
                print(f"  Props: {r[1]}")

            # Inspect Section
            print("\n2. Section Node Properties:")
            result = session.run("MATCH (s:Section) RETURN keys(s), properties(s) LIMIT 1")
            for r in result:
                print(f"  Keys: {r[0]}")
                print(f"  Props: {r[1]}")

            # Inspect Ordinance
            print("\n3. Ordinance Node Properties:")
            result = session.run("MATCH (o:Ordinance) RETURN keys(o), properties(o) LIMIT 1")
            for r in result:
                print(f"  Keys: {r[0]}")
                print(f"  Props: {r[1]}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        driver.close()

if __name__ == "__main__":
    inspect_nodes()

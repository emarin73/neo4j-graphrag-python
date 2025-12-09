
import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

def debug_topics():
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    try:
        driver.verify_connectivity()
        with driver.session() as session:
            # 1. List ALL Topics (limit 50)
            print("1. Topics Found in Graph:")
            result = session.run("MATCH (t:Topic) RETURN t.id, t.description LIMIT 50")
            for r in result:
                print(f"  Topic: {r[0]}")

            # 2. Search Sections for 'fence' text
            print("\n2. Sections containing 'fence':")
            # Usually text is in 'text' property
            result = session.run("MATCH (s:Section) WHERE toLower(s.text) CONTAINS 'fence' RETURN s.id, substring(s.text, 0, 50) as snippet LIMIT 5")
            sections = list(result)
            for r in sections:
                print(f"  Section: {r[0]} - '{r[1]}...'")

            if not sections:
                print("  No Sections found with 'fence' in text.")
                
            # 3. Check Section to Topic relationships
            if sections:
                print("\n3. Relationships for found sections:")
                for r in sections:
                    sid = r[0]
                    rels = session.run("MATCH (s:Section {id: $sid})-[r]->(n) RETURN type(r), labels(n), n.id", sid=sid)
                    for rel in rels:
                        print(f"  Section {sid} -[{rel[0]}]-> {rel[1]} ({rel[2]})")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        driver.close()

if __name__ == "__main__":
    debug_topics()

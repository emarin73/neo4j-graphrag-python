
import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

def verify_fence_rules():
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    try:
        driver.verify_connectivity()
        print("Verifying Fence Rules for Parcels...")
        
        with driver.session() as session:
            # Query for ANY parcel with fence rules (to verify the path exists)
            # We look for Topic containing "Fence" or "Fencing"
            query = """
            MATCH (p:Parcel)-[:HAS_ZONING]->(z:Zoning)-[:GOVERNED_BY]->(o:Zone)<-[:APPLIES_TO]-(s:Section)-[:HAS_TOPIC]->(t:Topic)
            WHERE toLower(t.id) CONTAINS 'fence' OR toLower(t.description) CONTAINS 'fence'
            RETURN p.parcel_id as parcel, o.id as zone, t.id as topic, s.id as section
            LIMIT 5
            """
            result = session.run(query)
            
            records = list(result)
            if records:
                print(f"Success! Found {len(records)} examples of linked fence rules.")
                for r in records:
                    print(f"  Parcel: {r['parcel']} (Zone: {r['zone']}) -> Topic: {r['topic']}, Section: {r['section']}")
            else:
                print("No Fence rules found linked to parcels yet.")
                print("Troubleshooting steps:")
                print("1. Did linking script run?")
                print("2. Are there Topics with 'Fence' in the name?")
                
                # Check for Fence topics
                check_topics = session.run("MATCH (t:Topic) WHERE toLower(t.id) CONTAINS 'fence' RETURN t.id LIMIT 5")
                topics = list(check_topics)
                if topics:
                    print(f"  Found Fence Topics: {[t['t.id'] for t in topics]}")
                else:
                    print("  No 'Fence' Topics found in graph.")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        driver.close()

if __name__ == "__main__":
    verify_fence_rules()

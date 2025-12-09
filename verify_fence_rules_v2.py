
import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

def verify_fence_rules_v2():
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    try:
        driver.verify_connectivity()
        print("Verifying Fence Rules (Schema Corrected)...")
        
        with driver.session() as session:
            # 1. Search for Fence Topics using 'name'
            print("1. Searching for Fence Topics:")
            query = "MATCH (t:Topic) WHERE toLower(t.name) CONTAINS 'fence' OR toLower(t.name) CONTAINS 'fencing' RETURN t.name, t.description LIMIT 5"
            topics = list(session.run(query))
            for r in topics:
                print(f"  Found Topic: {r['t.name']}")
            
            if not topics:
                print("  No 'Fence' topics found in Topic.name.")

            # 2. Verify Path from Parcel -> Fence Rule
            # Path: Parcel -> Zoning -> Zone <- Section -> Topic
            print("\n2. Checking Full Path:")
            query = """
            MATCH (p:Parcel)-[:HAS_ZONING]->(z:Zoning)-[:GOVERNED_BY]->(o:Zone)<-[:APPLIES_TO]-(s:Section)-[:HAS_TOPIC]->(t:Topic)
            WHERE toLower(t.name) CONTAINS 'fence' OR toLower(t.name) CONTAINS 'fencing'
            RETURN p.parcel_id, o.name, t.name, s.code, s.title
            LIMIT 5
            """
            result = list(session.run(query))
            if result:
                print(f"  SUCCESS! Found {len(result)} paths.")
                for r in result:
                    print(f"  Parcel {r['p.parcel_id']} (Zone {r['o.name']}) -> Code {r['s.code']} '{r['s.title']}' (Topic: {r['t.name']})")
                
                # Also try to get text from Chunk if Section has no text
                print("\n  Sample Rule Text (from Chunk):")
                chunk_query = """
                MATCH (s:Section)-[:MENTIONS|HAS_ENTITY]-(c:Chunk) 
                WHERE s.code = $code
                RETURN c.text LIMIT 1
                """
                # Note: Relationship might be implicit or reverse. Usually Chunk -> Section (HAS_ENTITY)
                # But let's try.
                chunk_res = session.run(chunk_query, code=result[0]['s.code']).single()
                if chunk_res:
                    print(f"  Chunk Text: {chunk_res['c.text'][:100]}...")
            else:
                print("  No full path found.")
                
            # 3. Check if Sections have "Fence" in title
            print("\n3. Checking Sections with 'Fence' in title:")
            query = "MATCH (s:Section) WHERE toLower(s.title) CONTAINS 'fence' RETURN s.code, s.title LIMIT 5"
            sections = list(session.run(query))
            for r in sections:
                print(f"  Section: {r['s.code']} - {r['s.title']}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        driver.close()

if __name__ == "__main__":
    verify_fence_rules_v2()

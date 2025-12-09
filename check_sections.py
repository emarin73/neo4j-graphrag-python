
import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

def check_sections():
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    try:
        driver.verify_connectivity()
        with driver.session() as session:
            print("Searching Sections for 'R-1', 'C-1' or 'Residential'...")
            
            query = """
            MATCH (s:Section)
            WHERE toLower(s.name) CONTAINS 'r-1' 
               OR toLower(s.name) CONTAINS 'c-1'
               OR toLower(s.name) CONTAINS 'residential'
               OR toLower(s.title) CONTAINS 'residential'
            RETURN s.name, s.title LIMIT 20
            """
            res = list(session.run(query))
            for r in res:
                print(f"Found Section: Code='{r['s.name']}' Title='{r['s.title']}'")
            
            if not res:
                print("No relevant Sections found.")
                
            # Count total sections
            count = session.run("MATCH (s:Section) RETURN count(s) as c").single()["c"]
            print(f"Total Sections in Graph: {count}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        driver.close()

if __name__ == "__main__":
    check_sections()

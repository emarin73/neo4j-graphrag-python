
import time
import os
import sys
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

def wait_and_link():
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    print("Waiting for Weston Graph Build to complete...")
    print("(Checking for 'Jurisdiction' node 'Weston'...)")
    
    start_time = time.time()
    built = False
    
    try:
        driver.verify_connectivity()
        with driver.session() as session:
            while time.time() - start_time < 1200: # Wait up to 20 mins
                # Check for Jurisdiction node (created at end of build)
                result = session.run("MATCH (j:Jurisdiction {name: 'Weston'}) RETURN j").single()
                
                if result:
                    print("\nBuild Complete! Jurisdiction 'Weston' found.")
                    built = True
                    break
                
                # Feedback
                sys.stdout.write(".")
                sys.stdout.flush()
                time.sleep(10)
            
            if not built:
                print("\nTimeout waiting for build. Please check logs.")
                return

            # Now Link
            print("\nLinking Parcels...")
            prefix = "Weston::"
            link_query = """
            MATCH (z:Zoning)
            WHERE z.zone_class IS NOT NULL
            WITH z, $prefix + z.zone_class as target_id
            MATCH (o:Zone)
            WHERE o.id = target_id
            MERGE (z)-[r:GOVERNED_BY]->(o)
            RETURN count(r) as links_created
            """
            links = session.run(link_query, prefix=prefix).single()["links_created"]
            print(f"Links created: {links}")
            
            # Now Test
            print("\nRunning Test Verification...")
            # Simple test query
            test_query = """
            MATCH (s:Section)-[:HAS_TOPIC]->(t:Topic)
            WHERE t.name CONTAINS 'Fence' AND s.id STARTS WITH 'Weston::'
            RETURN count(s) as rules
            """
            rules = session.run(test_query).single()["rules"]
            print(f"Fence Rules found in Weston: {rules}")
            
            if rules > 0 and links > 0:
                print("\nSUCCESS! Your KG is ready and verified.")
            else:
                print("\nWarning: Verification incomplete.")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        driver.close()

if __name__ == "__main__":
    wait_and_link()

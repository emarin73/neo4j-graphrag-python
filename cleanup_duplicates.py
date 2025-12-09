
import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

def cleanup_duplicates():
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    try:
        driver.verify_connectivity()
        with driver.session() as session:
            print("Cleaning up junk 'Weston::R-2' node...")
            
            # Find the junk node
            query_junk = """
            MATCH (z:Zone {id: 'Weston::R-2'})
            RETURN z.name, count(z) as c
            """
            res = session.run(query_junk).single()
            if res:
                print(f"Junk node found: '{res['z.name']}'")
                
                # We want to delete this node but ensure everything links to 'Weston::Single-Family Residence'
                # Actually, if we just delete it and re-run linker, the linker will find the correct node via 'code' match.
                
                query_delete = """
                MATCH (z:Zone {id: 'Weston::R-2'})
                DETACH DELETE z
                RETURN count(z) as deleted
                """
                deleted = session.run(query_delete).single()["deleted"]
                print(f"Deleted {deleted} junk node(s).")
            else:
                print("Junk node 'Weston::R-2' not found.")

            print("Cleaning links again just to be safe...")
            session.run("MATCH ()-[r:GOVERNED_BY]->() DELETE r")
            print("Links cleared.")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        driver.close()

if __name__ == "__main__":
    cleanup_duplicates()


import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

def fix_r2():
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    try:
        driver.verify_connectivity()
        with driver.session() as session:
            print("Correcting R-2 Mapping...")
            
            # 1. Remove R-2 from Duplex
            query_remove = """
            MATCH (z:Zone)
            WHERE z.id = 'Weston::Duplex Residential' AND z.code = 'R-2'
            SET z.code = 'R-2-Duplex' // renaming to preserve just in case, or set null
            RETURN count(z) as removed
            """
            removed = session.run(query_remove).single()["removed"]
            print(f"Removed R-2 from {removed} Duplex nodes.")
            
            # 2. Assign R-2 to Single Family
            # We found 'Weston::Single-Family Residence'
            query_assign = """
            MATCH (z:Zone)
            WHERE z.id = 'Weston::Single-Family Residence'
            SET z.code = 'R-2'
            RETURN count(z) as updated
            """
            updated = session.run(query_assign).single()["updated"]
            print(f"Assigned R-2 to {updated} Single Family nodes.")
            
            # 3. Rename ID for consistency (Optional but good)
            # We keep ID stable usually, but if the ID was 'Weston::Duplex_R2' it would be confusing.
            # Current ID is 'Weston::Single-Family Residence', which is fine.

            print("Correction complete.")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        driver.close()

if __name__ == "__main__":
    fix_r2()

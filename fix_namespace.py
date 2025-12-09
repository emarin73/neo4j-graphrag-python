
import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

def enforce_namespace(jurisdiction):
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    try:
        driver.verify_connectivity()
        prefix = f"{jurisdiction}::"
        print(f"Enforcing namespace '{prefix}' (Handling NULLs)...")
        
        with driver.session() as session:
            # 1. Update Zones (Use 'name' if ID is null)
            # COALESCE uses id if present (but not starting with prefix), else uses name, else "Unknown"
            
            # Case A: ID is NULL -> Set to prefix + name
            query_null = """
            MATCH (z:Zone)
            WHERE z.id IS NULL
            SET z.id = $prefix + coalesce(z.name, 'UnknownZone')
            RETURN count(z) as fixed
            """
            fixed = session.run(query_null, prefix=prefix).single()["fixed"]
            print(f"  Fixed {fixed} Zone nodes with NULL IDs.")
            
            # Case B: ID exists but missing prefix
            query_prefix = """
            MATCH (z:Zone)
            WHERE z.id IS NOT NULL AND NOT z.id STARTS WITH $prefix
            SET z.id = $prefix + z.id
            RETURN count(z) as updated
            """
            updated = session.run(query_prefix, prefix=prefix).single()["updated"]
            print(f"  Updated {updated} Zone nodes (missing prefix).")

            # 2. Update Sections (Use 'code' or 'name')
            query_sec = """
            MATCH (s:Section)
            WHERE s.id IS NULL
            SET s.id = $prefix + coalesce(s.code, s.name, 'UnknownSection')
            RETURN count(s) as fixed
            """
            fixed_s = session.run(query_sec, prefix=prefix).single()["fixed"]
            print(f"  Fixed {fixed_s} Section nodes with NULL IDs.")
            
            query_sec_up = """
            MATCH (s:Section)
            WHERE s.id IS NOT NULL AND NOT s.id STARTS WITH $prefix
            SET s.id = $prefix + s.id
            RETURN count(s) as updated
            """
            updated_s = session.run(query_sec_up, prefix=prefix).single()["updated"]
            print(f"  Updated {updated_s} Section nodes.")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        driver.close()

if __name__ == "__main__":
    enforce_namespace("Weston")

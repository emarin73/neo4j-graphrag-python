
import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

OFFICIAL_ZONES = [
    {"code": "R-1", "name": "Single-Family Residential Medium"},
    {"code": "R-2", "name": "Single-Family Residential Moderate"},
    {"code": "R-3", "name": "Single-Family Residential Moderate/Low"},
    {"code": "R-4", "name": "Single-Family Residential Low"},
    {"code": "RE", "name": "Estate Residential"},
    {"code": "RZ", "name": "Single-Family Residential zero Lot line"},
    {"code": "MF-1", "name": "Villa and Townhouse and Duplex"},
    {"code": "MF-2", "name": "Low Rise Multi Family"},
    {"code": "MF-3", "name": "Mid Rise Multi Family"},
    {"code": "MF-4", "name": "High Rise Multi Family"},
    {"code": "O-1", "name": "Office"},
    {"code": "C-1", "name": "Commercial"},
    {"code": "I-1", "name": "Industrial"},
    {"code": "GC", "name": "Golf Course"},
    {"code": "MU", "name": "Municipal Use"},
    {"code": "PECD", "name": "Planned Employment Center District"},
    {"code": "PDD", "name": "Planned Development District"},
    {"code": "AE", "name": "Agricultural Estate"},
    {"code": "CF", "name": "Community Facilities"},
    {"code": "CV", "name": "Conservation"}
]

JURISDICTION = "Weston"

def seed_zones():
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    try:
        driver.verify_connectivity()
        with driver.session() as session:
            print("Seeding Official Zoning Districts...")
            
            # 1. Cleanup Old/Ambiguous Nodes
            # specifically 'Single-Family Residence' which was capturing R-2 links
            print("Removing obsolete/ambiguous nodes...")
            session.run("MATCH (z:Zone {id: 'Weston::Single-Family Residence'}) DETACH DELETE z")
            
            for zone in OFFICIAL_ZONES:
                print(f"Processing {zone['code']} - {zone['name']}")
                
                query = """
                MERGE (z:Zone {id: $id})
                SET z.name = $name, z.code = $code, z.jurisdiction = $jurisdiction
                RETURN z
                """
                # Using Weston::{Name} as ID
                node_id = f"{JURISDICTION}::{zone['name']}"
                
                session.run(query, id=node_id, name=zone['name'], code=zone['code'], jurisdiction=JURISDICTION)
                
            print("Official Zones created/updated.")
            
            # Cleanup step:
            # If we have multiple zones with code='R2', consolidate them?
            # For now, let's just trust the Linker to find the one we just created (since we know its exact code).

    except Exception as e:
        print(f"Error: {e}")
    finally:
        driver.close()

if __name__ == "__main__":
    seed_zones()

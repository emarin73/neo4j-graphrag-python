
import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

def link_zones():
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    try:
        driver.verify_connectivity()
        print("Linking Parcels/Zoning to Ordinance Zones...")
        
        with driver.session() as session:
            # 1. Check what the new Zone nodes look like
            print("Inspection of new Zone nodes:")
            result = session.run("MATCH (z:Zone) RETURN z.id, z.name, labels(z) LIMIT 5")
            for record in result:
                print(f"  Zone: id={record.get('z.id')}, name={record.get('z.name')}")
                
            # 2. Perform the Link
            # We assume Zoning.zone_class (e.g., 'R-1') matches Zone.id (e.g., 'R-1')
            print("\nExecuting Link Query...")
            query = """
            MATCH (z:Zoning)
            WHERE z.zone_class IS NOT NULL
            MATCH (o:Zone)
            WHERE o.id = z.zone_class OR o.name = z.zone_class
            MERGE (z)-[r:GOVERNED_BY]->(o)
            RETURN count(r) as links_created
            """
            result = session.run(query)
            count = result.single()["links_created"]
            print(f"Links created: {count}")
            
            # 3. Verify
            if count > 0:
                print("\nVerification: Path from Parcel to Topic")
                verify_query = """
                MATCH (p:Parcel)-[:HAS_ZONING]->(z:Zoning)-[:GOVERNED_BY]->(o:Zone)<-[:APPLIES_TO]-(s:Section)-[:HAS_TOPIC]->(t:Topic)
                RETURN p.parcel_id, o.id, t.id LIMIT 1
                """
                verify = session.run(verify_query).single()
                if verify:
                    print(f"  Success! Path found: Parcel {verify[0]} -> Zone {verify[1]} -> Topic {verify[2]}")
                else:
                    print("  Links created, but no full path to Topic found yet.")
            else:
                print("No links created. Check if Zone IDs match Zoning classes.")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        driver.close()

if __name__ == "__main__":
    link_zones()

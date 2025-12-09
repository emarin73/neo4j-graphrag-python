
import os
import sys
from neo4j import GraphDatabase
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

def export_fence_rules(parcel_id, output_file=None):
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    
    if not output_file:
        output_file = f"fence_rules_{parcel_id}.txt"
    
    try:
        driver.verify_connectivity()
        with driver.session() as session:
            # Get parcel info
            query_info = """
            MATCH (p:Parcel {parcel_id: $pid})
            OPTIONAL MATCH (p)-[:HAS_ADDRESS]->(a:Address)
            OPTIONAL MATCH (p)-[:HAS_ZONING]->(z:Zoning)
            OPTIONAL MATCH (z)-[:GOVERNED_BY]->(oz:Zone)
            OPTIONAL MATCH (p)-[:IN_HOA]->(hoa:HOA)
            RETURN p, a, z, oz, hoa LIMIT 1
            """
            results = list(session.run(query_info, pid=parcel_id))
            
            if not results:
                print(f"Parcel {parcel_id} not found.")
                return
            
            result = results[0]
            parcel = result['p']
            addr = result['a']
            zoning = result['z']
            ord_zone = result['oz']
            hoa = result['hoa']
            
            # Get all fence rules
            query_rules = """
            MATCH (s:Section)
            WHERE s.id STARTS WITH 'Weston::' 
              AND toLower(s.text) CONTAINS 'fence'
            RETURN s.name, s.text
            ORDER BY s.name
            """
            all_rules = list(session.run(query_rules))
            
            # Write to file
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write("="*80 + "\n")
                f.write("FENCE REGULATIONS REPORT\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("="*80 + "\n\n")
                
                f.write("PROPERTY INFORMATION\n")
                f.write("-"*80 + "\n")
                f.write(f"Parcel ID: {parcel_id}\n")
                if addr:
                    f.write(f"Address: {addr.get('street', 'N/A')}, {addr.get('city', 'N/A')}\n")
                
                f.write(f"Property Type: {parcel.get('property_type', 'N/A')}\n")
                f.write(f"Lot Type: {parcel.get('lot_type', 'N/A')}\n")
                f.write(f"Corner Lot: {'Yes' if parcel.get('is_corner_lot') else 'No'}\n")
                f.write(f"Pool: {'Yes' if parcel.get('has_pool') else 'No'}\n")
                f.write(f"Fence Linear Feet: {parcel.get('fence_linear_feet', 'N/A')}\n")
                
                if zoning:
                    code = zoning.get('zone_class') or zoning.get('code') or zoning.get('zoneclass')
                    f.write(f"Zoning Code: {code}\n")
                
                if ord_zone:
                    f.write(f"Zoning District: {ord_zone.get('name')}\n")
                
                if hoa:
                    f.write(f"HOA: {hoa.get('name', 'N/A')}\n")
                
                f.write(f"Fence Permit Required: Yes\n")
                f.write("\n" + "="*80 + "\n\n")
                
                f.write(f"APPLICABLE FENCE REGULATIONS ({len(all_rules)} sections)\n")
                f.write("="*80 + "\n\n")
                
                for i, r in enumerate(all_rules, 1):
                    f.write(f"\n{'='*80}\n")
                    f.write(f"SECTION {r['s.name']} ({i} of {len(all_rules)})\n")
                    f.write(f"{'='*80}\n\n")
                    f.write(f"{r['s.text']}\n")
                
                f.write("\n" + "="*80 + "\n")
                f.write("END OF REPORT\n")
                f.write("="*80 + "\n")
            
            print(f"\n✓ Fence rules exported to: {output_file}")
            print(f"  Total sections: {len(all_rules)}")
            print(f"\nOpen the file to read all regulations.")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        driver.close()

if __name__ == "__main__":
    pid_arg = sys.argv[1] if len(sys.argv) > 1 else "503911073240"
    output_arg = sys.argv[2] if len(sys.argv) > 2 else None
    export_fence_rules(pid_arg, output_arg)

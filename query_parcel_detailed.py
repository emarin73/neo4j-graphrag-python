
import os
import sys
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

def query_parcel_detailed(parcel_id):
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    try:
        driver.verify_connectivity()
        with driver.session() as session:
            print(f"Querying Detailed Fence Rules for Parcel ID: {parcel_id}...")
            
            # 1. Get Parcel Info & Linked Zone
            query_info = """
            MATCH (p:Parcel {parcel_id: $pid})
            OPTIONAL MATCH (p)-[:HAS_ADDRESS]->(a:Address)
            OPTIONAL MATCH (p)-[:HAS_ZONING]->(z:Zoning)
            OPTIONAL MATCH (p)-[:HAS_LAND_USE]->(lu:LandUse)
            OPTIONAL MATCH (z)-[:GOVERNED_BY]->(oz:Zone)
            OPTIONAL MATCH (p)-[:BELONGS_TO]->(subdiv:Subdivision)-[:MANAGED_BY]->(hoa:HOA)
            RETURN p, a, z, lu, oz, hoa, subdiv LIMIT 1
            """
            results = list(session.run(query_info, pid=parcel_id))
            
            if not results:
                print(f"Parcel {parcel_id} not found.")
                return

            result = results[0]
            parcel = result['p']
            addr = result['a']
            zoning = result['z']
            land_use = result['lu']
            ord_zone = result['oz']
            hoa = result['hoa']
            subdiv = result['subdiv']
            
            print("\n" + "="*80)
            print("PROPERTY DETAILS")
            print("="*80)
            
            if addr:
                print(f"Address: {addr.get('street', 'N/A')}, {addr.get('city', 'N/A')}")
            
            # Property characteristics
            prop_type = parcel.get('property_type', 'N/A')
            is_corner = parcel.get('is_corner_lot', False)
            has_pool = parcel.get('has_pool', False)
            lot_type = parcel.get('lot_type', 'N/A')
            fence_linear_feet = parcel.get('fence_linear_feet', 'N/A')
            
            print(f"Property Type: {prop_type}")
            print(f"Lot Type: {lot_type}")
            print(f"Corner Lot: {'Yes' if is_corner else 'No'}")
            print(f"Pool: {'Yes' if has_pool else 'No'}")
            print(f"Fence Linear Feet: {fence_linear_feet}")
            
            if zoning:
                code = zoning.get('zone_class') or zoning.get('code') or zoning.get('zoneclass')
                print(f"Zoning Code: {code}")
            
            if land_use:
                lu_code = land_use.get('land_use_code') or land_use.get('code') or land_use.get('landuse')
                lu_desc = land_use.get('description') or land_use.get('land_use') or 'N/A'
                print(f"Land Use: {lu_desc} ({lu_code})")
            
            if ord_zone:
                print(f"Zoning District: {ord_zone.get('name')} (ID: {ord_zone.get('id')})")
            
            if subdiv:
                print(f"Subdivision: {subdiv.get('subdivision_id', 'N/A')}")
            
            if hoa:
                print(f"HOA: {hoa.get('name', 'N/A')} (ID: {hoa.get('hoa_id', 'N/A')})")
            
            print("\n" + "="*80)
            print("APPLICABLE FENCE REGULATIONS")
            print("="*80)
            
            # 2. Get all fence rules and filter/highlight based on property attributes
            query_rules = """
            MATCH (s:Section)
            WHERE s.id STARTS WITH 'Weston::' 
              AND toLower(s.text) CONTAINS 'fence'
            RETURN s.name, s.text
            ORDER BY s.name
            """
            all_rules = list(session.run(query_rules))
            
            if not all_rules:
                print("No fence regulations found in the knowledge graph.")
                return
            
            # Filter rules based on property characteristics
            relevant_rules = []
            general_rules = []
            
            for r in all_rules:
                text_lower = r['s.text'].lower()
                is_relevant = False
                relevance_reasons = []
                
                # Check for corner lot specific rules
                if is_corner and 'corner' in text_lower:
                    is_relevant = True
                    relevance_reasons.append("Corner lot rule")
                
                # Check for pool-related rules
                if has_pool and 'pool' in text_lower:
                    is_relevant = True
                    relevance_reasons.append("Pool-related rule")
                
                # Check for residential/single-family specific
                if 'residential' in text_lower or 'single' in text_lower or 'family' in text_lower:
                    is_relevant = True
                    relevance_reasons.append("Residential property rule")
                
                # Check for HOA mentions
                if hoa and ('hoa' in text_lower or 'homeowner' in text_lower or 'association' in text_lower):
                    is_relevant = True
                    relevance_reasons.append("HOA-related rule")
                
                # Check for permit requirements
                if 'permit' in text_lower:
                    is_relevant = True
                    relevance_reasons.append("Permit requirement")
                
                if is_relevant:
                    relevant_rules.append((r, relevance_reasons))
                else:
                    general_rules.append(r)
            
            # Display relevant rules first
            if relevant_rules:
                print(f"\n*** HIGHLY RELEVANT RULES ({len(relevant_rules)} sections) ***")
                print("These rules specifically apply to your property characteristics:\n")
                
                for r, reasons in relevant_rules:
                    print("="*80)
                    print(f"Section {r['s.name']}")
                    print(f"Relevant because: {', '.join(reasons)}")
                    print("="*80)
                    print(f"{r['s.text']}\n")
            
            # Display general rules
            if general_rules:
                print(f"\n*** GENERAL FENCE REGULATIONS ({len(general_rules)} sections) ***")
                print("These general rules may also apply:\n")
                
                for r in general_rules:
                    print("="*80)
                    print(f"Section {r['s.name']}")
                    print("="*80)
                    print(f"{r['s.text']}\n")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        driver.close()

if __name__ == "__main__":
    pid_arg = sys.argv[1] if len(sys.argv) > 1 else "503911073240"
    query_parcel_detailed(pid_arg)

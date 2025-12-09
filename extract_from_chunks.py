
import os
import asyncio
import json
from neo4j import GraphDatabase
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

JURISDICTION = "Weston"
PREFIX = f"{JURISDICTION}::"

client = AsyncOpenAI(api_key=OPENAI_API_KEY)

async def process_chunk(session, chunk_id, text):
    prompt = f"""
    You are an expert legal knowledge graph builder.
    Extract the following entities from the Ordinance Document text provided below.
    
    Entities to Extract:
    1. Section: The legal section (e.g., "Section 12.04", "§ 5.1"). 
       - id: Must start with "{PREFIX}" + the section code. (e.g., "{PREFIX}Section 12.04")
       - title: The title of the section.
       - text: The full text of the section rules.
    
    2. Zone: A zoning district mentioned or defined (e.g., "R-1", "Commercial District").
       - id: Must start with "{PREFIX}" + the zone code/name. (e.g., "{PREFIX}R-1")
       - name: The full name (e.g., "Single Family Residential").
       - code: The short code (e.g., "R-1").
       - type: "Residential", "Commercial", "Industrial", or "Other".

    Relationships:
    - Section APPLIES_TO Zone
    - Section DEFINES Zone
    
    Return JSON format:
    {{
        "sections": [ {{ "id": "...", "code": "...", "title": "...", "text": "..." }} ],
        "zones": [ {{ "id": "...", "name": "...", "code": "...", "type": "..." }} ],
        "relationships": [ {{ "from_section_id": "...", "to_zone_id": "...", "type": "APPLIES_TO" }} ]
    }}
    
    Text:
    {text[:4000]}
    """
    
    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        data = json.loads(response.choices[0].message.content)
        return data
    except Exception as e:
        print(f"LLM Error: {e}")
        return None

async def main():
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    try:
        driver.verify_connectivity()
        with driver.session() as session:
            # Get Chunks that don't have relationships yet (to avoid re-doing)
            # Actually, just get all chunks for now, verify cost isn't huge. 574 chunks * 0.01$ = $5. Fine.
            result = session.run("MATCH (c:Chunk) RETURN c.id, c.text")
            chunks = list(result)
            print(f"Processing {len(chunks)} chunks...")
            
            # Create Jurisdiction Node
            session.run(f"MERGE (j:Jurisdiction {{name: '{JURISDICTION}', id: '{JURISDICTION}'}})")
            
            batch_size = 10
            for i in range(0, len(chunks), batch_size):
                batch = chunks[i:i+batch_size]
                tasks = [process_chunk(session, r['c.id'], r['c.text']) for r in batch]
                results = await asyncio.gather(*tasks)
                
                for res in results:
                    if not res: continue
                    
                    # Write to Neo4j
                    # 1. Sections
                    for sec in res.get("sections", []):
                        query = """
                        MERGE (s:Section {id: $id})
                        SET s.code = $code, s.title = $title, s.text = $text, s.name = $code
                        WITH s
                        MATCH (j:Jurisdiction {id: $jurisdiction})
                        MERGE (s)-[:BELONGS_TO]->(j)
                        """
                        session.run(query, id=sec['id'], code=sec.get('code'), title=sec.get('title'), text=sec.get('text'), jurisdiction=JURISDICTION)
                        
                    # 2. Zones
                    for zone in res.get("zones", []):
                        query = """
                        MERGE (z:Zone {id: $id})
                        SET z.name = $name, z.code = $code, z.type = $type
                        """
                        session.run(query, id=zone['id'], name=zone.get('name'), code=zone.get('code'), type=zone.get('type'))
                        
                    # 3. Relationships
                    for rel in res.get("relationships", []):
                        query = """
                        MATCH (s:Section {id: $sid})
                        MATCH (z:Zone {id: $zid})
                        MERGE (s)-[:APPLIES_TO]->(z)
                        """
                        session.run(query, sid=rel['from_section_id'], zid=rel['to_zone_id'])

                print(f"Processed {i + len(batch)}/{len(chunks)}")
                
    finally:
        driver.close()

if __name__ == "__main__":
    asyncio.run(main())


import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

query = """
MATCH (p:Parcel {parcel_id: '503911073240'})
OPTIONAL MATCH (p)-[:BELONGS_TO]->(s:Subdivision)
OPTIONAL MATCH (s)-[:MANAGED_BY]->(hoa:HOA)
RETURN p.parcel_id as parcel,
       substring(p.parcel_id, 0, 8) as first8,
       s.subdivision_id as subdiv,
       hoa.name as hoa
"""

result = driver.session().run(query).single()
print(f"Parcel ID: {result['parcel']}")
print(f"First 8 chars: {result['first8']}")
print(f"Subdivision in DB: {result['subdiv']}")
print(f"Current HOA: {result['hoa']}")

driver.close()

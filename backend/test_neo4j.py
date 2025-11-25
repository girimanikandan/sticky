from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

# Load .env
load_dotenv()

uri = os.getenv("NEO4J_URI")
user = os.getenv("NEO4J_USER")
password = os.getenv("NEO4J_PASSWORD")

print("Testing Neo4j connection...")
print("URI:", uri)
print("USER:", user)
print("PASSWORD:", "******")

try:
    driver = GraphDatabase.driver(uri, auth=(user, password))
    with driver.session() as session:
        result = session.run("RETURN 1 AS num").single()
        print("Success ->", result["num"])
except Exception as e:
    print("\n🔥 Neo4j REAL ERROR:")
    print(e)

#!/usr/bin/env python3
import os, json
from pathlib import Path
from neo4j import GraphDatabase

NEO4J_URI=os.getenv("NEO4J_URI","bolt://localhost:7687")
NEO4J_USER=os.getenv("NEO4J_USER","neo4j")
NEO4J_PASSWORD=os.getenv("NEO4J_PASSWORD","password")
CONTROLS_PATH=os.getenv("CONTROLS_PATH","policy-store/controls.json")

def main():
    # This assumes policy-store/controls.json exists from your Phase 1 setup.
    # As a fallback, create a dummy file if it's missing.
    controls_file = Path(CONTROLS_PATH)
    if not controls_file.exists():
        controls_file.parent.mkdir(parents=True, exist_ok=True)
        controls_file.write_text('[]')

    controls = json.loads(controls_file.read_text())
    drv = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    with drv.session() as s:
        s.run("CREATE CONSTRAINT IF NOT EXISTS FOR (t:TTP) REQUIRE t.id IS UNIQUE")
        s.run("CREATE CONSTRAINT IF NOT EXISTS FOR (c:Control) REQUIRE c.id IS UNIQUE")
        for c in controls:
            cid = c.get("id")
            ttps = c.get("mitre_ttp", []) or []
            if not cid or not ttps:
                continue
            s.run("MERGE (c:Control {id:$id}) SET c.name=$name, c.category=$cat",
                  id=cid, name=c.get("name"), cat=c.get("category"))
            for t in ttps:
                s.run("""
                    MERGE (tech:TTP {id:$t})
                    MERGE (ctrl:Control {id:$cid})-[:COVERS]->(tech)
                """, t=t, cid=cid)
    drv.close()
    print("Technique->Control links complete.")

if __name__ == "__main__":
    main()
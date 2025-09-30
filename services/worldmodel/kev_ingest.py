#!/usr/bin/env python3
import os, requests
from neo4j import GraphDatabase

KEV_URL=os.getenv("KEV_URL","https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json")
NEO4J_URI=os.getenv("NEO4J_URI","bolt://localhost:7687")
NEO4J_USER=os.getenv("NEO4J_USER","neo4j")
NEO4J_PASSWORD=os.getenv("NEO4J_PASSWORD","password")

def main():
    r = requests.get(KEV_URL, timeout=30)
    r.raise_for_status()
    vulns = r.json().get("vulnerabilities", [])
    drv = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    with drv.session() as s:
        s.run("CREATE CONSTRAINT IF NOT EXISTS FOR (v:Vuln) REQUIRE v.id IS UNIQUE")
        for v in vulns:
            cve = v.get("cveID")
            if not cve:
                continue
            s.run("""
                MERGE (x:Vuln {id:$cve})
                SET x.kev=true, x.vendor=$vendor, x.product=$product, x.name=$name,
                    x.date_added=date($added), x.due_date=date($due),
                    x.required_action=$action, x.known_ransomware=$ransom
            """,
            cve=cve,
            vendor=v.get("vendorProject"),
            product=v.get("product"),
            name=v.get("vulnerabilityName"),
            added=v.get("dateAdded"),
            due=v.get("dueDate"),
            action=v.get("requiredAction"),
            ransom=(v.get("knownRansomwareCampaignUse","Unknown")=="Known"))
    drv.close()
    print(f"Ingested {len(vulns)} KEV entries.")

if __name__ == "__main__":
    main()
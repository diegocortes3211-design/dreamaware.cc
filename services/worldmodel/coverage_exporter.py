#!/usr/bin/env python3
import os, time
from neo4j import GraphDatabase
from prometheus_client import Gauge, Counter, start_http_server

NEO4J_URI=os.getenv("NEO4J_URI","bolt://localhost:7687")
NEO4J_USER=os.getenv("NEO4J_USER","neo4j")
NEO4J_PASSWORD=os.getenv("NEO4J_PASSWORD","password")
PORT=int(os.getenv("COVERAGE_EXPORTER_PORT","9409"))
POLL=int(os.getenv("COVERAGE_POLL_SECONDS","60"))

g_total = Gauge("kev_total", "Total KEV CVEs")
g_ttp_mapped = Gauge("kev_ttp_mapped_total", "KEV CVEs with any TTP mapping")
g_ctrl_covered = Gauge("kev_control_covered_total", "KEV CVEs with Control coverage via TTP")
g_cov_ratio = Gauge("kev_coverage_ratio", "Ratio: KEV with Control coverage / KEV total")
g_top_tech = Gauge("kev_top_technique_count", "Occurrences of TTP in KEV mappings", ["tech"])
g_vendor_count = Gauge("kev_vendor_count", "KEV count by vendor", ["vendor"])

def q(session, cypher, **params):
    return list(session.run(cypher, **params))

def collect_once(session):
    # Totals
    total_res = q(session, "MATCH (v:Vuln {kev:true}) RETURN count(v) AS n")
    total = total_res[0]["n"] if total_res else 0

    mapped_res = q(session, """
        MATCH (v:Vuln {kev:true})-[:LINKED_TO|:INFERRED_TECH]->(:TTP)
        RETURN count(DISTINCT v) AS n
    """)
    mapped = mapped_res[0]["n"] if mapped_res else 0

    covered_res = q(session, """
        MATCH (v:Vuln {kev:true})-[:LINKED_TO|:INFERRED_TECH]->(t:TTP)<-[:COVERS]-(:Control)
        RETURN count(DISTINCT v) AS n
    """)
    covered = covered_res[0]["n"] if covered_res else 0

    g_total.set(total or 0)
    g_ttp_mapped.set(mapped or 0)
    g_ctrl_covered.set(covered or 0)
    g_cov_ratio.set((covered/total) if total else 0.0)

    # Top techniques
    for row in q(session, """
        MATCH (v:Vuln {kev:true})-[:LINKED_TO|:INFERRED_TECH]->(t:TTP)
        RETURN t.id AS tech, count(*) AS n ORDER BY n DESC LIMIT 20
    """):
        g_top_tech.labels(tech=row["tech"]).set(row["n"])

    # Vendor counts
    for row in q(session, """
        MATCH (v:Vuln {kev:true})
        WITH coalesce(v.vendor,'Unknown') AS vendor, count(*) AS n
        RETURN vendor, n
    """):
        g_vendor_count.labels(vendor=row["vendor"]).set(row["n"])

def main():
    drv = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    start_http_server(PORT)
    print(f"[coverage_exporter] listening on :{PORT}/metrics")
    with drv.session() as s:
        while True:
            try:
                collect_once(s)
            except Exception as e:
                print(f"[coverage_exporter] error: {e}")
            time.sleep(POLL)

if __name__ == "__main__":
    main()
import yaml, pathlib, datetime

root = pathlib.Path(__file__).resolve().parents[1]
mem = root / "memory" / "links.yml"
out_links = root / "docs" / "links.md"
out_refs = root / "docs" / "references.md"

data = yaml.safe_load(mem.read_text(encoding="utf-8"))
items = data.get("links", [])

out_links.parent.mkdir(parents=True, exist_ok=True)
out_refs.parent.mkdir(parents=True, exist_ok=True)

links_md = ["# Canonical Links (Memory)\n"]
for i, l in enumerate(items, 1):
    tags = ", ".join(l.get("tags", []))
    links_md.append(f"{i}. [{l['name']}]({l['url']}) \n _tags_: {tags}")

links_md.append(f"\n_Last updated: {datetime.datetime.utcnow().isoformat()}Z_")

out_links.write_text("\n".join(links_md), encoding="utf-8")

refs_md = """# References

Citations and primary evidence tracked here. For BibTeX-backed cites, see `docs/references.bib`.
"""
out_refs.write_text(refs_md, encoding="utf-8")

print(f"Wrote {out_links} and {out_refs}")

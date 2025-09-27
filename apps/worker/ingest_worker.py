#!/usr/bin/env python3
import argparse
from packages.ingest.orchestrator import IngestOrchestrator

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True)
    parser.add_argument("--query", required=True)
    parser.add_argument("--index-path", default=".index")
    args = parser.parse_args()

    orchestrator = IngestOrchestrator(args.index_path, prompts=[])
    response = orchestrator.process(args.source, args.query)
    if response:
        print(response)

if __name__ == "__main__":
    main()
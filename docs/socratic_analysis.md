---
id: socratic-analysis
title: Socratic Vulnerability Analysis
---

This document outlines the Socratic Vulnerability Analysis framework integrated into our agentics system. This framework provides a structured, automated way to identify, document, and propose mitigations for security risks within the codebase.

## Methodology

The Socratic analysis is a key step in our "Plan -> Act -> Evaluate -> Analyze -> Propose" agentic loop. After the `Evaluator` service scores the results of an execution, the `SocraticAnalyzer` service takes over.

Its primary responsibility is to translate raw findings (such as those from static analysis tools like Semgrep) into a structured, human-readable, and machine-readable format known as the **Vulnerability Map**.

## The Vulnerability Map

Every identified security risk is documented as a "Vulnerability Map" entry. This ensures that all findings are captured consistently and contain all the necessary information for triage and remediation.

The structure of the map is strictly enforced by a JSON schema.

### Core Components of a Vulnerability Map:

- **Component**: The precise location of the vulnerability (e.g., `services/api/ingest.py:normalize_input`).
- **Claim**: A statement of what the component is supposed to do, which the finding contradicts.
- **Evidence**: Concrete proof of the vulnerability, including file, line numbers, and the problematic code snippet.
- **Vector**: The category of the flaw (e.g., `Security/Input trust`, `Security/Static Analysis`).
- **Risk**: A structured assessment of the vulnerability's severity, including impact and likelihood.
- **Finding**: A clear, concise description of the problem.
- **Mitigation**: A high-level recommendation on how to fix the vulnerability.
- **Checks**: The specific automated checks that identified the flaw (e.g., a Semgrep rule ID).
- **Status**: The current state of the vulnerability (e.g., `open`, `closed`).

For the complete data contract, see the official schema file: `schemas/vuln_map.schema.json`.

## Integration into the Agentic Workflow

1.  **Generation**: The `SocraticAnalyzer` is called by the `Orchestrator` after the `Evaluator` runs. It inspects the execution output (e.g., Semgrep results) and generates a list of `Vulnerability Map` objects for any open risks.

2.  **Consumption**: The list of vulnerability maps is then passed to the `SelfModifier`.

3.  **Action**: The `SelfModifier` iterates through the open vulnerabilities in the maps and generates specific, actionable proposals aimed at mitigating each identified risk. This creates a direct, automated feedback loop from security finding to proposed solution.

This automated analysis and proposal system allows the agent to proactively identify and suggest fixes for security issues, hardening the codebase with each execution cycle.
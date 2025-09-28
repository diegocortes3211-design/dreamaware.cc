# Xikizpedia Architecture

This document provides a high-level overview of the Xikizpedia platform, a data-driven system for analyzing and ranking web content.

## System Overview

The platform is composed of two primary components: a backend API service and a dynamic frontend application.

1.  **Backend API (`services/xikizpedia_api/`)**: A Python-based service built with FastAPI. Its responsibilities include:
    *   Exposing endpoints for creating and retrieving data.
    *   Housing the scoring engine for calculating Trust and AI Slop scores.
    *   Managing the data persistence layer (currently in-memory, designed for a database).

2.  **Dynamic Frontend (`site/`)**: A Docusaurus-based web application. Its responsibilities include:
    *   Providing the user interface for the platform.
    *   Fetching data from the backend API to display dynamic content.
    *   Presenting the source leaderboard and individual "xiki" entries.

## Data Flow: Content Ingestion Pipeline

The end-to-end process of ingesting and analyzing new content is orchestrated by the **Ingestion Agent**.

1.  **Trigger**: The process begins when the `xikizpedia_ingest_agent.py` is executed with a target URL and a title.
2.  **Download**: The agent securely downloads the text content from the URL.
3.  **Scoring**: The agent sends the raw text content to the backend's `/internal/score-content/` endpoint. The backend's `scoring_engine` calculates the Trust and AI Slop scores and returns them to the agent.
4.  **Abstract Generation**: The agent generates a concise, APA-style abstract from the content (placeholder logic).
5.  **Entry Creation**: The agent bundles the title, content, URL, and abstract into a single payload and sends it to the backend's `/entries/` endpoint.
6.  **Persistence**: The backend API receives the data, associates it with the calculated scores, and saves the final, structured `Entry` to the database.

## API Contract

The backend service exposes the following primary endpoints:

*   `POST /entries/`
    *   **Payload**: `{ "title": str, "content": str, "url": HttpUrl, "abstract": str }`
    *   **Response**: The newly created `Entry` object, including its source and scores.
*   `GET /entries/{slug}`
    *   **Response**: A single `Entry` object matching the provided slug.
*   `GET /leaderboard/`
    *   **Response**: A list of `Source` objects, sorted in descending order by their trust score.
*   `POST /internal/score-content/`
    *   **Payload**: `{ "content": str }`
    *   **Response**: A `Score` object containing the calculated `trust` and `ai_slop` scores.

## Data Models

The core data models are defined in `services/xikizpedia_api/schemas.py`:

*   **Entry**: The main wiki/dictionary definition, containing the title, content, abstract, and a link to its source.
*   **Source**: Represents the analyzed URL, containing the URL itself and its associated score.
*   **Score**: A simple object containing the `trust` and `ai_slop` floating-point values.
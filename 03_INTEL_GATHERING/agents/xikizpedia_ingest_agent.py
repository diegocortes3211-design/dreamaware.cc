from __future__ import annotations
import requests
import argparse

# Configuration for the local API
API_BASE_URL = "http://127.0.0.1:8000"

def download_content(url: str) -> str:
    """
    Placeholder for securely downloading and transcribing content from a URL.
    For now, it returns a block of dummy text.
    """
    print(f"[*] Downloading content from {url}...")
    # In a real implementation, this would use libraries like requests, BeautifulSoup,
    # or a headless browser for text, and tools like yt-dlp and Whisper for video.
    return """
    This is a sample text block for the Xikizpedia ingestion agent.
    Artificial intelligence (AI) is a wide-ranging branch of computer science
    concerned with building smart machines capable of performing tasks that
    typically require human intelligence. It is an interdisciplinary science
    with multiple approaches, but advancements in machine learning and deep
    learning are creating a paradigm shift in virtually every sector of the tech industry.
    It is important to note the ethical considerations surrounding AI development.
    In conclusion, AI is a transformative technology.
    """

def get_scores_from_api(content: str) -> dict:
    """
    Calls the backend API to get trust and AI slop scores for the content.
    """
    print("[*] Getting scores from API...")
    try:
        response = requests.post(
            f"{API_BASE_URL}/internal/score-content/",
            json={"content": content}
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"[!] Error contacting scoring API: {e}")
        return None

def generate_apa_abstract(content: str) -> str:
    """
    Placeholder for generating a concise APA-style abstract.
    """
    print("[*] Generating APA abstract...")
    # In a real implementation, this would use a fine-tuned LLM.
    first_sentence = content.strip().split('.')[0]
    return f"This document discusses the core concepts of Artificial Intelligence. {first_sentence}."

def create_entry_in_api(title: str, content: str, url: str, abstract: str) -> dict:
    """
    Calls the backend API to create the final Xikizpedia entry.
    """
    print("[*] Creating new entry in API...")
    entry_data = {
        "title": title,
        "content": content,
        "url": url,
        "abstract": abstract,
    }
    try:
        response = requests.post(f"{API_BASE_URL}/entries/", json=entry_data)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"[!] Error creating entry in API: {e}")
        return None

def run_ingestion(url: str, title: str):
    """
    Orchestrates the end-to-end ingestion pipeline.
    """
    print(f"--- Starting ingestion for: {title} ---")

    content = download_content(url)
    if not content:
        return

    scores = get_scores_from_api(content)
    if not scores:
        return

    print(f"[*] Scores received: Trust={scores['trust']:.2f}, AI Slop={scores['ai_slop']:.2f}")

    abstract = generate_apa_abstract(content)

    final_entry = create_entry_in_api(title, content, url, abstract)
    if not final_entry:
        return

    print(f"--- Ingestion complete! ---")
    print(f"[*] Created entry: {final_entry['slug']}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Xikizpedia Ingestion Agent")
    parser.add_argument("url", help="The URL of the content to ingest.")
    parser.add_argument("--title", required=True, help="The title for the Xikizpedia entry.")
    args = parser.parse_args()

    run_ingestion(args.url, args.title)
# services/wiki/score_fetcher.py

import requests

class WikipediaScoreFetcher:
    """
    Fetches a "score" for a given topic from Wikipedia.
    The score is a simple measure of notability (e.g., page existence and length).
    """

    def __init__(self):
        """
        Initializes the fetcher with the Wikipedia API endpoint.
        """
        self.api_url = "https://en.wikipedia.org/w/api.php"

    def fetch_score(self, topic: str) -> float:
        """
        Fetches a notability score for a topic from Wikipedia.

        The score is based on whether the page exists and the length of its content.
        Returns 0.0 if the page does not exist or an error occurs.

        Args:
            topic (str): The topic to search for on Wikipedia.

        Returns:
            float: A notability score.
        """
        params = {
            "action": "query",
            "format": "json",
            "titles": topic,
            "prop": "extracts",
            "exintro": True,
            "explaintext": True,
            "redirects": 1,
        }

        try:
            response = requests.get(self.api_url, params=params)
            response.raise_for_status()  # Raise an exception for bad status codes
            data = response.json()

            pages = data["query"]["pages"]
            page_id = next(iter(pages))

            # If page_id is -1, the page does not exist
            if page_id == "-1":
                return 0.0

            extract = pages[page_id].get("extract", "")
            # Score is based on the length of the introductory extract
            score = len(extract) / 1000.0  # Normalize by an arbitrary factor
            return min(1.0, score) # Clamp score at 1.0

        except requests.exceptions.RequestException:
            return 0.0
        except (KeyError, StopIteration):
            # Handle cases where the response format is unexpected
            return 0.0

# commit: feat: Implement Wikipedia Score Fetcher to gauge topic notability.
# services/dictionary/glossary_builder.py

import requests

class GlossaryBuilder:
    """
    Builds a glossary of slang terms by fetching definitions from the
    Urban Dictionary API.
    """

    def __init__(self):
        """
        Initializes the builder with the Urban Dictionary API endpoint.
        """
        self.api_url = "https://api.urbandictionary.com/v0/define"

    def build(self, terms: list) -> dict:
        """
        Builds a glossary for the given list of terms.

        Args:
            terms (list): A list of slang terms to define.

        Returns:
            dict: A dictionary mapping each term to its top definition.
        """
        glossary = {}
        for term in terms:
            if not term:
                continue

            params = {"term": term}
            try:
                response = requests.get(self.api_url, params=params)
                response.raise_for_status()
                data = response.json()

                if data["list"]:
                    # Take the first and most popular definition
                    top_definition = data["list"][0]["definition"]
                    # Clean up the definition by removing brackets
                    cleaned_definition = top_definition.replace("[", "").replace("]", "")
                    glossary[term] = cleaned_definition
                else:
                    glossary[term] = "Definition not found"

            except (requests.exceptions.RequestException, KeyError):
                glossary[term] = "Error fetching definition"

        return glossary

# commit: feat: Add Glossary Builder for Urban Dictionary terms.
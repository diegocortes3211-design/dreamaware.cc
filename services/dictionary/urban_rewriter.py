# services/dictionary/urban_rewriter.py

import re

class UrbanRewriter:
    """
    Rewrites text by replacing slang terms with their more formal definitions
    based on a provided glossary.
    """

    def __init__(self, glossary: dict):
        """
        Initializes the rewriter with a glossary.

        Args:
            glossary (dict): A dictionary mapping slang terms to their definitions.
        """
        self.glossary = {k.lower(): v for k, v in glossary.items()}
        # Create a regex to find all glossary terms in a case-insensitive way
        if glossary:
            self.pattern = re.compile(
                r'\b(' + '|'.join(re.escape(key) for key in self.glossary.keys()) + r')\b',
                re.IGNORECASE
            )
        else:
            self.pattern = None

    def rewrite(self, text: str) -> str:
        """
        Rewrites the given text by replacing slang terms.

        Args:
            text (str): The text to rewrite.

        Returns:
            str: The rewritten text.
        """
        if not self.pattern:
            return text

        def replace_match(match):
            term = match.group(0).lower()
            definition = self.glossary.get(term, match.group(0))
            return f"{match.group(0)} (meaning: {definition})"

        return self.pattern.sub(replace_match, text)

# commit: feat: Implement Urban Dictionary Rewriter module.
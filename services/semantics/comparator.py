# services/semantics/comparator.py

class SemanticsComparator:
    """
    Compares the semantic similarity of two pieces of text using sentence embeddings.
    This implementation uses the sentence-transformers library.
    """

    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        """
        Initializes the comparator and loads a pre-trained sentence-transformer model.

        Args:
            model_name (str): The name of the sentence-transformer model to use.
        """
        try:
            from sentence_transformers import SentenceTransformer
            from sentence_transformers.util import cos_sim
            self.model = SentenceTransformer(model_name)
            self.cos_sim = cos_sim
            self.ready = True
        except ImportError:
            self.model = None
            self.cos_sim = None
            self.ready = False

    def compare(self, text1: str, text2: str) -> float:
        """
        Calculates the semantic similarity score between two texts.

        The score is the cosine similarity of the text embeddings, ranging from
        -1.0 (opposite) to 1.0 (identical), with 0.0 indicating no correlation.

        Returns 0.0 if the model is not available.

        Args:
            text1 (str): The first text to compare.
            text2 (str): The second text to compare.

        Returns:
            float: The cosine similarity score.
        """
        if not self.ready or not text1 or not text2:
            return 0.0

        # Encode the texts to get their embeddings
        embedding1 = self.model.encode(text1, convert_to_tensor=True)
        embedding2 = self.model.encode(text2, convert_to_tensor=True)

        # Compute cosine similarity
        similarity = self.cos_sim(embedding1, embedding2)

        # The result is a tensor, so we extract the float value
        return similarity.item()

# commit: feat: Implement Semantics Comparator using sentence-transformers.
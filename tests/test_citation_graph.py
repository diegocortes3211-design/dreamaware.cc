# tests/test_citation_graph.py

import unittest
from services.citation.graph import CitationGraph

class TestCitationGraph(unittest.TestCase):
    """
    Tests for the CitationGraph.
    """

    def setUp(self):
        """
        Set up a new CitationGraph for each test.
        """
        self.cg = CitationGraph()

    def test_initial_graph_is_empty(self):
        """
        Tests that a new graph is initialized with no nodes or edges.
        """
        nodes, edges = self.cg.get_graph_size()
        self.assertEqual(nodes, 0)
        self.assertEqual(edges, 0)
        self.assertEqual(self.cg.calculate_pagerank(), {})

    def test_add_citation(self):
        """
        Tests that adding a citation correctly updates the graph size.
        """
        self.cg.add_citation("paper_A", "paper_B")
        nodes, edges = self.cg.get_graph_size()
        self.assertEqual(nodes, 2)
        self.assertEqual(edges, 1)

    def test_calculate_pagerank(self):
        """
        Tests the PageRank calculation on a simple graph.
        """
        # Create a simple citation chain: A -> B -> C
        self.cg.add_citation("paper_A", "paper_B")
        self.cg.add_citation("paper_B", "paper_C")

        pagerank_scores = self.cg.calculate_pagerank()

        # In this simple chain, C should have the highest rank
        self.assertIn("paper_A", pagerank_scores)
        self.assertIn("paper_B", pagerank_scores)
        self.assertIn("paper_C", pagerank_scores)
        self.assertGreater(pagerank_scores["paper_C"], pagerank_scores["paper_B"])
        self.assertGreater(pagerank_scores["paper_B"], pagerank_scores["paper_A"])

    def test_pagerank_on_complex_graph(self):
        """
        Tests PageRank on a more complex graph where one paper is cited more.
        """
        self.cg.add_citation("paper_A", "paper_C")
        self.cg.add_citation("paper_B", "paper_C")
        self.cg.add_citation("paper_D", "paper_A")

        pagerank_scores = self.cg.calculate_pagerank()

        # Paper C is the most cited and should have the highest PageRank
        self.assertGreater(pagerank_scores["paper_C"], pagerank_scores["paper_A"])
        self.assertGreater(pagerank_scores["paper_A"], pagerank_scores["paper_B"])
        self.assertGreater(pagerank_scores["paper_A"], pagerank_scores["paper_D"])

if __name__ == "__main__":
    unittest.main()

# commit: test: Add unit tests for Citation Graph.
# services/citation/graph.py

import networkx as nx

class CitationGraph:
    """
    Manages a citation graph and calculates PageRank for nodes.
    This implementation uses the networkx library for robust graph operations.
    """

    def __init__(self):
        """
        Initializes a new directed graph.
        """
        self.graph = nx.DiGraph()

    def add_citation(self, citing_paper: str, cited_paper: str):
        """
        Adds a citation link to the graph.

        Args:
            citing_paper (str): The paper that is making the citation.
            cited_paper (str): The paper that is being cited.
        """
        self.graph.add_edge(citing_paper, cited_paper)

    def calculate_pagerank(self) -> dict:
        """
        Calculates the PageRank for all papers in the graph.

        Returns:
            dict: A dictionary mapping each paper to its PageRank score.
        """
        if not self.graph.nodes:
            return {}

        # networkx's pagerank returns a dictionary of node -> score
        return nx.pagerank(self.graph)

    def get_graph_size(self) -> tuple:
        """
        Returns the number of nodes and edges in the graph.

        Returns:
            tuple: A tuple containing (number_of_nodes, number_of_edges).
        """
        return (self.graph.number_of_nodes(), self.graph.number_of_edges())

# commit: feat: Implement Citation Graph with PageRank calculation using networkx.
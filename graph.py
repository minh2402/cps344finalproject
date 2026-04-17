
import networkx as nx 

class GraphManager:
    def __init__(self):
        self.graph = nx.Graph()
        self.pos = {}

    def create_graph(self, num_nodes, edges):
        self.graph.clear()
        self.graph.add_nodes_from(range(num_nodes))
        self.graph.add_edges_from(edges)
        self.pos = nx.spring_layout(self.graph)

    def get_neighbors(self, node):
        return list(self.graph.neighbors(node))
    
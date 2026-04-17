from __future__ import annotations

import heapq
import math
from dataclasses import dataclass


@dataclass(frozen=True)
class TopologySpec:
    name: str
    positions: dict[int, tuple[float, float]]
    edges: list[tuple[int, int, int]]
    default_source: int
    default_destination: int
    description: str


class SimpleGraph:
    def __init__(self) -> None:
        self.nodes: list[int] = []
        self._adjacency: dict[int, dict[int, dict[str, int]]] = {}

    def clear(self) -> None:
        self.nodes = []
        self._adjacency = {}

    def add_nodes_from(self, nodes) -> None:
        for node in nodes:
            if node not in self._adjacency:
                self._adjacency[node] = {}
                self.nodes.append(node)

    def add_edge(self, node_a: int, node_b: int, delay_ms: int) -> None:
        self.add_nodes_from([node_a, node_b])
        payload = {"delay_ms": delay_ms}
        self._adjacency[node_a][node_b] = payload
        self._adjacency[node_b][node_a] = payload

    def neighbors(self, node: int) -> list[int]:
        return list(self._adjacency[node].keys())

    def edges(self, data: bool = False):
        emitted: set[tuple[int, int]] = set()
        result = []
        for node_a, neighbors in self._adjacency.items():
            for node_b, payload in neighbors.items():
                edge = tuple(sorted((node_a, node_b)))
                if edge in emitted:
                    continue
                emitted.add(edge)
                if data:
                    result.append((edge[0], edge[1], payload))
                else:
                    result.append(edge)
        return result

    def edge_data(self, node_a: int, node_b: int) -> dict[str, int]:
        return self._adjacency[node_a][node_b]


TOPOLOGY_PRESETS: dict[str, TopologySpec] = {
    "Campus Backbone": TopologySpec(
        name="Campus Backbone",
        positions={
            0: (-0.95, 0.05),
            1: (-0.45, -0.45),
            2: (-0.15, 0.35),
            3: (0.25, -0.2),
            4: (0.65, 0.3),
            5: (0.95, -0.05),
        },
        edges=[
            (0, 1, 260),
            (0, 2, 180),
            (1, 2, 200),
            (1, 3, 220),
            (2, 3, 170),
            (2, 4, 230),
            (3, 4, 180),
            (3, 5, 260),
            (4, 5, 190),
        ],
        default_source=0,
        default_destination=5,
        description="Balanced multi-path topology for the default TCP vs UDP demo.",
    ),
    "Bottleneck Path": TopologySpec(
        name="Bottleneck Path",
        positions={
            0: (-0.95, 0.05),
            1: (-0.55, -0.3),
            2: (-0.2, 0.0),
            3: (0.2, 0.0),
            4: (0.55, 0.3),
            5: (0.95, -0.05),
        },
        edges=[
            (0, 1, 180),
            (1, 2, 220),
            (2, 3, 360),
            (3, 4, 220),
            (4, 5, 180),
            (1, 3, 420),
            (2, 4, 420),
        ],
        default_source=0,
        default_destination=5,
        description="A narrow center link makes packet loss and delay easier to observe.",
    ),
    "Redundant Ring": TopologySpec(
        name="Redundant Ring",
        positions={
            0: (-0.75, 0.0),
            1: (-0.35, -0.55),
            2: (0.35, -0.55),
            3: (0.75, 0.0),
            4: (0.35, 0.55),
            5: (-0.35, 0.55),
        },
        edges=[
            (0, 1, 170),
            (1, 2, 190),
            (2, 3, 170),
            (3, 4, 190),
            (4, 5, 170),
            (5, 0, 190),
            (0, 2, 240),
            (2, 4, 240),
            (4, 0, 240),
        ],
        default_source=5,
        default_destination=2,
        description="A looped topology that highlights alternate routes and duplicates.",
    ),
}


class GraphManager:
    def __init__(self) -> None:
        self.graph = SimpleGraph()
        self.pos: dict[int, tuple[float, float]] = {}
        self.current_topology_name = ""
        self.default_source = 0
        self.default_destination = 0
        self.description = ""

    def create_graph(
        self,
        num_nodes: int,
        edges: list[tuple[int, int]] | list[tuple[int, int, int]],
    ) -> None:
        self.graph.clear()
        self.graph.add_nodes_from(range(num_nodes))
        for edge in edges:
            if len(edge) == 2:
                node_a, node_b = edge
                delay_ms = 200
            else:
                node_a, node_b, delay_ms = edge
            self.graph.add_edge(node_a, node_b, delay_ms)
        self.pos = self._circle_layout(self.graph.nodes)
        self.current_topology_name = "Custom"
        self.default_source = 0
        self.default_destination = max(self.graph.nodes, default=0)
        self.description = "Custom topology"

    def load_topology(self, topology_name: str) -> None:
        spec = TOPOLOGY_PRESETS[topology_name]
        self.graph.clear()
        self.graph.add_nodes_from(spec.positions.keys())
        for node_a, node_b, delay_ms in spec.edges:
            self.graph.add_edge(node_a, node_b, delay_ms)
        self.pos = dict(spec.positions)
        self.current_topology_name = spec.name
        self.default_source = spec.default_source
        self.default_destination = spec.default_destination
        self.description = spec.description

    def cycle_topology(self, step: int = 1) -> str:
        names = list(TOPOLOGY_PRESETS.keys())
        if not self.current_topology_name:
            new_name = names[0]
        else:
            current_index = names.index(self.current_topology_name)
            new_name = names[(current_index + step) % len(names)]
        self.load_topology(new_name)
        return new_name

    def get_neighbors(self, node: int) -> list[int]:
        return self.graph.neighbors(node)

    def get_edge_delay(self, node_a: int, node_b: int) -> int:
        return int(self.graph.edge_data(node_a, node_b)["delay_ms"])

    def get_route(self, source: int, destination: int) -> list[int]:
        distances = {node: float("inf") for node in self.graph.nodes}
        previous: dict[int, int | None] = {node: None for node in self.graph.nodes}
        distances[source] = 0.0
        heap: list[tuple[float, int]] = [(0.0, source)]

        while heap:
            current_distance, node = heapq.heappop(heap)
            if node == destination:
                break
            if current_distance > distances[node]:
                continue
            for neighbor in self.graph.neighbors(node):
                new_distance = current_distance + self.get_edge_delay(node, neighbor)
                if new_distance >= distances[neighbor]:
                    continue
                distances[neighbor] = new_distance
                previous[neighbor] = node
                heapq.heappush(heap, (new_distance, neighbor))

        if distances[destination] == float("inf"):
            raise KeyError(f"No route from {source} to {destination}")

        route = [destination]
        while route[-1] != source:
            prev_node = previous[route[-1]]
            if prev_node is None:
                raise KeyError(f"No route from {source} to {destination}")
            route.append(prev_node)
        route.reverse()
        return route

    def build_forwarding_tables(self) -> dict[int, dict[int, int]]:
        forwarding_tables: dict[int, dict[int, int]] = {}
        for source in self.graph.nodes:
            table: dict[int, int] = {}
            for destination in self.graph.nodes:
                if source == destination:
                    continue
                route = self.get_route(source, destination)
                table[destination] = route[1]
            forwarding_tables[source] = table
        return forwarding_tables

    def get_topology_names(self) -> list[str]:
        return list(TOPOLOGY_PRESETS.keys())

    def _circle_layout(self, nodes: list[int]) -> dict[int, tuple[float, float]]:
        total = max(len(nodes), 1)
        positions: dict[int, tuple[float, float]] = {}
        for index, node in enumerate(nodes):
            angle = (index / total) * 6.28318
            positions[node] = (0.78 * math.cos(angle), 0.78 * math.sin(angle))
        return positions

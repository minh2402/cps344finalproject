from __future__ import annotations

import os

import pygame

from graph import GraphManager
from simulation import SimulationEngine

NODE_RADIUS = 22


class Renderer:
    def __init__(self, graph_manager: GraphManager) -> None:
        pygame.display.init()
        pygame.font.init()
        display_info = pygame.display.Info()
        self.width = max(1280, int(display_info.current_w * 0.94))
        self.height = max(800, int(display_info.current_h * 0.92))
        self.graph_width = int(self.width * 0.68)
        os.environ["SDL_VIDEO_CENTERED"] = "1"
        self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
        pygame.display.set_caption("TCP vs UDP Protocol Visualization")
        self.clock = pygame.time.Clock()
        self.graph_manager = graph_manager
        self.title_font = pygame.font.SysFont("arial", 26, bold=True)
        self.body_font = pygame.font.SysFont("arial", 16)
        self.small_font = pygame.font.SysFont("arial", 13)

    def draw(self, simulation: SimulationEngine) -> float:
        self.screen.fill((18, 22, 30))
        self._draw_graph(simulation)
        self._draw_side_panel(simulation)
        pygame.display.flip()
        return self.clock.tick(60)

    def _draw_graph(self, simulation: SimulationEngine) -> None:
        graph_surface = pygame.Rect(0, 0, self.graph_width, self.height)
        pygame.draw.rect(self.screen, (24, 31, 42), graph_surface)

        for node_a, node_b, data in self.graph_manager.graph.edges(data=True):
            point_a = self._to_screen(self.graph_manager.pos[node_a])
            point_b = self._to_screen(self.graph_manager.pos[node_b])
            pygame.draw.line(self.screen, (92, 110, 130), point_a, point_b, 3)
            midpoint = ((point_a[0] + point_b[0]) // 2, (point_a[1] + point_b[1]) // 2)
            delay_label = self.small_font.render(f"{int(data['delay_ms'])} ms", True, (160, 173, 190))
            self.screen.blit(delay_label, (midpoint[0] - 20, midpoint[1] - 12))

        for event in simulation.packet_events:
            if event.kind == "drop" and event.start_node is not None and event.end_node is not None:
                start = self._to_screen(self.graph_manager.pos[event.start_node])
                end = self._to_screen(self.graph_manager.pos[event.end_node])
                midpoint = ((start[0] + end[0]) // 2, (start[1] + end[1]) // 2)
                self._draw_cross(midpoint, (225, 90, 90))
                label = self.small_font.render(event.label, True, (236, 158, 158))
                self.screen.blit(label, (midpoint[0] - 28, midpoint[1] - 26))
            elif event.kind == "drop" and event.start_node is not None:
                pos = self._to_screen(self.graph_manager.pos[event.start_node])
                self._draw_cross(pos, (225, 90, 90))
                label = self.small_font.render(event.label, True, (236, 158, 158))
                self.screen.blit(label, (pos[0] - 28, pos[1] - 42))

        for flight in simulation.in_flight_packets:
            start = self._to_screen(self.graph_manager.pos[flight.start_node])
            end = self._to_screen(self.graph_manager.pos[flight.end_node])
            x = start[0] + (end[0] - start[0]) * flight.progress
            y = start[1] + (end[1] - start[1]) * flight.progress
            packet_color = self._packet_color(flight.packet, flight.delayed)
            pygame.draw.circle(self.screen, packet_color, (int(x), int(y)), 10)
            if flight.packet.retransmission:
                pygame.draw.circle(self.screen, (255, 225, 150), (int(x), int(y)), 13, 2)
            label = self.small_font.render(flight.packet.label, True, (240, 240, 240))
            self.screen.blit(label, (int(x) + 12, int(y) - 8))

        for node in self.graph_manager.graph.nodes:
            pos = self._to_screen(self.graph_manager.pos[node])
            is_endpoint = node in {simulation.source, simulation.destination}
            fill_color = (90, 170, 255) if is_endpoint else (88, 114, 140)
            pygame.draw.circle(self.screen, fill_color, pos, NODE_RADIUS)
            pygame.draw.circle(self.screen, (230, 240, 255), pos, NODE_RADIUS, 2)
            label = self.body_font.render(f"R{node}", True, (12, 18, 24))
            self.screen.blit(label, (pos[0] - 14, pos[1] - 10))

        for event in simulation.packet_events:
            if event.kind == "delivered" and event.node is not None:
                pos = self._to_screen(self.graph_manager.pos[event.node])
                pygame.draw.circle(self.screen, (100, 225, 150), pos, NODE_RADIUS + 8, 3)
                label = self.small_font.render(event.label, True, (165, 235, 188))
                self.screen.blit(label, (pos[0] - 18, pos[1] - 42))

        title = self.title_font.render("Network Topology", True, (240, 244, 250))
        subtitle = self.small_font.render(self.graph_manager.description, True, (176, 188, 204))
        self.screen.blit(title, (24, 18))
        self.screen.blit(subtitle, (24, 52))

    def _draw_side_panel(self, simulation: SimulationEngine) -> None:
        panel = pygame.Rect(self.graph_width, 0, self.width - self.graph_width, self.height)
        pygame.draw.rect(self.screen, (30, 36, 48), panel)
        pygame.draw.line(self.screen, (75, 86, 105), (self.graph_width, 0), (self.graph_width, self.height), 2)

        y = 24
        title = self.title_font.render("Protocol Simulator", True, (244, 247, 252))
        self.screen.blit(title, (self.graph_width + 24, y))
        y += 44

        for line in simulation.get_status_lines():
            surface = self.body_font.render(line, True, (215, 223, 234))
            self.screen.blit(surface, (self.graph_width + 24, y))
            y += 28

        y += 12
        section = self.body_font.render("Run Stats", True, (246, 211, 123))
        self.screen.blit(section, (self.graph_width + 24, y))
        y += 32
        for line in simulation.get_stat_lines():
            surface = self.body_font.render(line, True, (225, 230, 238))
            self.screen.blit(surface, (self.graph_width + 24, y))
            y += 28

        y += 18
        legend = self.body_font.render("Legend", True, (246, 211, 123))
        self.screen.blit(legend, (self.graph_width + 24, y))
        y += 28
        legend_items = [
            ((255, 156, 94), "UDP data"),
            ((112, 220, 160), "TCP data"),
            ((120, 205, 255), "ACK packet"),
            ((255, 204, 112), "Delayed packet"),
            ((206, 145, 255), "Duplicate packet"),
            ((255, 96, 96), "Dropped packet"),
        ]
        for color, label in legend_items:
            pygame.draw.circle(self.screen, color, (self.graph_width + 36, y + 8), 8)
            surface = self.body_font.render(label, True, (225, 230, 238))
            self.screen.blit(surface, (self.graph_width + 54, y))
            y += 26

        y += 18
        controls = self.body_font.render("Controls", True, (246, 211, 123))
        self.screen.blit(controls, (self.graph_width + 24, y))
        y += 28
        for line in simulation.get_controls():
            surface = self.small_font.render(line, True, (199, 208, 220))
            self.screen.blit(surface, (self.graph_width + 24, y))
            y += 22

    def _packet_color(self, packet, delayed: bool) -> tuple[int, int, int]:
        if packet.packet_type == "ack":
            return (120, 205, 255)
        if packet.duplicate:
            return (206, 145, 255)
        if packet.retransmission:
            return (255, 205, 124)
        if delayed:
            return (255, 221, 112)
        if packet.protocol == "UDP":
            return (255, 156, 94)
        return (112, 220, 160)

    def _draw_cross(self, center: tuple[int, int], color: tuple[int, int, int]) -> None:
        offset = 9
        pygame.draw.line(
            self.screen,
            color,
            (center[0] - offset, center[1] - offset),
            (center[0] + offset, center[1] + offset),
            3,
        )
        pygame.draw.line(
            self.screen,
            color,
            (center[0] - offset, center[1] + offset),
            (center[0] + offset, center[1] - offset),
            3,
        )

    def _to_screen(self, pos: tuple[float, float]) -> tuple[int, int]:
        x = int((pos[0] + 1.15) * (self.graph_width / 2.4))
        y = int((pos[1] + 1.05) * (self.height / 2.1))
        return x, y

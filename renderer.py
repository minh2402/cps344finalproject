import pygame

WIDTH, HEIGHT = 800, 600
NODE_RADIUS = 15

class Renderer:
    def __init__(self, graph_manager):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Graph Visualizer")
        self.clock = pygame.time.Clock()
        self.graph_manager = graph_manager

    def draw(self, messages):
        self.screen.fill((30, 30, 30))

    # Draw edges
        for edge in self.graph_manager.graph.edges():
            p1 = self._to_screen(self.graph_manager.pos[edge[0]])
            p2 = self._to_screen(self.graph_manager.pos[edge[1]])
            pygame.draw.line(self.screen, (200, 200, 200), p1, p2, 2)

    # Draw nodes
        for node in self.graph_manager.graph.nodes():
            pos = self._to_screen(self.graph_manager.pos[node])
            pygame.draw.circle(self.screen, (100, 200, 255), pos, NODE_RADIUS)

        # Draw messages
        for msg in messages:
            start_pos = self._to_screen(self.graph_manager.pos[msg.start])
            end_pos = self._to_screen(self.graph_manager.pos[msg.end])

            x = start_pos[0] + (end_pos[0] - start_pos[0]) * msg.progress
            y = start_pos[1] + (end_pos[1] - start_pos[1]) * msg.progress

            pygame.draw.circle(self.screen, (255, 100, 100), (int(x), int(y)), 6)

        pygame.display.flip()
        self.clock.tick(60)

    def _to_screen(self, pos):
        x = int(pos[0] * 300 + WIDTH // 2)
        y = int(pos[1] * 300 + HEIGHT // 2)
        return (x, y)

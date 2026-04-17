from graph import GraphManager
from renderer import Renderer
from simulation import Message
import pygame


def main():
    gm = GraphManager()

    # Example graph (you'll replace with user input later)
    num_nodes = 5
    edges = [(0,1), (1,2), (2,3), (3,4), (0,4)]
    gm.create_graph(num_nodes, edges)

    renderer = Renderer(gm)
    messages = [Message(0, 3)]

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Update messages
        for msg in messages[:]:
            if msg.update():
                messages.remove(msg)

        renderer.draw(messages)

    pygame.quit()


if __name__ == "__main__":
    main()

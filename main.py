from __future__ import annotations

import traceback

import pygame

from graph import GraphManager
from renderer import Renderer
from simulation import SimulationEngine


def handle_keydown(event: pygame.event.Event, simulation: SimulationEngine) -> None:
    if event.key == pygame.K_ESCAPE:
        raise SystemExit
    elif event.key == pygame.K_SPACE:
        simulation.start_run()
    elif event.key == pygame.K_m:
        simulation.toggle_mode()
    elif event.key == pygame.K_t:
        simulation.cycle_topology()
    elif event.key == pygame.K_c:
        simulation.toggle_chaos()
    elif event.key == pygame.K_d:
        simulation.toggle_duplicates()
    elif event.key == pygame.K_s:
        simulation.toggle_sdn()
    elif event.key == pygame.K_p:
        simulation.toggle_traffic_profile()
    elif event.key == pygame.K_LEFTBRACKET:
        simulation.adjust_loss_rate(-0.02)
    elif event.key == pygame.K_RIGHTBRACKET:
        simulation.adjust_loss_rate(0.02)
    elif event.key == pygame.K_MINUS:
        simulation.adjust_delay_multiplier(-0.1)
    elif event.key in {pygame.K_EQUALS, pygame.K_PLUS}:
        simulation.adjust_delay_multiplier(0.1)
    elif event.key == pygame.K_r:
        simulation.reset_run_state(keep_mode=True)


def main() -> None:
    graph_manager = GraphManager()
    simulation = SimulationEngine(graph_manager)
    simulation.setup_topology("Campus Backbone")
    renderer = Renderer(graph_manager)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                handle_keydown(event, simulation)

        dt_ms = renderer.draw(simulation)
        simulation.update(dt_ms)

    pygame.quit()


if __name__ == "__main__":
    try:
        main()
    except Exception:
        with open("crash.log", "w", encoding="utf-8") as crash_file:
            traceback.print_exc(file=crash_file)
        raise

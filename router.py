from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field

from packet import Packet


@dataclass
class Router:
    router_id: int
    forwarding_table: dict[int, int]
    processing_delay_ms: float = 45.0
    queue: deque[Packet] = field(default_factory=deque)
    next_available_time_ms: float = 0.0

    def enqueue(self, packet: Packet) -> None:
        self.queue.append(packet)

    def has_work(self) -> bool:
        return bool(self.queue)

    def next_hop(self, destination: int) -> int:
        next_hop = self.forwarding_table.get(destination)
        if next_hop is None:
            raise KeyError(f"No route from {self.router_id} to {destination}")
        return next_hop


def build_routers(
    forwarding_tables: dict[int, dict[int, int]],
    processing_delay_ms: float = 45.0,
) -> dict[int, Router]:
    return {
        router_id: Router(
            router_id=router_id,
            forwarding_table=table,
            processing_delay_ms=processing_delay_ms,
        )
        for router_id, table in forwarding_tables.items()
    }

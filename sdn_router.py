from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from packet import Packet
from router import Router


PacketPredicate = Callable[[Packet], bool]


@dataclass(frozen=True)
class Action:
    action_type: str
    action_value: int | None = None


class SDNRouter(Router):
    def __init__(
        self,
        router_id: int,
        forwarding_table: dict[int, int],
        rules: list[tuple[PacketPredicate, Action]],
        processing_delay_ms: float = 45.0,
    ) -> None:
        super().__init__(
            router_id=router_id,
            forwarding_table=forwarding_table,
            processing_delay_ms=processing_delay_ms,
        )
        self.rules = rules

    def apply_rules(self, packet: Packet) -> Action | None:
        for predicate, action in self.rules:
            if predicate(packet):
                return action
        return None


def build_demo_sdn_routers(
    forwarding_tables: dict[int, dict[int, int]],
    firewall_router: int | None,
    blocked_port: int = 80,
    processing_delay_ms: float = 45.0,
) -> dict[int, Router]:
    routers: dict[int, Router] = {}
    for router_id, table in forwarding_tables.items():
        if router_id == firewall_router:
            rules = [
                (
                    lambda packet, blocked_port=blocked_port: packet.dst_port == blocked_port
                    and packet.packet_type == "data",
                    Action("drop"),
                )
            ]
            routers[router_id] = SDNRouter(
                router_id=router_id,
                forwarding_table=table,
                rules=rules,
                processing_delay_ms=processing_delay_ms,
            )
        else:
            routers[router_id] = Router(
                router_id=router_id,
                forwarding_table=table,
                processing_delay_ms=processing_delay_ms,
            )
    return routers

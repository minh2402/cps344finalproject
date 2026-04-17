from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Packet:
    packet_id: int
    session_id: int
    source: int
    destination: int
    current_node: int
    protocol: str
    packet_type: str
    sequence: int
    dst_port: int = 443
    ack_for: int | None = None
    retransmission: bool = False
    duplicate: bool = False
    duplicated_from: int | None = None
    route_history: list[int] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.route_history:
            self.route_history = [self.current_node]

    @property
    def label(self) -> str:
        if self.packet_type == "ack":
            return f"ACK {self.ack_for}"
        return f"{self.protocol} {self.sequence}"


@dataclass
class InFlightPacket:
    packet: Packet
    start_node: int
    end_node: int
    total_time_ms: float
    remaining_time_ms: float
    delayed: bool = False
    dropped: bool = False

    @property
    def progress(self) -> float:
        if self.total_time_ms <= 0:
            return 1.0
        return max(0.0, min(1.0, 1.0 - (self.remaining_time_ms / self.total_time_ms)))


@dataclass
class PacketEvent:
    kind: str
    node: int | None = None
    start_node: int | None = None
    end_node: int | None = None
    label: str = ""
    ttl_ms: float = 900.0

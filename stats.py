from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class RunStats:
    packets_sent: int = 0
    packets_delivered: int = 0
    packets_dropped: int = 0
    retransmissions: int = 0
    duplicate_packets: int = 0
    acknowledgements: int = 0
    start_time_ms: float | None = None
    end_time_ms: float | None = None
    completed_sequences: set[int] = field(default_factory=set)

    def mark_started(self, now_ms: float) -> None:
        if self.start_time_ms is None:
            self.start_time_ms = now_ms

    def mark_finished(self, now_ms: float) -> None:
        self.end_time_ms = now_ms

    @property
    def completion_time_ms(self) -> float:
        if self.start_time_ms is None:
            return 0.0
        end_time = self.end_time_ms if self.end_time_ms is not None else self.start_time_ms
        return max(0.0, end_time - self.start_time_ms)

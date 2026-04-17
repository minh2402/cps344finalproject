from __future__ import annotations

import heapq
import random
from dataclasses import dataclass
from typing import Callable

from graph import GraphManager
from packet import InFlightPacket, Packet, PacketEvent
from router import Router, build_routers
from sdn_router import SDNRouter, build_demo_sdn_routers
from stats import RunStats


@dataclass
class NetworkConditions:
    loss_rate: float = 0.08
    delay_multiplier: float = 1.0
    duplicate_rate: float = 0.04
    chaos_mode: bool = False


class SimulationEngine:
    def __init__(self, graph_manager: GraphManager) -> None:
        self.graph_manager = graph_manager
        self.random = random.Random(344)
        self.conditions = NetworkConditions()
        self.mode = "UDP"
        self.packet_goal = 6
        self.traffic_port = 443
        self.use_sdn = False
        self.send_interval_ms = 260.0
        self.retransmission_timeout_ms = 950.0
        self.max_runtime_ms = 25000.0
        self.processing_delay_ms = 45.0
        self.firewall_nodes = {
            "Campus Backbone": 3,
            "Bottleneck Path": 2,
            "Redundant Ring": 4,
        }

        self.current_time_ms = 0.0
        self.running = False
        self.completed = False
        self.source = 0
        self.destination = 0
        self.session_id = 1
        self.next_packet_id = 1
        self.next_event_id = 1
        self.next_sequence_to_send = 0
        self.awaiting_ack: int | None = None
        self.timeout_token = 0
        self.udp_sent_all = False
        self.chaos_drop_remaining = 0
        self.delivered_sequences: set[int] = set()

        self.events: list[tuple[float, int, Callable[[], None]]] = []
        self.in_flight_packets: list[InFlightPacket] = []
        self.packet_events: list[PacketEvent] = []
        self.routers: dict[int, Router] = {}
        self.stats = RunStats()

    def setup_topology(self, topology_name: str | None = None) -> None:
        if topology_name is not None:
            self.graph_manager.load_topology(topology_name)
        elif not self.graph_manager.current_topology_name:
            self.graph_manager.load_topology(self.graph_manager.get_topology_names()[0])
        self.source = self.graph_manager.default_source
        self.destination = self.graph_manager.default_destination
        self._rebuild_routers()
        self.reset_run_state(keep_mode=True)

    def reset_run_state(self, keep_mode: bool = True) -> None:
        if not keep_mode:
            self.mode = "UDP"
        self.current_time_ms = 0.0
        self.running = False
        self.completed = False
        self.next_sequence_to_send = 0
        self.awaiting_ack = None
        self.timeout_token = 0
        self.udp_sent_all = False
        self.chaos_drop_remaining = 0
        self.delivered_sequences = set()
        self.next_packet_id = 1
        self.next_event_id = 1
        self.events = []
        self.in_flight_packets = []
        self.packet_events = []
        self.stats = RunStats()
        for router in self.routers.values():
            router.queue.clear()
            router.next_available_time_ms = 0.0

    def start_run(self) -> None:
        self.reset_run_state(keep_mode=True)
        self.running = True
        self.stats.mark_started(self.current_time_ms)
        if self.mode == "UDP":
            for sequence in range(self.packet_goal):
                delay_ms = sequence * self.send_interval_ms
                self._schedule(delay_ms, lambda seq=sequence: self._send_data(seq))
            self.udp_sent_all = True
        else:
            self._schedule(0.0, lambda: self._send_data(0))

    def update(self, dt_ms: float) -> None:
        self._update_packet_events(dt_ms)
        if not self.running:
            return

        self.current_time_ms += dt_ms
        self._run_due_events()
        self._dispatch_routers()
        self._advance_in_flight_packets(dt_ms)

        if self.mode == "UDP" and self.udp_sent_all and self._network_idle():
            self._finish_run()
        elif self.mode == "TCP" and self.completed and self._network_idle():
            self._finish_run()
        elif self.current_time_ms >= self.max_runtime_ms:
            self._finish_run()

    def set_mode(self, mode: str) -> None:
        self.mode = mode
        self.reset_run_state(keep_mode=True)

    def toggle_mode(self) -> None:
        self.set_mode("TCP" if self.mode == "UDP" else "UDP")

    def cycle_topology(self) -> None:
        self.graph_manager.cycle_topology()
        self._rebuild_routers()
        self.reset_run_state(keep_mode=True)

    def toggle_duplicates(self) -> None:
        self.conditions.duplicate_rate = 0.05 if self.conditions.duplicate_rate == 0.0 else 0.0
        self.reset_run_state(keep_mode=True)

    def toggle_chaos(self) -> None:
        self.conditions.chaos_mode = not self.conditions.chaos_mode
        self.reset_run_state(keep_mode=True)

    def toggle_sdn(self) -> None:
        self.use_sdn = not self.use_sdn
        self._rebuild_routers()
        self.reset_run_state(keep_mode=True)

    def toggle_traffic_profile(self) -> None:
        self.traffic_port = 80 if self.traffic_port == 443 else 443
        self.reset_run_state(keep_mode=True)

    def adjust_loss_rate(self, delta: float) -> None:
        self.conditions.loss_rate = min(0.6, max(0.0, self.conditions.loss_rate + delta))
        self.reset_run_state(keep_mode=True)

    def adjust_delay_multiplier(self, delta: float) -> None:
        self.conditions.delay_multiplier = min(
            2.5,
            max(0.4, self.conditions.delay_multiplier + delta),
        )
        self.reset_run_state(keep_mode=True)

    def _rebuild_routers(self) -> None:
        forwarding_tables = self.graph_manager.build_forwarding_tables()
        if self.use_sdn:
            firewall_router = self.firewall_nodes.get(self.graph_manager.current_topology_name)
            self.routers = build_demo_sdn_routers(
                forwarding_tables=forwarding_tables,
                firewall_router=firewall_router,
                processing_delay_ms=self.processing_delay_ms,
            )
        else:
            self.routers = build_routers(
                forwarding_tables=forwarding_tables,
                processing_delay_ms=self.processing_delay_ms,
            )

    def _schedule(self, delay_ms: float, callback: Callable[[], None]) -> None:
        due_time = self.current_time_ms + delay_ms
        heapq.heappush(self.events, (due_time, self.next_event_id, callback))
        self.next_event_id += 1

    def _run_due_events(self) -> None:
        while self.events and self.events[0][0] <= self.current_time_ms:
            _, _, callback = heapq.heappop(self.events)
            callback()

    def _dispatch_routers(self) -> None:
        for router_id in sorted(self.routers):
            router = self.routers[router_id]
            if not router.has_work() or router.next_available_time_ms > self.current_time_ms:
                continue

            packet = router.queue.popleft()
            action = None
            if isinstance(router, SDNRouter):
                action = router.apply_rules(packet)
                if action is not None and action.action_type == "drop":
                    self._record_drop(packet, start_node=router.router_id, end_node=None, reason="SDN drop")
                    router.next_available_time_ms = self.current_time_ms + router.processing_delay_ms
                    continue

            next_hop = (
                action.action_value
                if action is not None and action.action_type == "forward"
                else router.next_hop(packet.destination)
            )
            router.next_available_time_ms = self.current_time_ms + router.processing_delay_ms
            self._launch_link(packet, router.router_id, next_hop)

    def _advance_in_flight_packets(self, dt_ms: float) -> None:
        remaining_packets: list[InFlightPacket] = []
        for flight in self.in_flight_packets:
            flight.remaining_time_ms -= dt_ms
            if flight.remaining_time_ms > 0:
                remaining_packets.append(flight)
                continue

            if flight.dropped:
                self._record_drop(
                    flight.packet,
                    start_node=flight.start_node,
                    end_node=flight.end_node,
                    reason="Link loss",
                )
                continue

            self._handle_arrival(flight)

        self.in_flight_packets = remaining_packets

    def _handle_arrival(self, flight: InFlightPacket) -> None:
        packet = flight.packet
        packet.current_node = flight.end_node
        packet.route_history.append(flight.end_node)
        if packet.current_node == packet.destination:
            self._record_delivery(packet)
            if packet.packet_type == "data":
                self._on_data_received(packet)
            else:
                self._on_ack_received(packet)
            return

        self.routers[packet.current_node].enqueue(packet)

    def _send_data(self, sequence: int, retransmission: bool = False) -> None:
        if sequence >= self.packet_goal:
            return

        packet = self._make_packet(
            source=self.source,
            destination=self.destination,
            packet_type="data",
            sequence=sequence,
            ack_for=None,
            retransmission=retransmission,
        )
        self._inject_packet(packet)

        if self.mode == "TCP":
            self.awaiting_ack = sequence
            self.timeout_token += 1
            active_token = self.timeout_token
            self._schedule(
                self.retransmission_timeout_ms,
                lambda seq=sequence, token=active_token: self._on_timeout(seq, token),
            )

    def _send_ack(self, sequence: int) -> None:
        ack_packet = self._make_packet(
            source=self.destination,
            destination=self.source,
            packet_type="ack",
            sequence=sequence,
            ack_for=sequence,
            retransmission=False,
        )
        self.stats.acknowledgements += 1
        self._inject_packet(ack_packet)

    def _inject_packet(self, packet: Packet) -> None:
        self.stats.packets_sent += 1
        if packet.retransmission:
            self.stats.retransmissions += 1
        if packet.duplicate:
            self.stats.duplicate_packets += 1
        self.routers[packet.source].enqueue(packet)

    def _make_packet(
        self,
        source: int,
        destination: int,
        packet_type: str,
        sequence: int,
        ack_for: int | None,
        retransmission: bool,
        duplicate: bool = False,
        duplicated_from: int | None = None,
    ) -> Packet:
        packet = Packet(
            packet_id=self.next_packet_id,
            session_id=self.session_id,
            source=source,
            destination=destination,
            current_node=source,
            protocol=self.mode,
            packet_type=packet_type,
            sequence=sequence,
            ack_for=ack_for,
            dst_port=self.traffic_port,
            retransmission=retransmission,
            duplicate=duplicate,
            duplicated_from=duplicated_from,
        )
        self.next_packet_id += 1
        return packet

    def _launch_link(self, packet: Packet, start_node: int, end_node: int) -> None:
        base_delay_ms = self.graph_manager.get_edge_delay(start_node, end_node)
        total_delay_ms, delayed = self._sample_link_delay(base_delay_ms)
        dropped = self._should_drop_packet()
        self.in_flight_packets.append(
            InFlightPacket(
                packet=packet,
                start_node=start_node,
                end_node=end_node,
                total_time_ms=total_delay_ms,
                remaining_time_ms=total_delay_ms,
                delayed=delayed,
                dropped=dropped,
            )
        )

        if self.conditions.duplicate_rate > 0.0 and self.random.random() < self.conditions.duplicate_rate:
            duplicate_packet = self._make_packet(
                source=packet.source,
                destination=packet.destination,
                packet_type=packet.packet_type,
                sequence=packet.sequence,
                ack_for=packet.ack_for,
                retransmission=packet.retransmission,
                duplicate=True,
                duplicated_from=packet.packet_id,
            )
            duplicate_packet.current_node = start_node
            duplicate_packet.route_history = list(packet.route_history)
            self._inject_duplicate_flight(duplicate_packet, start_node, end_node, base_delay_ms)

    def _inject_duplicate_flight(self, packet: Packet, start_node: int, end_node: int, base_delay_ms: int) -> None:
        self.stats.packets_sent += 1
        self.stats.duplicate_packets += 1
        total_delay_ms, delayed = self._sample_link_delay(base_delay_ms)
        self.in_flight_packets.append(
            InFlightPacket(
                packet=packet,
                start_node=start_node,
                end_node=end_node,
                total_time_ms=total_delay_ms,
                remaining_time_ms=total_delay_ms,
                delayed=delayed,
                dropped=self._should_drop_packet(),
            )
        )

    def _sample_link_delay(self, base_delay_ms: int) -> tuple[float, bool]:
        scaled_base = base_delay_ms * self.conditions.delay_multiplier
        jitter = self.random.uniform(0.0, 80.0 * self.conditions.delay_multiplier)
        total_delay = scaled_base + jitter
        if self.conditions.chaos_mode and self.random.random() < 0.18:
            total_delay += self.random.uniform(250.0, 850.0)
        return total_delay, total_delay > (base_delay_ms * 1.35)

    def _should_drop_packet(self) -> bool:
        if self.conditions.chaos_mode:
            if self.chaos_drop_remaining > 0:
                self.chaos_drop_remaining -= 1
                return True
            if self.random.random() < 0.05:
                self.chaos_drop_remaining = self.random.randint(1, 2)
                return True
        return self.random.random() < self.conditions.loss_rate

    def _on_data_received(self, packet: Packet) -> None:
        if packet.sequence not in self.delivered_sequences:
            self.delivered_sequences.add(packet.sequence)
            self.stats.completed_sequences.add(packet.sequence)
            self.stats.packets_delivered += 1

        if self.mode == "TCP":
            self._send_ack(packet.sequence)

    def _on_ack_received(self, packet: Packet) -> None:
        if self.awaiting_ack != packet.ack_for:
            return
        self.awaiting_ack = None
        if packet.ack_for is None:
            return
        next_sequence = packet.ack_for + 1
        if next_sequence >= self.packet_goal:
            self.completed = True
            return
        self.next_sequence_to_send = next_sequence
        self._schedule(150.0, lambda seq=next_sequence: self._send_data(seq))

    def _on_timeout(self, sequence: int, token: int) -> None:
        if not self.running or self.completed:
            return
        if self.awaiting_ack != sequence or token != self.timeout_token:
            return
        self._send_data(sequence, retransmission=True)

    def _record_drop(
        self,
        packet: Packet,
        start_node: int | None,
        end_node: int | None,
        reason: str,
    ) -> None:
        self.stats.packets_dropped += 1
        self.packet_events.append(
            PacketEvent(
                kind="drop",
                start_node=start_node,
                end_node=end_node,
                label=reason,
            )
        )

    def _record_delivery(self, packet: Packet) -> None:
        label = "ACK" if packet.packet_type == "ack" else f"SEQ {packet.sequence}"
        self.packet_events.append(PacketEvent(kind="delivered", node=packet.current_node, label=label))

    def _update_packet_events(self, dt_ms: float) -> None:
        next_events: list[PacketEvent] = []
        for event in self.packet_events:
            event.ttl_ms -= dt_ms
            if event.ttl_ms > 0:
                next_events.append(event)
        self.packet_events = next_events

    def _network_idle(self) -> bool:
        routers_busy = any(router.has_work() for router in self.routers.values())
        return not routers_busy and not self.in_flight_packets and not self.events

    def _finish_run(self) -> None:
        if not self.running:
            return
        self.running = False
        self.completed = True
        self.stats.mark_finished(self.current_time_ms)

    def get_status_lines(self) -> list[str]:
        mode_label = f"{self.mode}-like"
        traffic_label = "HTTP/80" if self.traffic_port == 80 else "HTTPS/443"
        run_state = "Running" if self.running else "Idle"
        return [
            f"Mode: {mode_label}   State: {run_state}",
            f"Topology: {self.graph_manager.current_topology_name}",
            (
                "Conditions: "
                f"loss={self.conditions.loss_rate:.0%}, "
                f"delay x{self.conditions.delay_multiplier:.1f}, "
                f"duplicate={'on' if self.conditions.duplicate_rate > 0 else 'off'}, "
                f"chaos={'on' if self.conditions.chaos_mode else 'off'}"
            ),
            (
                "Traffic: "
                f"{traffic_label}, SDN={'on' if self.use_sdn else 'off'}, "
                f"source={self.source}, destination={self.destination}"
            ),
        ]

    def get_stat_lines(self) -> list[str]:
        elapsed_ms = self.stats.completion_time_ms if not self.running else self.current_time_ms
        return [
            f"Packets sent: {self.stats.packets_sent}",
            f"Packets delivered: {self.stats.packets_delivered}/{self.packet_goal}",
            f"Packets dropped: {self.stats.packets_dropped}",
            f"Retransmissions: {self.stats.retransmissions}",
            f"Duplicates: {self.stats.duplicate_packets}",
            f"Acknowledgements: {self.stats.acknowledgements}",
            f"Completion time: {elapsed_ms / 1000.0:.2f}s",
        ]

    def get_controls(self) -> list[str]:
        return [
            "SPACE start run",
            "M switch UDP/TCP",
            "T cycle topology",
            "C toggle chaos",
            "D toggle duplicates",
            "S toggle SDN firewall",
            "P toggle traffic port 443/80",
            "[ / ] adjust loss",
            "- / = adjust delay",
            "R reset",
        ]

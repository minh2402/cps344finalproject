# TCP vs UDP Protocol Visualization on Custom Network Topologies

This repository now contains a single Python simulator for the CPS344 final project. It reuses the original Python visualization structure, the forwarding-table ideas from the packet-forwarding homework, and the delay/loss/retransmission concepts from the C++ assignments.

## Files

- `main.py` - pygame entry point and keyboard controls
- `graph.py` - predefined topologies, positions, shortest-path routing, forwarding-table generation
- `renderer.py` - topology drawing, packet animation, event markers, stats panel
- `packet.py` - packet and in-flight animation models
- `router.py` - forwarding-table router queues
- `sdn_router.py` - optional SDN-style firewall drop rule
- `simulation.py` - UDP-like and TCP-like behavior, network conditions, events, retransmissions
- `stats.py` - per-run metrics

## Run

1. Install dependencies:

```bash
python3 -m pip install pygame
```

2. Start the simulator:

```bash
python3 main.py
```

## Controls

- `Space` - start a run
- `M` - switch between UDP-like and TCP-like mode
- `T` - cycle predefined topologies
- `C` - toggle chaos mode
- `D` - toggle duplicate packets
- `S` - toggle SDN firewall behavior
- `P` - switch traffic profile between port `443` and blocked port `80`
- `[` and `]` - decrease or increase packet loss
- `-` and `=` - decrease or increase delay multiplier
- `R` - reset the current run
- `Esc` - exit the simulator window

## Notes

- The UDP mode sends packets without retransmission.
- The TCP mode uses sequence numbers, ACK packets, and timeout-based retransmission.
- SDN mode adds a simple firewall-style rule that drops data packets destined for port `80` at one router.

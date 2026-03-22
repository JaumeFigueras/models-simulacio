#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
M/M/1 Queue with Two Arrival Streams
=====================================

A single-server queueing system fed by **two independent Poisson arrival
streams**, each producing a different entity type.  The process block
uses a **dictionary-based service time** to apply a different exponential
service distribution depending on the entity type.

Model structure::

    Arrival (TypeA) ──┐
                      ├──→ Process (Server) ──→ Delete (Exit)
    Arrival (TypeB) ──┘

- **TypeA** arrivals: exponential IAT with mean ``MEAN_IAT_A`` minutes,
  exponential service with mean ``MEAN_SERVICE_A`` minutes.
- **TypeB** arrivals: exponential IAT with mean ``MEAN_IAT_B`` minutes,
  exponential service with mean ``MEAN_SERVICE_B`` minutes.

The combined arrival rate is λ = λ_A + λ_B and the system behaves as an
M/M/1 queue with a mixed service distribution.  The server utilization
is ρ = λ_A · E[S_A] + λ_B · E[S_B] (provided ρ < 1 for stability).

With the default parameters:

    λ_A = 1/8 = 0.125,  E[S_A] = 3.0  →  ρ_A = 0.375
    λ_B = 1/12 = 0.0833, E[S_B] = 4.0  →  ρ_B = 0.333
    ρ = ρ_A + ρ_B = 0.708
"""

import random

import simpy

from simpy_extensions.process_flow import Arrival, Process, Delete, Resource

# ── Parameters ───────────────────────────────────────────────────────
MEAN_IAT_A = 8.0           # Mean inter-arrival time TypeA (minutes)
MEAN_IAT_B = 12.0          # Mean inter-arrival time TypeB (minutes)
MEAN_SERVICE_A = 3.0       # Mean service time TypeA (minutes)
MEAN_SERVICE_B = 4.0       # Mean service time TypeB (minutes)
SIM_TIME = 100_000         # Simulation horizon (minutes)
RANDOM_SEED = 42           # Reproducibility

# ── Theoretical values ──────────────────────────────────────────────
lam_a = 1.0 / MEAN_IAT_A
lam_b = 1.0 / MEAN_IAT_B
lam_total = lam_a + lam_b
rho_a = lam_a * MEAN_SERVICE_A
rho_b = lam_b * MEAN_SERVICE_B
rho = rho_a + rho_b

# ── Build model ─────────────────────────────────────────────────────
random.seed(RANDOM_SEED)
env = simpy.Environment()

# Single server (M/M/1)
server = Resource(env, name='Server', capacity=1)

# Process block with dictionary-based service times per entity type
station = Process(
    env,
    name='Service',
    resource=server,
    service_time={
        'TypeA': lambda: random.expovariate(1.0 / MEAN_SERVICE_A),
        'TypeB': lambda: random.expovariate(1.0 / MEAN_SERVICE_B),
    },
)

# Delete block (terminal)
sink = Delete(env, name='Exit')

# Connect: Process → Delete
station.next_block = sink

# Two independent arrival streams, both feeding the same process block
source_a = Arrival(
    env,
    name='TypeA Arrivals',
    inter_arrival_time=lambda: random.expovariate(1.0 / MEAN_IAT_A),
    entity_type='TypeA',
    entity_name_prefix='PartA',
    next_block=station,
)

source_b = Arrival(
    env,
    name='TypeB Arrivals',
    inter_arrival_time=lambda: random.expovariate(1.0 / MEAN_IAT_B),
    entity_type='TypeB',
    entity_name_prefix='PartB',
    next_block=station,
)

# ── Run ──────────────────────────────────────────────────────────────
env.run(until=SIM_TIME)

# ── Results ──────────────────────────────────────────────────────────
type_a_entities = [e for e in sink.deleted_entities if e.entity_type == 'TypeA']
type_b_entities = [e for e in sink.deleted_entities if e.entity_type == 'TypeB']

avg_system_a = (sum(e.system_time() for e in type_a_entities) / len(type_a_entities)
                if type_a_entities else 0.0)
avg_system_b = (sum(e.system_time() for e in type_b_entities) / len(type_b_entities)
                if type_b_entities else 0.0)

print("=" * 60)
print("M/M/1 Queue with Two Arrival Streams")
print("=" * 60)
print(f"Simulation time:       {SIM_TIME:,} minutes")
print(f"Random seed:           {RANDOM_SEED}")
print()

print("--- Arrival Parameters ---")
print(f"TypeA: mean IAT = {MEAN_IAT_A} min (λ_A = {lam_a:.4f}), "
      f"mean service = {MEAN_SERVICE_A} min")
print(f"TypeB: mean IAT = {MEAN_IAT_B} min (λ_B = {lam_b:.4f}), "
      f"mean service = {MEAN_SERVICE_B} min")
print(f"Combined λ = {lam_total:.4f},  "
      f"ρ = {rho_a:.3f} + {rho_b:.3f} = {rho:.4f}")
print()

print("--- Entity Counts ---")
print(f"{'Stream':<20} {'Created':>10} {'Deleted':>10}")
print("-" * 42)
print(f"{'TypeA':<20} {source_a.entities_created:>10,} {len(type_a_entities):>10,}")
print(f"{'TypeB':<20} {source_b.entities_created:>10,} {len(type_b_entities):>10,}")
print(f"{'Total':<20} "
      f"{source_a.entities_created + source_b.entities_created:>10,} "
      f"{sink.entities_deleted:>10,}")
print()

print("--- Performance Metrics ---")
print(f"{'Metric':<30} {'Simulation':>12} {'Theory':>12}")
print("-" * 56)
print(f"{'Server utilization':<30} "
      f"{server.stats.utilization(env.now):>12.4f} "
      f"{rho:>12.4f}")
print(f"{'Avg system time (all)':<30} "
      f"{sink.avg_system_time():>12.4f} {'—':>12}")
print(f"{'Avg system time (TypeA)':<30} "
      f"{avg_system_a:>12.4f} {'—':>12}")
print(f"{'Avg system time (TypeB)':<30} "
      f"{avg_system_b:>12.4f} {'—':>12}")
print(f"{'Avg wait in queue':<30} "
      f"{server.stats.avg_wait_time():>12.4f} {'—':>12}")
print(f"{'Avg queue length':<30} "
      f"{server.stats.avg_queue_length(env.now):>12.4f} {'—':>12}")
print(f"{'Max queue length':<30} "
      f"{server.stats.max_queue_length:>12d}")
print("=" * 60)
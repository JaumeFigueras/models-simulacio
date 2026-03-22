#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
M/M/1 Queue Model
==================

A classic single-server queueing system where:

- **M** (arrivals): Poisson process → inter-arrival times are exponential
  with mean ``MEAN_IAT`` minutes.
- **M** (service): Service times are exponential with mean
  ``MEAN_SERVICE`` minutes.
- **1** (servers): A single server (resource capacity = 1).

Theoretical steady-state results (ρ = λ/μ < 1):

- Traffic intensity:   ρ = MEAN_SERVICE / MEAN_IAT
- Avg entities in sys: L = ρ / (1 − ρ)
- Avg time in sys:     W = 1 / (μ − λ)
- Avg queue length:    Lq = ρ² / (1 − ρ)
- Avg wait in queue:   Wq = ρ / (μ − λ)

With MEAN_IAT = 5.0 and MEAN_SERVICE = 4.0:

    ρ  = 4/5 = 0.80
    L  = 0.80 / 0.20 = 4.0 entities
    W  = 1 / (1/4 − 1/5) = 1 / 0.05 = 20.0 minutes
    Lq = 0.64 / 0.20 = 3.2 entities
    Wq = 0.80 / (1/4 − 1/5) = 0.80 / 0.05 = 16.0 minutes
"""

import random

import simpy

from simpy_extensions.process_flow import Arrival, Process, Delete, Resource

# ── Parameters ───────────────────────────────────────────────────────
MEAN_IAT = 5.0          # Mean inter-arrival time (minutes)
MEAN_SERVICE = 4.0      # Mean service time (minutes)
SIM_TIME = 100_000      # Simulation horizon (minutes) — long for accuracy
RANDOM_SEED = 42         # Reproducibility

# ── Theoretical steady-state values ─────────────────────────────────
lam = 1.0 / MEAN_IAT              # Arrival rate λ
mu = 1.0 / MEAN_SERVICE           # Service rate μ
rho = lam / mu                    # Traffic intensity ρ
L_theory = rho / (1 - rho)        # Avg number in system
W_theory = 1 / (mu - lam)         # Avg time in system
Lq_theory = rho ** 2 / (1 - rho)  # Avg queue length
Wq_theory = rho / (mu - lam)      # Avg wait in queue

# ── Build model ──────────────────────────────────────────────────────
random.seed(RANDOM_SEED)
env = simpy.Environment()

# Single server (capacity = 1) → the "1" in M/M/1
server = Resource(env, name='Server', capacity=1)

# Arrival block: exponential inter-arrival times
source = Arrival(
    env,
    name='Arrivals',
    inter_arrival_time=lambda: random.expovariate(1.0 / MEAN_IAT),
)

# Process block: exponential service times (receives Entity as argument)
station = Process(
    env,
    name='Service',
    resource=server,
    service_time=lambda entity: random.expovariate(1.0 / MEAN_SERVICE),
)

# Delete block
sink = Delete(env, name='Exit')

# Connect the flow: Arrival → Process → Delete
source.next_block = station
station.next_block = sink

# ── Run ──────────────────────────────────────────────────────────────
env.run(until=SIM_TIME)

# ── Results ──────────���───────────────────────────────────────────────
print("=" * 60)
print("M/M/1 Queue Simulation Results")
print("=" * 60)
print(f"Simulation time:      {SIM_TIME:,} minutes")
print(f"Random seed:          {RANDOM_SEED}")
print(f"Mean IAT:             {MEAN_IAT} min (λ = {lam:.4f})")
print(f"Mean service:         {MEAN_SERVICE} min (μ = {mu:.4f})")
print(f"Traffic intensity ρ:  {rho:.4f}")
print()

print("--- Simulation vs Theory ---")
print(f"{'Metric':<25} {'Simulation':>12} {'Theory':>12}")
print("-" * 51)
print(f"{'Server utilization':<25} "
      f"{server.stats.utilization(env.now):>12.4f} "
      f"{rho:>12.4f}")
print(f"{'Avg time in system (W)':<25} "
      f"{sink.avg_system_time():>12.4f} "
      f"{W_theory:>12.4f}")
print(f"{'Avg wait in queue (Wq)':<25} "
      f"{server.stats.avg_wait_time():>12.4f} "
      f"{Wq_theory:>12.4f}")
print(f"{'Avg queue length (Lq)':<25} "
      f"{server.stats.avg_queue_length(env.now):>12.4f} "
      f"{Lq_theory:>12.4f}")
print(f"{'Max queue length':<25} "
      f"{server.stats.max_queue_length:>12d}")
print()
print(f"Entities created:     {source.entities_created:,}")
print(f"Entities deleted:     {sink.entities_deleted:,}")
print("=" * 60)
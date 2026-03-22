#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import simpy
import random

from simpy_extensions.process_flow import Arrival, Process, Delete, Resource

env = simpy.Environment()

# Define resources (like AnyLogic ResourcePool)
drill = Resource(env, name='Drill', capacity=2)

# Build the flow: Arrival → Process → Delete
source = Arrival(env, name='Part Arrivals',
                 inter_arrival_time=lambda: random.expovariate(1 / 5.0))
station = Process(env, name='Drilling Station',
                  resource=drill,
                  service_time=lambda: random.uniform(3.0, 7.0))
sink = Delete(env, name='Exit')

# Connect the flow (like drawing arrows on a canvas)
source.next_block = station
station.next_block = sink

# Run
env.run(until=480)

# Results
print(f"Entities created:   {source.entities_created}")
print(f"Entities deleted:   {sink.entities_deleted}")
print(f"Avg system time:    {sink.avg_system_time():.2f}")
print(f"Drill utilization:  {drill.stats.utilization(env.now):.2%}")
print(f"Avg queue length:   {drill.stats.avg_queue_length(env.now):.2f}")
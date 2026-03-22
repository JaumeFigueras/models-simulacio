#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import simpy
import pytest

from simpy_extensions.process_flow.entity import Entity
from simpy_extensions.process_flow.resource import Resource
from simpy_extensions.process_flow.arrival import Arrival
from simpy_extensions.process_flow.process import Process
from simpy_extensions.process_flow.delete import Delete


class TestSingleTypePipeline:
    """Integration: Arrival → Process → Delete with one entity type."""

    def test_full_pipeline(self, env):
        # IAT=5, service=3, 4 entities
        res = Resource(env, name="Machine", capacity=1)
        sink = Delete(env, name="Exit")
        station = Process(
            env, name="Work", resource=res, service_time=lambda e: 3.0, next_block=sink
        )
        source = Arrival(
            env,
            name="Source",
            inter_arrival_time=lambda: 5.0,
            max_entities=4,
            next_block=station,
        )
        env.run()

        assert source.entities_created == 4
        assert station.entities_processed == 4
        assert sink.entities_deleted == 4

        # Entity 1: arrives t=5, service 5→8, deleted at 8, system_time=3
        # Entity 2: arrives t=10, service 10→13, deleted at 13, system_time=3
        # Entity 3: arrives t=15, service 15→18, deleted at 18, system_time=3
        # Entity 4: arrives t=20, service 20→23, deleted at 23, system_time=3
        # No queuing because IAT (5) > service (3) with 1 server
        for entity in sink.deleted_entities:
            assert entity.system_time() == pytest.approx(3.0)

        assert sink.avg_system_time() == pytest.approx(3.0)

    def test_pipeline_with_queuing(self, env):
        """IAT < service time → entities queue up."""
        res = Resource(env, name="Machine", capacity=1)
        sink = Delete(env, name="Exit")
        station = Process(
            env, name="Work", resource=res, service_time=lambda e: 5.0, next_block=sink
        )
        source = Arrival(
            env,
            name="Source",
            inter_arrival_time=lambda: 2.0,
            max_entities=3,
            next_block=station,
        )
        env.run()

        assert source.entities_created == 3
        assert sink.entities_deleted == 3

        # Entity 1: arrives t=2, service 2→7
        # Entity 2: arrives t=4, waits until t=7, service 7→12
        # Entity 3: arrives t=6, waits until t=12, service 12→17
        times = [e.deletion_time for e in sink.deleted_entities]
        assert times[0] == pytest.approx(7.0)
        assert times[1] == pytest.approx(12.0)
        assert times[2] == pytest.approx(17.0)


class TestTwoTypePipeline:
    """Integration: Two Arrivals → one Process (dict) → one Delete."""

    def test_two_entity_types(self, env):
        res = Resource(env, name="Machine", capacity=1)
        sink = Delete(env, name="Exit")
        station = Process(
            env,
            name="Work",
            resource=res,
            service_time={
                "TypeA": lambda: 2.0,
                "TypeB": lambda: 4.0,
            },
            next_block=sink,
        )
        source_a = Arrival(
            env,
            name="SourceA",
            inter_arrival_time=lambda: 10.0,
            entity_type="TypeA",
            max_entities=2,
            next_block=station,
        )
        source_b = Arrival(
            env,
            name="SourceB",
            inter_arrival_time=lambda: 10.0,
            entity_type="TypeB",
            max_entities=2,
            next_block=station,
        )
        env.run()

        assert source_a.entities_created == 2
        assert source_b.entities_created == 2
        assert sink.entities_deleted == 4

        # Verify both types are present
        types_seen = {e.entity_type for e in sink.deleted_entities}
        assert types_seen == {"TypeA", "TypeB"}

        # All entity IDs are unique
        ids = [e.entity_id for e in sink.deleted_entities]
        assert len(set(ids)) == 4

    def test_two_types_different_service_times(self, env):
        """With capacity=2, both types process in parallel, confirming
        different service durations."""
        res = Resource(env, name="Machine", capacity=2)
        sink = Delete(env, name="Exit")
        station = Process(
            env,
            name="Work",
            resource=res,
            service_time={
                "TypeA": lambda: 2.0,
                "TypeB": lambda: 6.0,
            },
            next_block=sink,
        )
        # Both arrive at the same time (t=10), capacity=2 → parallel
        source_a = Arrival(
            env,
            name="SourceA",
            inter_arrival_time=lambda: 10.0,
            entity_type="TypeA",
            max_entities=1,
            next_block=station,
        )
        source_b = Arrival(
            env,
            name="SourceB",
            inter_arrival_time=lambda: 10.0,
            entity_type="TypeB",
            max_entities=1,
            next_block=station,
        )
        env.run()

        type_a_entities = [
            e for e in sink.deleted_entities if e.entity_type == "TypeA"
        ]
        type_b_entities = [
            e for e in sink.deleted_entities if e.entity_type == "TypeB"
        ]

        assert len(type_a_entities) == 1
        assert len(type_b_entities) == 1

        # Both created at t=10; TypeA served 2 → deleted at 12; TypeB served 6 → deleted at 16
        assert type_a_entities[0].deletion_time == pytest.approx(12.0)
        assert type_b_entities[0].deletion_time == pytest.approx(16.0)

        # System times should differ
        assert type_a_entities[0].system_time() == pytest.approx(2.0)
        assert type_b_entities[0].system_time() == pytest.approx(6.0)


class TestResourceUtilization:
    """Integration: verify resource utilization after a full run."""

    def test_utilization_calculation(self, env):
        res = Resource(env, name="Machine", capacity=1)
        sink = Delete(env, name="Exit")
        station = Process(
            env, name="Work", resource=res, service_time=lambda e: 5.0, next_block=sink
        )
        source = Arrival(
            env,
            name="Source",
            inter_arrival_time=lambda: 10.0,
            max_entities=2,
            next_block=station,
        )
        env.run()
        # Entities at t=10 and t=20. Service: 10→15 and 20→25. Total busy=10
        # Sim ends at t=25. Utilization = 10/25 = 0.4
        assert res.stats.utilization(env.now) == pytest.approx(0.4)
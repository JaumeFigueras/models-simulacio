#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import simpy
import pytest

from simpy_extensions.process_flow.entity import Entity
from simpy_extensions.process_flow.resource import Resource
from simpy_extensions.process_flow.process import Process
from simpy_extensions.process_flow.delete import Delete


class TestProcessServiceTimeCallable:
    """Tests for Process with a single callable service_time."""

    def test_callable_service_time(self, env):
        res = Resource(env, name="Machine", capacity=1)
        sink = Delete(env, name="Sink")
        station = Process(
            env,
            name="Station",
            resource=res,
            service_time=lambda e: 5.0,
            next_block=sink,
        )
        entity = Entity(entity_id=1, creation_time=0.0)
        env.process(station.handle(entity))
        env.run()
        assert station.entities_processed == 1
        assert sink.entities_deleted == 1
        # Entity created at 0, served for 5 → deleted at 5
        assert entity.deletion_time == 5.0

    def test_callable_inspects_entity_type(self, env):
        res = Resource(env, name="Machine", capacity=1)
        sink = Delete(env, name="Sink")

        def svc(entity):
            if entity.entity_type == "Fast":
                return 2.0
            return 8.0

        station = Process(
            env, name="Station", resource=res, service_time=svc, next_block=sink
        )
        fast = Entity(entity_id=1, creation_time=0.0, entity_type="Fast")
        slow = Entity(entity_id=2, creation_time=0.0, entity_type="Slow")
        env.process(station.handle(fast))
        env.process(station.handle(slow))
        env.run()
        # Fast finishes at t=2, Slow finishes at t=2+8=10
        assert fast.deletion_time == 2.0
        assert slow.deletion_time == 10.0


class TestProcessServiceTimeDict:
    """Tests for Process with a dictionary service_time."""

    def test_dict_dispatches_by_entity_type(self, env):
        res = Resource(env, name="Machine", capacity=1)
        sink = Delete(env, name="Sink")
        station = Process(
            env,
            name="Station",
            resource=res,
            service_time={
                "TypeA": lambda: 3.0,
                "TypeB": lambda: 7.0,
            },
            next_block=sink,
        )
        ea = Entity(entity_id=1, creation_time=0.0, entity_type="TypeA")
        eb = Entity(entity_id=2, creation_time=0.0, entity_type="TypeB")
        env.process(station.handle(ea))
        env.process(station.handle(eb))
        env.run()
        # TypeA: served 3 → deleted at 3; TypeB: served 7 → deleted at 3+7=10
        assert ea.deletion_time == 3.0
        assert eb.deletion_time == 10.0

    def test_dict_falls_back_to_default(self, env):
        res = Resource(env, name="Machine", capacity=1)
        sink = Delete(env, name="Sink")
        station = Process(
            env,
            name="Station",
            resource=res,
            service_time={
                "TypeA": lambda: 3.0,
                "default": lambda: 6.0,
            },
            next_block=sink,
        )
        entity = Entity(entity_id=1, creation_time=0.0, entity_type="Unknown")
        env.process(station.handle(entity))
        env.run()
        assert entity.deletion_time == 6.0

    def test_dict_raises_value_error_no_match(self, env):
        res = Resource(env, name="Machine", capacity=1)
        station = Process(
            env,
            name="Station",
            resource=res,
            service_time={"TypeA": lambda: 3.0},
        )
        entity = Entity(entity_id=1, creation_time=0.0, entity_type="TypeX")
        with pytest.raises(ValueError, match="no service-time entry"):
            station._resolve_service_time(entity)


class TestProcessTiming:
    """Tests for seize-delay-release timing and forwarding."""

    def test_seize_delay_release_timing(self, env):
        res = Resource(env, name="Machine", capacity=1)
        sink = Delete(env, name="Sink")
        station = Process(
            env,
            name="Station",
            resource=res,
            service_time=lambda e: 4.0,
            next_block=sink,
        )
        e1 = Entity(entity_id=1, creation_time=0.0)
        e2 = Entity(entity_id=2, creation_time=0.0)
        env.process(station.handle(e1))
        env.process(station.handle(e2))
        env.run()
        # e1: service 0→4; e2 waits, service 4→8
        assert e1.deletion_time == 4.0
        assert e2.deletion_time == 8.0

    def test_no_next_block(self, env):
        res = Resource(env, name="Machine", capacity=1)
        station = Process(
            env,
            name="Station",
            resource=res,
            service_time=lambda e: 3.0,
        )
        entity = Entity(entity_id=1, creation_time=0.0)
        env.process(station.handle(entity))
        env.run()
        assert station.entities_processed == 1
        assert entity.deletion_time is None  # not forwarded to Delete

    def test_entities_processed_counter(self, env):
        res = Resource(env, name="Machine", capacity=1)
        station = Process(
            env,
            name="Station",
            resource=res,
            service_time=lambda e: 1.0,
        )
        for i in range(5):
            e = Entity(entity_id=i + 1, creation_time=0.0)
            env.process(station.handle(e))
        env.run()
        assert station.entities_processed == 5


class TestProcessResourceStats:
    """Tests that resource stats are updated during processing."""

    def test_utilization_after_processing(self, env):
        res = Resource(env, name="Machine", capacity=1)
        station = Process(
            env,
            name="Station",
            resource=res,
            service_time=lambda e: 5.0,
        )
        entity = Entity(entity_id=1, creation_time=0.0)
        env.process(station.handle(entity))
        env.run()
        # Busy 5 out of 5 time units
        assert res.stats.utilization(env.now) == pytest.approx(1.0)

    def test_wait_time_recorded(self, env):
        res = Resource(env, name="Machine", capacity=1)
        station = Process(
            env,
            name="Station",
            resource=res,
            service_time=lambda e: 3.0,
        )
        e1 = Entity(entity_id=1, creation_time=0.0)
        e2 = Entity(entity_id=2, creation_time=0.0)
        env.process(station.handle(e1))
        env.process(station.handle(e2))
        env.run()
        # e1 waits 0, e2 waits 3 → avg = 1.5
        assert res.stats.avg_wait_time() == pytest.approx(1.5)


class TestProcessRepr:
    """Tests for Process.__repr__."""

    def test_repr(self, env):
        res = Resource(env, name="Drill", capacity=2)
        station = Process(
            env,
            name="Drilling",
            resource=res,
            service_time=lambda e: 5.0,
        )
        result = repr(station)
        assert "name='Drilling'" in result
        assert "resource='Drill'" in result
        assert "entities_processed=0" in result
        
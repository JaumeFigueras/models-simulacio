#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import simpy
import pytest

from simpy_extensions.process_flow.entity import Entity
from simpy_extensions.process_flow.delete import Delete


class TestDeleteHandle:
    """Tests for Delete.handle() behaviour."""

    def test_sets_deletion_time(self, env):
        sink = Delete(env, name="Sink")
        entity = Entity(entity_id=1, creation_time=0.0)
        # Advance env to t=10 then handle
        env.run(until=10)
        env.process(sink.handle(entity))
        env.run()
        assert entity.deletion_time == 10.0

    def test_increments_counter(self, env):
        sink = Delete(env, name="Sink")
        for i in range(4):
            e = Entity(entity_id=i + 1, creation_time=0.0)
            env.process(sink.handle(e))
        env.run()
        assert sink.entities_deleted == 4

    def test_keeps_entities_by_default(self, env):
        sink = Delete(env, name="Sink")
        e = Entity(entity_id=1, creation_time=0.0)
        env.process(sink.handle(e))
        env.run()
        assert len(sink.deleted_entities) == 1
        assert sink.deleted_entities[0] is e

    def test_does_not_keep_when_disabled(self, env):
        sink = Delete(env, name="Sink", keep_entities=False)
        e = Entity(entity_id=1, creation_time=0.0)
        env.process(sink.handle(e))
        env.run()
        assert sink.entities_deleted == 1
        assert len(sink.deleted_entities) == 0


class TestDeleteSystemTime:
    """Tests for Delete system-time tracking."""

    def test_total_system_time(self, env):
        sink = Delete(env, name="Sink")
        e1 = Entity(entity_id=1, creation_time=0.0)
        e2 = Entity(entity_id=2, creation_time=5.0)
        # Delete both at t=10
        env.run(until=10)
        env.process(sink.handle(e1))
        env.process(sink.handle(e2))
        env.run()
        # e1: 10-0=10, e2: 10-5=5 → total=15
        assert sink.total_system_time == pytest.approx(15.0)

    def test_avg_system_time_no_entities(self, env):
        sink = Delete(env, name="Sink")
        assert sink.avg_system_time() == 0.0

    def test_avg_system_time_correct(self, env):
        sink = Delete(env, name="Sink")
        e1 = Entity(entity_id=1, creation_time=0.0)
        e2 = Entity(entity_id=2, creation_time=5.0)
        env.run(until=10)
        env.process(sink.handle(e1))
        env.process(sink.handle(e2))
        env.run()
        # (10 + 5) / 2 = 7.5
        assert sink.avg_system_time() == pytest.approx(7.5)


class TestDeleteRepr:
    """Tests for Delete.__repr__."""

    def test_repr_initial(self, env):
        sink = Delete(env, name="Exit")
        assert repr(sink) == "Delete(name='Exit', entities_deleted=0)"

    def test_repr_after_deletions(self, env):
        sink = Delete(env, name="Exit")
        e = Entity(entity_id=1, creation_time=0.0)
        env.process(sink.handle(e))
        env.run()
        assert "entities_deleted=1" in repr(sink)
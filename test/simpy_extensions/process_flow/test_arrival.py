#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import simpy
import pytest

from simpy_extensions.process_flow.entity import Entity
from simpy_extensions.process_flow.arrival import Arrival
from simpy_extensions.process_flow.delete import Delete


class TestArrivalCreation:
    """Tests for Arrival construction and attribute storage."""

    def test_attributes_stored(self, env):
        source = Arrival(env, name="Source", inter_arrival_time=lambda: 5.0)
        assert source.name == "Source"
        assert source.entity_type == "default"
        assert source.max_entities is None
        assert source.entity_name_prefix == "Entity"
        assert source.entities_created == 0
        assert source.next_block is None

    def test_custom_entity_type(self, env):
        source = Arrival(
            env, name="Source", inter_arrival_time=lambda: 5.0, entity_type="TypeA"
        )
        assert source.entity_type == "TypeA"

    def test_custom_prefix(self, env):
        sink = Delete(env, name="Sink")
        source = Arrival(
            env,
            name="Source",
            inter_arrival_time=lambda: 5.0,
            entity_name_prefix="Part",
            max_entities=1,
            next_block=sink,
        )
        env.run()
        assert sink.deleted_entities[0].name.startswith("Part-")


class TestArrivalEntityGeneration:
    """Tests for entity creation logic in Arrival."""

    def test_max_entities_respected(self, env):
        sink = Delete(env, name="Sink")
        source = Arrival(
            env,
            name="Source",
            inter_arrival_time=lambda: 1.0,
            max_entities=3,
            next_block=sink,
        )
        env.run()
        assert source.entities_created == 3
        assert sink.entities_deleted == 3

    def test_entities_created_counter(self, env):
        source = Arrival(
            env, name="Source", inter_arrival_time=lambda: 10.0, max_entities=5
        )
        env.run()
        assert source.entities_created == 5

    def test_entity_type_stamped(self, env):
        sink = Delete(env, name="Sink")
        source = Arrival(
            env,
            name="Source",
            inter_arrival_time=lambda: 1.0,
            entity_type="Rush",
            max_entities=2,
            next_block=sink,
        )
        env.run()
        for entity in sink.deleted_entities:
            assert entity.entity_type == "Rush"

    def test_no_next_block(self, env):
        """Arrival without a next_block should still create entities."""
        source = Arrival(
            env, name="Source", inter_arrival_time=lambda: 1.0, max_entities=3
        )
        env.run()
        assert source.entities_created == 3


class TestArrivalTiming:
    """Tests for inter-arrival time correctness."""

    def test_deterministic_arrival_times(self, env):
        sink = Delete(env, name="Sink")
        source = Arrival(
            env,
            name="Source",
            inter_arrival_time=lambda: 5.0,
            max_entities=3,
            next_block=sink,
        )
        env.run()
        # Entities arrive at t=5, t=10, t=15
        assert sink.deleted_entities[0].creation_time == 5.0
        assert sink.deleted_entities[1].creation_time == 10.0
        assert sink.deleted_entities[2].creation_time == 15.0

    def test_unlimited_entities_run_until(self, env):
        """Without max_entities, entities are created until sim ends."""
        source = Arrival(
            env, name="Source", inter_arrival_time=lambda: 10.0
        )
        env.run(until=35)
        # Arrivals at t=10, t=20, t=30 → 3 entities
        assert source.entities_created == 3


class TestArrivalUniqueIds:
    """Tests for globally unique entity IDs across multiple Arrivals."""

    def test_unique_ids_across_arrivals(self, env):
        sink = Delete(env, name="Sink")
        source_a = Arrival(
            env,
            name="A",
            inter_arrival_time=lambda: 2.0,
            entity_type="TypeA",
            max_entities=3,
            next_block=sink,
        )
        source_b = Arrival(
            env,
            name="B",
            inter_arrival_time=lambda: 2.0,
            entity_type="TypeB",
            max_entities=3,
            next_block=sink,
        )
        env.run()
        ids = [e.entity_id for e in sink.deleted_entities]
        assert len(ids) == 6
        assert len(set(ids)) == 6  # all unique


class TestArrivalRepr:
    """Tests for Arrival.__repr__."""

    def test_repr(self, env):
        source = Arrival(
            env,
            name="Parts",
            inter_arrival_time=lambda: 5.0,
            entity_type="TypeA",
        )
        result = repr(source)
        assert "name='Parts'" in result
        assert "entity_type='TypeA'" in result
        assert "entities_created=0" in result
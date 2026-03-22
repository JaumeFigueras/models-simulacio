#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pytest

from simpy_extensions.process_flow.entity import Entity


class TestEntityConstruction:
    """Tests for Entity __init__ and default values."""

    def test_default_construction(self):
        e = Entity(entity_id=1, creation_time=0.0)
        assert e.entity_id == 1
        assert e.entity_type == "default"
        assert e.name == "Entity-1"
        assert e.creation_time == 0.0
        assert e.deletion_time is None
        assert e.attributes == {}

    def test_custom_construction(self):
        attrs = {"priority": "high", "weight": 3.5}
        e = Entity(
            entity_id=42,
            creation_time=10.0,
            entity_type="TypeA",
            name="CustomPart",
            attributes=attrs,
        )
        assert e.entity_id == 42
        assert e.entity_type == "TypeA"
        assert e.name == "CustomPart"
        assert e.creation_time == 10.0
        assert e.deletion_time is None
        assert e.attributes is attrs
        assert e.attributes["priority"] == "high"
        assert e.attributes["weight"] == 3.5

    def test_default_entity_type(self):
        e = Entity(entity_id=1, creation_time=0.0)
        assert e.entity_type == "default"

    def test_auto_generated_name(self):
        e = Entity(entity_id=7, creation_time=0.0)
        assert e.name == "Entity-7"

    def test_attributes_empty_when_none_provided(self):
        e = Entity(entity_id=1, creation_time=0.0)
        assert isinstance(e.attributes, dict)
        assert len(e.attributes) == 0

    def test_attributes_are_independent(self):
        """Two entities with no attributes should have independent dicts."""
        e1 = Entity(entity_id=1, creation_time=0.0)
        e2 = Entity(entity_id=2, creation_time=0.0)
        e1.attributes["color"] = "red"
        assert "color" not in e2.attributes


class TestEntitySystemTime:
    """Tests for Entity.system_time()."""

    def test_system_time_none_before_deletion(self):
        e = Entity(entity_id=1, creation_time=5.0)
        assert e.system_time() is None

    def test_system_time_after_deletion(self):
        e = Entity(entity_id=1, creation_time=5.0)
        e.deletion_time = 15.0
        assert e.system_time() == 10.0

    def test_system_time_zero_duration(self):
        e = Entity(entity_id=1, creation_time=5.0)
        e.deletion_time = 5.0
        assert e.system_time() == 0.0


class TestEntityIdGeneration:
    """Tests for Entity.generate_id() and reset_id_counter()."""

    def test_generate_id_sequential(self):
        id1 = Entity.generate_id()
        id2 = Entity.generate_id()
        id3 = Entity.generate_id()
        assert id1 == 1
        assert id2 == 2
        assert id3 == 3

    def test_reset_id_counter(self):
        Entity.generate_id()
        Entity.generate_id()
        Entity.reset_id_counter()
        assert Entity.generate_id() == 1

    def test_generate_id_starts_at_one(self):
        assert Entity.generate_id() == 1


class TestEntityRepr:
    """Tests for Entity.__repr__."""

    def test_repr_default(self):
        e = Entity(entity_id=1, creation_time=0.0)
        result = repr(e)
        assert "entity_id=1" in result
        assert "entity_type='default'" in result
        assert "name='Entity-1'" in result
        assert "creation_time=0.0" in result

    def test_repr_custom(self):
        e = Entity(entity_id=5, creation_time=3.0, entity_type="Rush", name="Part-5")
        result = repr(e)
        assert "entity_id=5" in result
        assert "entity_type='Rush'" in result
        assert "name='Part-5'" in result
        assert "creation_time=3.0" in result
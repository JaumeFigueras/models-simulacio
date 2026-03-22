#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import simpy
import pytest

from simpy_extensions.process_flow.resource import Resource
from simpy_extensions.statistics.resource import ResourceStats


class TestResourceConstruction:
    """Tests for Resource __init__ and default values."""

    def test_default_capacity(self, env):
        r = Resource(env, name="Drill")
        assert r.capacity == 1

    def test_custom_capacity(self, env):
        r = Resource(env, name="Drill", capacity=3)
        assert r.capacity == 3

    def test_name_stored(self, env):
        r = Resource(env, name="Lathe")
        assert r.name == "Lathe"

    def test_env_reference(self, env):
        r = Resource(env, name="Drill")
        assert r.env is env

    def test_simpy_resource_type(self, env):
        r = Resource(env, name="Drill", capacity=2)
        assert isinstance(r.simpy_resource, simpy.Resource)

    def test_simpy_resource_capacity(self, env):
        r = Resource(env, name="Drill", capacity=4)
        assert r.simpy_resource.capacity == 4

    def test_stats_instance(self, env):
        r = Resource(env, name="Drill")
        assert isinstance(r.stats, ResourceStats)


class TestResourceRepr:
    """Tests for Resource.__repr__."""

    def test_repr_default_capacity(self, env):
        r = Resource(env, name="Drill")
        assert repr(r) == "Resource(name='Drill', capacity=1)"

    def test_repr_custom_capacity(self, env):
        r = Resource(env, name="Lathe", capacity=5)
        assert repr(r) == "Resource(name='Lathe', capacity=5)"
        
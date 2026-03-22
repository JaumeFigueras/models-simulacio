#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys

import pytest
import simpy

# Add src/ to the Python path so that `simpy_extensions` is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from simpy_extensions.process_flow.entity import Entity


@pytest.fixture
def env():
    """Provide a fresh SimPy environment for each test."""
    return simpy.Environment()


@pytest.fixture(autouse=True)
def reset_entity_ids():
    """Reset the Entity class-level ID counter before every test."""
    Entity.reset_id_counter()
    yield
    Entity.reset_id_counter()
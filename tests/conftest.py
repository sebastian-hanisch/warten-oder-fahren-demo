"""Gemeinsame Fixtures: das Linienbeispiel von Hand (DEMO-PLAYBOOK §1b)."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import wof_model as M  # noqa: E402


@pytest.fixture
def line():
    """Linienbeispiel: Depot bei 0; Auftrag 1 bei x = 10 (Eingang 0, Frist 60), Auftrag 2 bei x = 20 (Eingang 15, Frist 75); Last 1; Kapazität 8; Geschwindigkeit 1."""
    return M.line_example(75.0)


@pytest.fixture
def line_tight():
    """Wie das Linienbeispiel, aber Frist 35 für Auftrag 2 (späteste Abfahrt allein 15)."""
    return M.line_example(35.0)

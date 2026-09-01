# tests/test_agent_management.py
from screens.agent_management import _partition_agents


def test_partition_keeps_original_indices():
    """Indices must survive the split — the delete button pops by original index."""
    agents = [{"id": "david"}, {"id": "tom", "active": False}, {"id": "perry"}]
    active, inactive = _partition_agents(agents)

    assert [i for i, _ in active] == [0, 2]
    assert [i for i, _ in inactive] == [1]


def test_partition_treats_missing_active_flag_as_active():
    agents = [{"id": "legacy"}]
    active, inactive = _partition_agents(agents)

    assert [a["id"] for _, a in active] == ["legacy"]
    assert inactive == []


def test_partition_all_inactive():
    agents = [{"id": "tom", "active": False}, {"id": "dana", "active": False}]
    active, inactive = _partition_agents(agents)

    assert active == []
    assert [i for i, _ in inactive] == [0, 1]

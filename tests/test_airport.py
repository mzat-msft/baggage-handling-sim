import pytest

from sim.airport import Gate, Point


dist_points = [
    ((Point(0, 0), Point(0, 0)), 0),
    ((Point(1, 0), Point(0, 0)), 1),
    ((Point(0, 1), Point(0, 0)), 1),
]


@pytest.mark.parametrize("points, distance", dist_points)
def test_dist_points(points, distance):
    assert points[0].distance(points[1]) == distance
    assert points[1].distance(points[0]) == distance


dist_gates = [
    ((Gate('a', 0, 0), Gate('b', 0, 0)), 0),
    ((Gate('a', 0, 0), Gate('b', 1, 0)), 1),
    ((Gate('a', 1, 0), Gate('b', 1, 0)), 0),
]


@pytest.mark.parametrize("gates, distance", dist_gates)
def test_dist_gates(gates, distance):
    assert gates[0].distance(gates[1]) == distance
    assert gates[1].distance(gates[0]) == distance

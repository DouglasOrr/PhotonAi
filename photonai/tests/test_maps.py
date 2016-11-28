from .. import schema, maps
from . import test_schema
import itertools as it
import numpy as np
from nose_parameterized import parameterized
from fastavro.writer import validate


all_maps = [
    (maps.empty,),
    (maps.singleton,),
    (maps.binary,),
    (maps.orbital,),
]


@parameterized(all_maps)
def test_validate(spec):
    m = spec.Map(100)
    assert validate(m.space, schema.Space.CREATE)

    for planet in m.planets:
        assert validate(planet, schema.Planet.CREATE)

    for n in [0, 10]:
        assert validate(m.ship(test_schema.Controller.CREATE),
                        schema.Ship.CREATE)


@parameterized(all_maps)
def test_deterministic(spec):
    reference = spec.Map(100)
    space = reference.space
    planets = reference.planets
    ships = [reference.ship(test_schema.Controller.CREATE)
             for _ in range(10)]
    for x in range(10):
        m = spec.Map(100)
        assert m.space == space
        assert m.planets == planets
        m_ships = [m.ship(test_schema.Controller.CREATE)
                   for _ in range(10)]
        assert m_ships == ships


def test_binary_subdivision():
    expected = [
        0,
        1/2.,
        1/4., 3/4.,
        1/8., 3/8., 5/8., 7/8.,
        1/16., 3/16., 5/16., 7/16., 9/16., 11/16., 13/16., 15/16.
    ]
    np.testing.assert_allclose(
        list(it.islice(maps.common.binary_subdivision(), len(expected))),
        expected)

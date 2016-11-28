from .. import schema, maps
from . import test_schema
import itertools as it
import numpy as np
from nose_parameterized import parameterized
from fastavro.writer import validate


@parameterized([
    (maps.empty,),
    (maps.singleton,),
    (maps.binary,),
    (maps.orbital,),
])
def test_validate(spec):
    m = spec.Map(100)
    assert validate(m.space, schema.Space.CREATE)

    for planet in m.planets:
        assert validate(planet, schema.Planet.CREATE)

    for n in [0, 10]:
        assert validate(m.ship(test_schema.Controller.CREATE),
                        schema.Ship.CREATE)


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

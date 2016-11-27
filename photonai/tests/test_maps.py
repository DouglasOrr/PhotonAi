from .. import schema, maps
from . import test_schema
from nose_parameterized import parameterized
from fastavro.writer import validate


@parameterized([
    (maps.singleton,),
    (maps.empty,),
    (maps.binary,),
])
def test_validate(spec):
    m = spec.Map(100)
    assert validate(m.space, schema.Space.CREATE)

    for planet in m.planets:
        assert validate(planet, schema.Body.CREATE)

    for n in [0, 1]:
        assert validate(m.ship(test_schema.Controller.CREATE),
                        schema.Ship.CREATE)

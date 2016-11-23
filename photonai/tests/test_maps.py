from ..maps import singleton
from .. import schema
from . import test_schema
from fastavro.writer import validate


def test_singleton():
    assert validate(singleton.space, schema.Space.CREATE)

    for planet in singleton.planets:
        assert validate(planet, schema.Body.CREATE)

    for n in [0, 1]:
        assert validate(singleton.ship(n, test_schema.Controller.CREATE),
                        schema.Ship.CREATE)

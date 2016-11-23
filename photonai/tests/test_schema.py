from .. import schema
from fastavro.writer import validate
from nose_parameterized import parameterized
import io
import fastavro


# Data also useful for other tests

VECTOR = dict(x=100., y=-23.4)


class Space:
    CREATE = dict(dimensions=VECTOR,
                  gravity=0.12)


class Body:
    STATE = dict(position=VECTOR,
                 velocity=VECTOR,
                 orientation=2.5)

    CREATE = dict(radius=60.3,
                  mass=14.4,
                  state=STATE)


class Weapon:
    STATE = dict(reload=1.2,
                 temperature=18.3)

    CREATE = dict(max_reload=0.1,
                  max_temperature=19.6,
                  temperature_decay=0.25,
                  speed=120.5,
                  time_to_live=0.46,
                  state=STATE)


class Controller:
    STATE = dict(fire=False,
                 rotate=-0.5,
                 thrust=0.9)

    CREATE = dict(name='test_controller',
                  version=123,
                  state=STATE)


class Ship:
    STATE = dict(body=Body.STATE,
                 weapon=Weapon.STATE,
                 controller=Controller.STATE)

    CREATE = dict(body=Body.CREATE,
                  weapon=Weapon.CREATE,
                  controller=Controller.CREATE,
                  max_thrust=40.3,
                  max_rotate=15.3)


class Pellet:
    STATE = dict(body=Body.STATE,
                 time_to_live=0.38)

    CREATE = dict(body=Body.CREATE,
                  time_to_live=0.46)


class Object:
    DESTROY = dict()

    EVENTS = [dict(id=2468,
                   data=data)
              for data in [Body.CREATE, Body.STATE,
                           Ship.CREATE, Ship.STATE,
                           Pellet.CREATE, Pellet.STATE,
                           DESTROY]]


def almost_equal(x, y):
    '''Structural equality with approximate floating point equality.
    '''
    if type(x) != type(y):
        return False
    if isinstance(x, dict):
        return (x.keys() == y.keys() and
                all(almost_equal(x[k], y[k]) for k in x))
    elif isinstance(x, list):
        return (len(x) == len(y) and
                all(almost_equal(a, b) for a, b in zip(x, y)))
    elif isinstance(x, float):
        return abs(x - y) < 1e-4
    else:
        return x == y


STEPS = [dict(clock=300,
              duration=0.01,
              data=data)
         for data in [Space.CREATE, Object.EVENTS]]


@parameterized([
    (schema.VECTOR, VECTOR),
    (schema.Space.CREATE, Space.CREATE),
    (schema.Body.STATE, Body.STATE),
    (schema.Body.CREATE, Body.CREATE),
    (schema.Weapon.STATE, Weapon.STATE),
    (schema.Weapon.CREATE, Weapon.CREATE),
    (schema.Controller.STATE, Controller.STATE),
    (schema.Controller.CREATE, Controller.CREATE),
    (schema.Ship.STATE, Ship.STATE),
    (schema.Ship.CREATE, Ship.CREATE),
    (schema.Pellet.STATE, Pellet.STATE),
    (schema.Pellet.CREATE, Pellet.CREATE),
    (schema.Object.DESTROY, Object.DESTROY),
] + [
    (schema.Object.EVENT, e) for e in Object.EVENTS
] + [
    (schema.STEP, s) for s in STEPS
])
def test_valid(obj_schema, obj):
    assert validate(obj, obj_schema), \
        'Did not match %s.%s' % (obj_schema['namespace'], obj_schema['name'])

    # Round-trip encode using Avro, then decode
    # - we should end up with the same data
    with io.BytesIO() as f:
        fastavro.writer.writer(f, obj_schema, (obj,))
        buf = bytes(f.getbuffer())

    with io.BytesIO(buf) as f:
        obj_reloaded = next(iter(fastavro.reader(f)))

    assert almost_equal(obj, obj_reloaded)

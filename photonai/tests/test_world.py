from .. import world
from . import test_schema
import numpy as np
from nose_parameterized import parameterized
from nose.tools import eq_


@parameterized([
    (world.Vector, test_schema.VECTOR),
    (world.Space, test_schema.Space.CREATE),
    (world.Body, test_schema.Body.CREATE, test_schema.Body.STATE),
    (world.Weapon, test_schema.Weapon.CREATE, test_schema.Weapon.STATE),
    (world.Controller, test_schema.Controller.CREATE,
     test_schema.Controller.STATE),
    (world.Ship, test_schema.Ship.CREATE, test_schema.Ship.STATE),
    (world.Pellet, test_schema.Pellet.CREATE, test_schema.Pellet.STATE),
])
def test_create_and_update_no_crash(world_cls, create, state=None):
    obj = world_cls.create(create)
    if state is not None:
        obj.update(state)
    str(obj)


def test_world():
    w = world.World()

    # Set up the world
    w(dict(clock=0,
           duration=0.1,
           data=test_schema.Space.CREATE))

    eq_(len(w.objects), 0)
    eq_(w.clock, 0)
    eq_(w.time, 0.1)
    np.testing.assert_equal(w.space.dimensions,
                            np.array([test_schema.VECTOR['x'],
                                      test_schema.VECTOR['y']]))
    eq_(w.space.gravity, test_schema.Space.CREATE['gravity'])

    # Objects can be created
    w(dict(clock=1,
           duration=0.1,
           data=[dict(id=100, data=test_schema.Body.CREATE),
                 dict(id=200, data=test_schema.Pellet.CREATE)]))
    eq_(w.clock, 1)
    eq_(w.time, 0.2)
    eq_(w.objects.keys(), set([100, 200]))

    body_orientation = test_schema.Body.STATE['orientation']
    eq_(w.objects[100].orientation, body_orientation)
    eq_(w.objects[200].orientation, body_orientation)

    # Objects can be updated
    body_update = test_schema.Body.STATE.copy()
    body_update['orientation'] += 2

    w(dict(clock=2,
           duration=0.1,
           data=[dict(id=100, data=body_update)]))
    eq_(w.objects.keys(), set([100, 200]))

    eq_(w.objects[100].orientation, body_update['orientation'])
    eq_(w.objects[200].orientation, body_orientation)

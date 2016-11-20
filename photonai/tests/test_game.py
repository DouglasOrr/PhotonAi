from .. import game
import fastavro
import itertools as it


def test_nothing():
    universe = dict(
        dimensions=dict(x=200, y=100),
        gravity=0.1,
        controllers=[],
    )
    step_0 = dict(
        timestamp=0,
        data=universe
    )
    assert fastavro._writer.validate(step_0, game.Schema.STEP)
    step_1 = dict(
        timestamp=100,
        data=[
            dict(id=10, data=dict(
                type='Planet',
                radius=10,
                mass=100,
                controller=None,
                state=dict(
                    position=dict(x=50, y=50),
                    velocity=dict(x=0, y=0),
                    orientation=0
                ))),
            dict(id=20, data=dict(
                type='Planet',
                radius=1,
                mass=1,
                controller=None,
                state=dict(
                    position=dict(x=60, y=10),
                    velocity=dict(x=1, y=6),
                    orientation=0
                ))),
        ])
    assert fastavro._writer.validate(step_1, game.Schema.STEP)

    viz = game.SimpleViz()
    viz(step_0)
    viz(step_1)


def test_engine():
    universe = dict(
        dimensions=dict(x=200, y=100),
        gravity=0.1,
        controllers=[],
    )
    planets = [
        dict(type='Planet',
             radius=10,
             mass=1000,
             controller=None,
             state=dict(
                 position=dict(x=50, y=50),
                 velocity=dict(x=0, y=0),
                 orientation=0
             )),
        dict(type='Planet',
             radius=1,
             mass=1,
             controller=None,
             state=dict(
                 position=dict(x=60, y=10),
                 velocity=dict(x=8, y=5),
                 orientation=0
             )),
    ]

    engine = game.Game(universe, planets, 100)
    viz = game.SimpleViz()
    for state in it.islice(engine, 100):
        viz(state)

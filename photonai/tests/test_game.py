from .. import game
import fastavro
import itertools as it


class SimpleViz:
    '''A simple text log vizualizer for simulations.
    '''
    def __call__(self, step):
        t = step['timestamp']
        print('# t = %.3f s' % (t / 1000.0))
        if isinstance(step['data'], dict):
            # Must be a Universe - reset
            self._objects = {}
        else:
            for event in step['data']:
                data = event['data']
                if 'type' in data:
                    # Create
                    self._objects[event['id']] = dict(
                        label='%s[%d]' % (data['type'], event['id']),
                        position=data['state']['position'])
                elif 'position' in data:
                    # Update
                    self._objects[event['id']]['position'] = data['position']
                else:
                    # Destroy
                    del self.objects[event['id']]
        for obj in self._objects.values():
            p = obj['position']
            print('\t%s (%0.1f, %0.1f)' % (obj['label'], p['x'], p['y']))


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

    viz = SimpleViz()
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
    viz = SimpleViz()
    for state in it.islice(engine, 100):
        viz(state)

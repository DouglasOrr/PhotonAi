class Schema:
    VECTOR = dict(
        type='record',
        name='Vector',
        fields=[
            dict(name='x', type='float'),
            dict(name='y', type='float'),
        ]
    )
    OBJECT_TYPE = dict(
        type='enum',
        name='ObjectType',
        symbols=[
            'Planet',
            'Ship',
            'Shell',
        ]
    )
    STATE = dict(
        type='record',
        name='State',
        fields=[
            dict(name='position', type=VECTOR),
            dict(name='velocity', type=VECTOR),
            dict(name='orientation', type='float'),
        ]
    )
    CREATE = dict(
        type='record',
        name='Create',
        fields=[
            dict(name='type', type=OBJECT_TYPE),
            dict(name='radius', type='float'),
            dict(name='mass', type='float'),
            dict(name='controller', type=['null', 'int'],
                 doc='index of the controller used for this object'
                 ' (into the universe\'s controllers list), if any'),
            dict(name='state', type=STATE),
        ]
    )
    DESTROY = dict(
        type='record',
        name='Destroy',
        fields=[],
    )
    EVENT = dict(
        type='record',
        name='Event',
        doc='Records the update of an individual game object',
        fields=[
            dict(name='id', type='int'),
            dict(name='data', type=[
                CREATE,
                STATE,
                DESTROY,
            ]),
        ]
    )
    CONTROLLER = dict(
        type='record',
        name='Controller',
        doc='Information about the controller of an object',
        fields=[
            dict(name='name', type='string'),
            dict(name='version', type='int'),
        ]
    )
    UNIVERSE = dict(
        type='record',
        name='Universe',
        doc='Setup information for the game universe',
        fields=[
            dict(name='dimensions', type=VECTOR),
            dict(name='gravity', type='float'),
            dict(name='controllers', type='array', items=CONTROLLER),
        ]
    )
    STEP = dict(
        type='record',
        name='Step',
        doc='A step of the game engine',
        fields=[
            dict(name='timestamp', type='long',
                 doc='Step discrete timestamp in ms'),
            dict(name='data', type=[
                UNIVERSE,
                dict(type='array', items=EVENT),
            ])
        ]
    )


class Vector:
    __slots__ = ('x', 'y')

    def __init__(self, x, y):
        self.x = x
        self.y = y

    @property
    def to_dict(self):
        return dict(x=self.x, y=self.y)

    @classmethod
    def from_dict(cls, d):
        return cls(x=float(d['x']), y=float(d['y']))

    @staticmethod
    def distance_sq(a, b):
        return (a.x - b.x) ** 2 + (a.y - b.y) ** 2

    @classmethod
    def zero(cls):
        return cls(0.0, 0.0)


class State:
    __slots__ = ('position', 'velocity', 'orientation')

    def __init__(self, position, velocity, orientation):
        self.position = position
        self.velocity = velocity
        self.orientation = orientation

    @property
    def to_dict(self):
        return dict(position=self.position.to_dict,
                    velocity=self.velocity.to_dict,
                    orientation=self.orientation)

    @classmethod
    def from_dict(cls, d):
        return cls(position=Vector.from_dict(d['position']),
                   velocity=Vector.from_dict(d['velocity']),
                   orientation=float(d['orientation']))


class Game:
    '''The game engine. Not very complex.
    '''
    def __init__(self, universe, start, tick_time):
        '''Create an immutable game engine (run the game by iterating over the engine
        to get steps).

        universe -- Schema.UNIVERSE

        start -- [Schema.CREATE]

        tick_time -- number of ms to tick each step
        '''
        self._universe = universe
        self._start = start
        self._tick_time = tick_time

    def __iter__(self):
        yield dict(timestamp=0, data=self._universe)
        yield dict(timestamp=0,
                   data=[dict(id=id, data=create)
                         for id, create in enumerate(self._start)])

        # Constants
        gravity_strength = self._universe['gravity']
        t_s = self._tick_time / 1000.0
        masses = {n: start['mass'] for n, start in enumerate(self._start)}

        # Variables
        states = [(n, State.from_dict(start['state']))
                  for n, start in enumerate(self._start)]
        t = 0
        while True:
            t += self._tick_time

            # Gravity
            acceleration = {id: Vector.zero() for id, _ in states}
            for idx, (id_a, a) in enumerate(states):
                m_a = masses[id_a]
                for id_b, b in states[idx+1:]:
                    m_b = masses[id_b]
                    d_sq = Vector.distance_sq(a.position, b.position)
                    s = t_s * gravity_strength * m_a * m_b / d_sq
                    acceleration[id_a].x += s * (b.position.x - a.position.x)
                    acceleration[id_a].y += s * (b.position.y - a.position.y)
                    acceleration[id_b].x += s * (a.position.x - b.position.x)
                    acceleration[id_b].y += s * (a.position.y - b.position.y)

            # Velocity
            for id, state in states:
                a = acceleration[id]
                state.velocity.x += a.x / 2
                state.velocity.y += a.y / 2
                state.position.x += t_s * state.velocity.x
                state.position.y += t_s * state.velocity.y
                state.velocity.x += a.x / 2
                state.velocity.y += a.y / 2

            yield dict(timestamp=t,
                       data=[dict(id=id, data=state.to_dict)
                             for id, state in states])

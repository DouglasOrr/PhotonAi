class Control:
    pass

class Object:
    __slots__ = ('mass',)
    def __init__(self, mass):
        self.mass = mass

class Planet(Object):
    pass

class Ship(Object):
    pass


SCHEMA_VECTOR = dict(
    type='record',
    name='Vector',
    fields=[
        dict(name='x', type='float'),
        dict(name='y', type='float'),
    ],
)

SCHEMA_TYPE = dict(
    type='enum',
    name='Type',
    symbols=[
        'Planet',
        'Ship',
        'Shell',
    ],
)

SCHEMA_STATE = dict(
    type='record',
    name='State',
    fields=[
        dict(name='id', type='int'),
        dict(name='position', type=SCHEMA_VECTOR),
        dict(name='orientation', type='float'),
    ],
)

SCHEMA_CREATE = dict(
    type='record',
    name='Create',
    fields=[
        dict(name='type', type=SCHEMA_TYPE),
        dict(name='state', type=SCHEMA_STATE),
        dict(name='mass', type='float'),
    ],
)

SCHEMA_EVENT = dict(
    type='record',
    name='Tick',
    fields=[
        dict(name='time', type='long'),
        dict(name='events', dict(type='array', items=[
            SCHEMA_CREATE,
            SCHEMA_STATE,
        ])),
    ],
)

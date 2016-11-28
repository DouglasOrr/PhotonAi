'''Helpers which make it easier to work with the logs from
 photonai.schema'''

from fastavro.writer import validate
from . import schema
from .util import Vector


class Item:
    '''Utility base class to make implementing create/update for specific
    game items simpler.
    '''
    __slots__ = ('update_clock',)

    def __init__(self, clock, **args):
        self.update_clock = clock
        for k, v in args.items():
            setattr(self, k, v)

    @staticmethod
    def _read_state(state):
        '''Overridden by derived classes to return an attribute dictionary
        for state updates.
        '''
        raise NotImplementedError

    @staticmethod
    def _read_create(create):
        '''Overridden by derived classes to return an attribute dictionary
        for object creation.
        '''
        raise NotImplementedError

    def __str__(self):
        return '%s{ %s }' % (type(self).__name__,
                             ', '.join('%s=%s' % (k, getattr(self, k))
                                       for k in self.__slots__))

    @classmethod
    def create(cls, clock, create):
        '''Create an instance of this item from a CREATE event.
        '''
        return cls(clock=clock, **cls._read_create(create))

    def update(self, clock, state):
        '''Update an instance of this item from a STATE event.
        '''
        self.update_clock = clock
        for k, v in self._read_state(state).items():
            setattr(self, k, v)


class Space(Item):
    __slots__ = Item.__slots__ + ('dimensions', 'gravity', 'lifetime')

    @staticmethod
    def _read_create(create):
        return dict(dimensions=Vector.create(create['dimensions']),
                    gravity=float(create['gravity']),
                    lifetime=float(create['lifetime']))


class Body(Item):
    __slots__ = Item.__slots__ + (
        'radius', 'mass',
        'position', 'velocity', 'orientation')

    @staticmethod
    def _read_state(state):
        return dict(position=Vector.create(state['position']),
                    velocity=Vector.create(state['velocity']),
                    orientation=float(state['orientation']))

    @staticmethod
    def _read_create(create):
        return dict(radius=float(create['radius']),
                    mass=float(create['mass']),
                    **Body._read_state(create['state']))


class Weapon(Item):
    __slots__ = Item.__slots__ + (
        'max_reload', 'max_temperature', 'temperature_decay',
        'speed', 'time_to_live',
        'fired', 'reload', 'temperature')

    @staticmethod
    def _read_state(state):
        return dict(fired=bool(state['fired']),
                    reload=float(state['reload']),
                    temperature=float(state['temperature']))

    @staticmethod
    def _read_create(create):
        d = {k: float(create[k])
             for k in ('max_reload', 'max_temperature', 'temperature_decay',
                       'speed', 'time_to_live')}
        d.update(Weapon._read_state(create['state']))
        return dict(**d)


class Controller(Item):
    __slots__ = Item.__slots__ + (
        'name', 'version', 'fire', 'rotate', 'thrust')

    @staticmethod
    def _read_state(state):
        return dict(fire=bool(state['fire']),
                    rotate=float(state['rotate']),
                    thrust=float(state['thrust']))

    @staticmethod
    def _read_create(create):
        return dict(name=str(create['name']),
                    version=int(create['version']),
                    **Controller._read_state(create['state']))


class Planet(Body):
    __slots__ = Body.__slots__ + ('name',)

    @staticmethod
    def _read_state(state):
        return Body._read_state(state['body'])

    @staticmethod
    def _read_create(create):
        return dict(name=create['name'],
                    **Body._read_create(create['body']))


class Ship(Body):
    __slots__ = Body.__slots__ + (
        'weapon', 'controller', 'max_thrust', 'max_rotate')

    @staticmethod
    def _read_state(state):
        return Body._read_state(state['body'])

    def update(self, clock, state):
        self.weapon.update(clock, state['weapon'])
        self.controller.update(clock, state['controller'])
        super().update(clock, state)

    @staticmethod
    def _read_create(create):
        return dict(max_thrust=float(create['max_thrust']),
                    max_rotate=float(create['max_rotate']),
                    **Body._read_create(create['body']))

    @classmethod
    def create(cls, clock, create):
        weapon = Weapon.create(clock, create['weapon'])
        controller = Controller.create(clock, create['controller'])
        return cls(clock=clock, weapon=weapon, controller=controller,
                   **cls._read_create(create))


class Pellet(Body):
    __slots__ = Body.__slots__ + ('time_to_live',)

    @staticmethod
    def _read_state(state):
        return dict(time_to_live=float(state['time_to_live']),
                    **Body._read_state(state['body']))

    @staticmethod
    def _read_create(create):
        return dict(time_to_live=float(create['time_to_live']),
                    **Body._read_create(create['body']))


class World:
    '''Saves the visible world state, updated step-by-step.
    '''
    __slots__ = ('clock', 'time', 'space', 'objects')

    def _handle_event(self, clock, event):
        id_ = event['id']
        data = event['data']

        # Validate in order richest-to-emptiest events (safest due to the
        # Avro libraries' duck-typing)
        if validate(data, schema.Ship.CREATE):
            assert id_ not in self.objects
            self.objects[id_] = Ship.create(clock, data)
        elif validate(data, schema.Pellet.CREATE):
            assert id_ not in self.objects
            self.objects[id_] = Pellet.create(clock, data)
        elif validate(data, schema.Planet.CREATE):
            assert id_ not in self.objects
            self.objects[id_] = Planet.create(clock, data)

        elif validate(data, [schema.Planet.STATE,
                             schema.Ship.STATE,
                             schema.Pellet.STATE]):
            self.objects[id_].update(clock, data)

        elif validate(data, schema.Object.DESTROY):
            del self.objects[id_]

        else:
            raise ValueError('Unrecognized event %s' % event)

    def __call__(self, step):
        if validate(step['data'], schema.Space.CREATE):
            # the first event in a stream should hit this branch
            self.space = Space.create(step['clock'], step['data'])
            self.objects = dict()
            self.time = 0
        else:  # must be a list of events
            for event in step['data']:
                self._handle_event(step['clock'], event)

        self.clock = step['clock']
        self.time += step['duration']

'''Helpers which make it easier to work with the logs from
 `photonai.schema`.

The raw logs are event-based (i.e. each Step must be understood in the
context of all preceding steps), but the `photonai.world.World` defined
here is state-based, providing a snapshot of the current state of the
game.
'''

from fastavro.writer import validate
from . import schema
from .util import Vector


class Item:
    '''Utility base class to make implementing create/update for specific
    game items simpler.

    `update_clock` -- step number when this object was last updated (compare
    with `photonai.world.World.clock` to see if this object is up-to-date).
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
    '''Information about the overall space of the game (e.g. the dimensions
    outside which ships will wrap around, and pellets destroyed).

    `dimensions` -- 2D numpy array specifying size of the space.

    `gravity` -- scalar strength of gravity (F = g m_1 m_2 / r).

    '''
    __slots__ = Item.__slots__ + ('dimensions', 'gravity')

    @staticmethod
    def _read_create(create):
        return dict(dimensions=Vector.create(create['dimensions']),
                    gravity=float(create['gravity']))


class Body(Item):
    '''Base class for 'bodies', which have position, size, mass.

    `radius` -- scalar radius of the circular hitbox (for collisions).

    `mass` -- scalar mass (used for gravity & acceleration).

    `position` -- 2D numpy array of current position.

    `velocity` -- 2D numpy array of velocity (change in position per time
    unit).

    `orientation` -- scalar orientation (use `photonai.util.direction` to find
    the direction vector), measured clockwise from vertical (+Y).
    '''
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
    '''Information about the weapon attached to a `photonai.world.Ship`.

    `max_reload` -- scalar reload time when the weapon is "cool" (below
    `max_temperature`).

    `max_temperature` -- scalar temperature above which weapon must wait to be
    able to fire (temperature increases by 1 when fired).

    `temperature_decay` -- scalar time taken to decay from
    `max_temperature + 1` back down to `max_temperature` (effectively the
    reload time when the weapon is "hot").

    `speed` -- scalar relative speed of ejected pellets.

    `time_to_live` -- scalar time to live of ejected pellets.

    `fired` -- `True` if the weapon was fired last step.

    `reload` -- scalar current reload timer (when zero, the weapon may be
    fired).

    `temperature` -- scalar current temperature.
    '''
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
    '''Information about control output for a bot.

    `name` -- name of the controller

    `version` -- upload version of the controller

    `fire` -- control signal to fire the weapon

    `rotate` -- control signal to rotate the ship

    `thrust` -- control signal to apply thrust to the ship
    '''
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
    '''A planet - usually large mass & radius, forming an obstacle.

    `name` -- friendly name to identify the planet.

    '''
    __slots__ = Body.__slots__ + ('name',)

    @staticmethod
    def _read_state(state):
        return Body._read_state(state['body'])

    @staticmethod
    def _read_create(create):
        return dict(name=create['name'],
                    **Body._read_create(create['body']))


class Ship(Body):
    '''A ship controlled by an AI `controller`.
    Note that the ship will wrap position (around (x, y) axes independently)
    if it leaves `space.dimensions`.

    `weapon` -- `photonai.world.Weapon`

    `controller` -- `photonai.world.Controller`

    `max_thrust` -- scalar maximum force
    (s.t. `F = clamp(controller.thrust, 0, 1) * max_thrust`).

    `max_rotate` -- scalar maximum rotation speed
    (s.t. `A = clamp(controller.rotate, -1, 1) * max_rotate`).

    '''
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
    '''A small, fast, pellet fired from a `photonai.world.Weapon`.

    `time_to_live` -- time remaining before the pellet self-destructs
    (N.B. the pellet will destruct early if it goes outside
    `space.dimensions`).
    '''
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

    `clock` -- step number of last update.

    `time` -- time of last update.

    `space` -- `photonai.world.Space`.

    `objects` -- a dict of ID to some {`photonai.world.Ship`,
    `photonai.world.Planet`, `photonai.world.Pellet`} currently surviving
    top-level game objects.

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

    def __str__(self):
        return 'World {\n  space: %s\n  clock: %s\n%s\n}' % (
            self.space,
            self.clock,
            '\n'.join('  - %s' % v for v in self.objects.values()))

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

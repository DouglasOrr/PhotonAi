'''Some common setup for maps.
'''

import numpy as np
from ..util import Vector


def binary_subdivision():
    '''Yields a sequence of subdivisions of the continuous
    interval [0, 1], to maximize spacing for an unknown N.
    I.e. yields:
    [0, 1/2, 1/4, 3/4, 1/8, 3/8, 5/8, 7/8, 1/16, ...]
    '''
    yield 0.0
    n = 1

    # n: yields
    # 0: 0,
    # 1: 1/2,
    # 2: 1/4, 3/4,
    # 4: 1/8, 3/8, 5/8, 7/8
    # ...
    while True:
        # 2 * (nearest power of two)
        denom = 2 ** (1 + int(np.log(n) / np.log(2)))
        yield (1 + 2 * (n % (denom / 2))) / float(denom)
        n += 1


def random_orientations(random):
    '''Choose an initial random orientation (bearing angle), and generate
    maximally spaced orientations from that.
    '''
    base_orientation = 2 * np.pi * random.rand()
    return (2 * np.pi * x + base_orientation
            for x in binary_subdivision())


class Map:
    def __init__(self, seed):
        self._random = np.random.RandomState(seed)

    @property
    def space(self):
        '''Override to change the overall space layout.
        '''
        return dict(
            dimensions=dict(x=150, y=100),
            gravity=0.1,
            lifetime=60.0)

    @property
    def planets(self):
        '''Return the set of planets to initialize the map with.
        '''
        raise NotImplementedError

    def ship(self, controller):
        '''Create a ship, possibly at a random location.
        '''
        raise NotImplementedError

    def _orbit_speed(self, mass):
        return np.sqrt(self.space['gravity'] * mass)

    @property
    def _center(self):
        return Vector.create(self.space['dimensions']) / 2

    def _create_planet(self, name, radius, mass, position, velocity):
        return dict(name=name,
                    body=dict(
                        radius=radius,
                        mass=mass,
                        state=dict(
                            position=Vector.to_log(position),
                            velocity=Vector.to_log(velocity),
                            orientation=0)))

    def _create_weapon(self):
        return dict(
            max_reload=0.1,
            max_temperature=10,
            temperature_decay=0.25,
            speed=100,
            time_to_live=1,
            state=dict(reload=0, temperature=0))

    def _create_ship(self, controller, position, velocity, orientation):
        return dict(
            body=dict(
                radius=2,
                mass=1,
                state=dict(
                    position=Vector.to_log(position),
                    velocity=Vector.to_log(velocity),
                    orientation=orientation)),
            weapon=self._create_weapon(),
            controller=controller,
            max_thrust=20,
            max_rotate=2)

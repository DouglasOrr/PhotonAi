'''Some common setup for maps.
'''

import numpy as np
from ..util import Vector


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
            lifetime=100.0)

    @property
    def planets(self):
        '''Return the set of planets to initialize the map with.
        '''
        raise NotImplementedError

    def ship(self, controller):
        '''Create a ship, possibly at a random location.
        '''
        raise NotImplementedError

    def _create_planet(self, radius, mass, position, velocity):
        return dict(
            radius=radius,
            mass=mass,
            state=dict(
                position=Vector.to_log(position),
                velocity=Vector.to_log(velocity),
                orientation=0))

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
            max_thrust=10,
            max_rotate=1)

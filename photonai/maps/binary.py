'''Two planets orbiting each other.
'''

import numpy as np
from . import common
from .. import util


class Map(common.Map):
    def __init__(self, seed):
        super().__init__(seed)
        self._planet_radius = 12.0
        self._orbit = 60.0
        self._planet_mass = 2000
        self._n = 0

    @property
    def planets(self):
        speed = np.sqrt(0.5) * self._orbit_speed(self._planet_mass)
        p_a = self._center + [-self._orbit / 2, 0]
        v_a = speed * util.Vector.up()
        p_b = self._center + [self._orbit / 2, 0]
        v_b = speed * util.Vector.down()
        return [self._create_planet(
            radius=self._planet_radius,
            mass=self._planet_mass,
            position=p, velocity=v)
                for p, v in [(p_a, v_a), (p_b, v_b)]]

    def ship(self, controller):
        # Compute a random 'x' value at alternating sides
        offset = self._center[0] - self._orbit / 2 - 2 * self._planet_radius
        assert 0 < offset
        x = offset * self._random.rand()
        if self._n % 2 == 1:
            x = self.space['dimensions']['x'] - x
        self._n += 1

        y = self.space['dimensions']['y'] * np.random.rand()
        return self._create_ship(
            controller=controller,
            position=np.array([x, y], dtype=np.float),
            velocity=util.Vector.zero(),
            orientation=2 * np.pi * self._random.rand())

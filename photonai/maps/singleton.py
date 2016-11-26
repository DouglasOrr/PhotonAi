'''One big central planet.
'''

import numpy as np
from . import common
from .. import util


class Map(common.Map):
    def __init__(self, seed):
        super().__init__(seed)
        self._base_orientation = 2 * np.pi * self._random.rand()
        self._n = 0
        self._planet_radius = 20
        self._orbit_radius = 20
        self._planet_position = util.Vector.create(
            self.space['dimensions']) / 2

    @property
    def planets(self):
        return [self._create_planet(
            radius=self._planet_radius,
            mass=1000,
            position=self._planet_position,
            velocity=util.Vector.zero())]

    def ship(self, controller):
        # Compute ratio:
        # 0: 0,
        # 1: 1/2,
        # 2: 1/4, 3/4,
        # 4: 1/8, 3/8, 5/8, 7/8
        # ...
        if self._n == 0:
            ratio = 0
        else:
            # 2 * (nearest power of two)
            denom = 2 ** (1 + int(np.log(self._n) / np.log(2)))
            ratio = (1 + 2 * (self._n % (denom / 2))) / float(denom)
        self._n += 1
        orientation = self._base_orientation + ratio * 2 * np.pi
        radius = self._planet_radius + self._orbit_radius
        position = self._planet_position + radius * util.direction(orientation)

        return self._create_ship(
            controller=controller,
            position=position,
            velocity=util.Vector.zero(),
            orientation=orientation)

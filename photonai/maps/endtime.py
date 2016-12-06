'''The end of the universe.
'''

from . import common
from .. import util
import numpy as np


class Map(common.Map):
    def __init__(self, seed):
        super().__init__(seed)
        self._planet_grid = [
            (x, y)
            for x in [0, 50, 100, 150]
            for y in [0, 50, 100]
        ]
        self._ship_grid = [
            (x, y)
            for x in [25, 75, 125]
            for y in [50]
        ] + [
            (x, y)
            for x in [50, 100]
            for y in [25, 75]
        ]
        self._random.shuffle(self._ship_grid)
        self._next_ship = iter(self._ship_grid)

    @property
    def planets(self):
        return [
            self._create_planet(
                radius=9,
                mass=16,
                name='x%d_y%d' % (x, y),
                position=np.array([x, y], dtype=np.float32),
                velocity=np.zeros((2,), dtype=np.float32))
            for x, y in self._planet_grid]

    def ship(self, controller):
        orientation = 2 * np.pi * self._random.rand()
        return self._create_ship(
            controller=controller,
            position=np.array(next(self._next_ship), dtype=np.float32),
            velocity=util.Vector.zero(),
            orientation=orientation)

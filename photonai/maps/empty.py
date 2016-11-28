'''No planets - just ships.
'''

import numpy as np
from . import common
from .. import util


class Map(common.Map):
    @property
    def planets(self):
        return []

    def ship(self, controller):
        position = (self._random.rand(2) *
                    util.Vector.create(self.space['dimensions']))
        orientation = 2 * np.pi * self._random.rand()
        return self._create_ship(
            controller=controller,
            position=position,
            velocity=util.Vector.zero(),
            orientation=orientation)

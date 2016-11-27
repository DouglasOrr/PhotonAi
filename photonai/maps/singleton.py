'''One big central planet.
'''

from . import common
from .. import util


class Map(common.Map):
    def __init__(self, seed):
        super().__init__(seed)
        self._planet_radius = 20
        self._orbit = 40
        self._orientation = iter(common.random_orientations(self._random))

    @property
    def planets(self):
        return [self._create_planet(
            radius=self._planet_radius,
            mass=1000,
            position=self._center,
            velocity=util.Vector.zero())]

    def ship(self, controller):
        orientation = next(self._orientation)
        return self._create_ship(
            controller=controller,
            position=(self._center +
                      self._orbit * util.direction(orientation)),
            velocity=util.Vector.zero(),
            orientation=orientation)

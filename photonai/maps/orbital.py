'''A planet with an orbiting moon, with ships also starting in orbit.
'''

from . import common
from .. import util
import numpy as np


class Map(common.Map):
    def __init__(self, seed):
        super().__init__(seed)
        self._planet_radius = 15.0
        self._moon_radius = 5.0
        self._orbit_radius = 35.0
        self._planet_mass = 2000
        self._moon_mass = 10

        self._orientation = iter(common.random_orientations(self._random))
        self._moon_orientation = next(self._orientation)

    def _orbit(self, orientation):
        return dict(
            position=(self._center +
                      self._orbit_radius * util.direction(orientation)),
            velocity=(self._orbit_speed(self._planet_mass) *
                      util.direction(orientation + np.pi / 2)))

    @property
    def planets(self):
        planet = self._create_planet(
            radius=self._planet_radius,
            mass=self._planet_mass,
            position=self._center,
            velocity=util.Vector.zero())

        moon = self._create_planet(
            radius=self._moon_radius,
            mass=self._moon_mass,
            **self._orbit(self._moon_orientation))

        return [planet, moon]

    def ship(self, controller):
        orientation = next(self._orientation)
        return self._create_ship(
            controller=controller,
            orientation=(orientation + np.pi / 2),
            **self._orbit(orientation))

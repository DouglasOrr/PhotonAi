'''No planets - just ships.
'''

from . import common
import numpy as np


space = common.space


planets = []


def ship(n, controller):
    position = np.random.rand(2) * [space['dimensions']['x'],
                                    space['dimensions']['y']]
    orientation = 2 * np.pi * np.random.rand()
    return common.ship(
        controller=controller,
        position=dict(x=position[0], y=position[1]),
        velocity=dict(x=0, y=0),
        orientation=orientation)

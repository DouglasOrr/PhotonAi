'''One big central planet.
'''

import math
from . import common


space = common.space


planets = [common.planet(radius=20,
                         mass=1000,
                         position=dict(x=75, y=50),
                         velocity=dict(x=0, y=0))]


def ship(n, controller):
    if n == 0:
        return common.ship(
            controller=controller,
            position=dict(x=25, y=50),
            velocity=dict(x=0, y=0),
            orientation=math.pi / 2)
    elif n == 1:
        return common.ship(
            controller=controller,
            position=dict(x=125, y=50),
            velocity=dict(x=0, y=0),
            orientation=-math.pi / 2)
    else:
        raise ValueError(
            'Can only place two ships on this map')

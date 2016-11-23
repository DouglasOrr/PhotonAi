import math


space = dict(
    dimensions=dict(x=150, y=100),
    gravity=0.01)


planets = [dict(
    radius=25,
    mass=1000,
    state=dict(
        position=dict(x=75, y=50),
        velocity=dict(x=0, y=0),
        orientation=0))]


def ship(n, controller):
    weapon = dict(
        max_reload=0.1,
        max_temperature=10,
        temperature_decay=0.25,
        speed=100,
        time_to_live=1,
        state=dict(reload=0, temperature=0))
    if n == 0:
        initial_state = dict(
            position=dict(x=25, y=50),
            velocity=dict(x=0, y=0),
            orientation=math.pi / 2)
    else:
        initial_state = dict(
            position=dict(x=125, y=50),
            velocity=dict(x=0, y=0),
            orientation=-math.pi / 2)
    return dict(
        body=dict(
            radius=1,
            mass=1,
            state=initial_state),
        weapon=weapon,
        controller=controller,
        max_thrust=10,
        max_rotate=1)

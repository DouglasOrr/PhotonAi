'''Some common setup for maps.
'''

space = dict(
    dimensions=dict(x=150, y=100),
    gravity=0.1,
    lifetime=100.0)


weapon = dict(
    max_reload=0.1,
    max_temperature=10,
    temperature_decay=0.25,
    speed=100,
    time_to_live=1,
    state=dict(reload=0, temperature=0))


def ship(controller, position, velocity, orientation):
    return dict(
        body=dict(
            radius=2,
            mass=1,
            state=dict(
                position=position,
                velocity=velocity,
                orientation=orientation)),
        weapon=weapon,
        controller=controller,
        max_thrust=10,
        max_rotate=1)


def planet(radius, mass, position, velocity):
    return dict(
        radius=radius,
        mass=mass,
        state=dict(
            position=position,
            velocity=velocity,
            orientation=0.0))

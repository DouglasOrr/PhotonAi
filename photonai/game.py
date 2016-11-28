from . import world, util
import itertools as it
import numpy as np


def _move_body(subject, others, space, dt, forward=None, rotate=0):
    accel = world.Vector.zero()

    if forward is not None:
        accel += forward * util.direction(subject.orientation)

    # Massless objects experience no gravity
    if subject.mass != 0:
        for other in others:
            if other is not subject:
                relative = other.position - subject.position
                strength = space.gravity * other.mass / (relative ** 2).sum()
                accel += strength * relative

    new_velocity = subject.velocity + dt * accel

    new_position = (subject.position +
                    (dt / 2) * subject.velocity +
                    (dt / 2) * new_velocity)

    # Ships should wrap around the world
    if isinstance(subject, world.Ship):
        new_position = new_position % space.dimensions

    new_orientation = (subject.orientation + dt * rotate) % (2 * np.pi)

    return dict(position=world.Vector.to_log(new_position),
                velocity=world.Vector.to_log(new_velocity),
                orientation=new_orientation)


def _is_collision(subject, others):
    for other in others:
        if other is not subject:
            d_sq = ((other.position - subject.position) ** 2).sum()
            if d_sq < (subject.radius + other.radius) ** 2:
                return True
    return False


def _fire_pellet(ship, state):
    direction = util.direction(state['orientation'])
    # Use a small "fudge ratio" to spawn the pellet further away from the ship
    # (so we don't shoot ourselves).
    # Also ensure we use the "new state" of the ship at the end of this
    # timestep.
    position = (world.Vector.create(state['position']) +
                1.01 * ship.radius * direction)
    velocity = (world.Vector.create(state['velocity']) +
                ship.weapon.speed * direction)
    return dict(
        body=dict(
            mass=0.0,
            radius=0.0,
            state=dict(
                position=world.Vector.to_log(position),
                velocity=world.Vector.to_log(velocity),
                orientation=state['orientation'],
            )),
        time_to_live=ship.weapon.time_to_live)


def game(map_spec, controller_bots, step_duration):
    '''Create an iterable of game updates.

    map_spec -- should have properties (space, planets, ship)

    controller_bots -- a list of .schema.Controller.CREATE, except
    instead of a 'state', has a 'bot' instance of .bot.Bot

    step_duration -- period of time per step

    returns -- a sequence of log events (according to .schema.STEP)
    by running the game.

    '''
    world_ = world.World()
    world_.clock = -1  # Advances to zero on first step
    object_ids = it.count()
    last_step = None

    def step(data):
        step_ = dict(clock=world_.clock + 1,
                     duration=step_duration,
                     data=data)
        nonlocal last_step
        last_step = step_
        world_(step_)
        return step_

    def move_body(obj, **args):
        return _move_body(
            obj, world_.objects.values(),
            space=world_.space,
            dt=step_duration,
            **args)

    # Setup the world & initial objects

    ship_to_bot = {}
    ships = []
    for controller_bot in controller_bots:
        ship_id = next(object_ids)
        controller = controller_bot.copy()
        ship_to_bot[ship_id] = controller.pop('bot')
        controller['state'] = dict(
            fire=False,
            rotate=0.0,
            thrust=0.0,
        )
        ships.append(dict(id=ship_id, data=map_spec.ship(controller)))

    planets = [dict(id=next(object_ids), data=planet)
               for planet in map_spec.planets]

    yield step(map_spec.space)

    # Introduce the bots to the space
    for bot in ship_to_bot.values():
        bot(dict(step=last_step, ship_id=None))

    yield step(planets + ships)

    # Enter the main loop

    while world_.time < world_.space.lifetime:
        events = []
        for id in world_.objects:
            obj = world_.objects[id]

            if (isinstance(obj, (world.Ship, world.Pellet)) and
                    _is_collision(obj, world_.objects.values())):
                state = dict()  # destroys it

            elif isinstance(obj, world.Ship):
                control = ship_to_bot[id](dict(step=last_step, ship_id=id))

                # Body
                forward = obj.max_thrust * np.clip(control['thrust'], 0, 1)
                rotate = obj.max_rotate * np.clip(control['rotate'], -1, 1)
                body_state = move_body(obj, forward=forward, rotate=rotate)

                # Weapon
                weapon = obj.weapon
                reload = max(0, weapon.reload - step_duration)
                # Calculate the decay ratio needed to get the time spent above
                # max_temperature to == weapon.temperature_decay
                mr = weapon.max_temperature / (weapon.max_temperature + 1)
                decay_ratio = mr ** (step_duration / weapon.temperature_decay)
                temperature = decay_ratio * weapon.temperature
                if (control['fire'] and reload == 0 and
                        temperature < weapon.max_temperature):
                    # We are allowed to fire
                    events.append(dict(id=next(object_ids),
                                       data=_fire_pellet(obj, body_state)))
                    reload = weapon.max_reload
                    temperature += 1

                state = dict(
                    body=body_state,
                    weapon=dict(reload=reload, temperature=temperature),
                    controller=control)

            elif isinstance(obj, world.Pellet):
                time_to_live = obj.time_to_live - step_duration
                if 0 < time_to_live:
                    state = dict(
                        body=move_body(obj),
                        time_to_live=time_to_live)
                else:
                    state = dict()  # destroys it

            elif isinstance(obj, world.Planet):
                state = dict(body=move_body(obj))

            else:
                raise ValueError('Unknown object type %s' % type(obj))

            events.append(dict(id=id, data=state))
        yield step(events)

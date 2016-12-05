from . import world, util
import numpy as np
import itertools as it
import logging


def _is_collision(subject, others):
    '''Test for collisions.

    subject -- a (subclass of a) world.Body instance to test

    others -- a list of world.Body instances to test against

    returns -- `True` if the subject has collided with any object in the
    list 'others'.

    '''
    for other in others:
        if other is not subject:
            d_sq = ((other.position - subject.position) ** 2).sum()
            if d_sq < (subject.radius + other.radius) ** 2:
                return True
    return False


class _Destroy(Exception):
    '''Raised when an object should be destroyed.
    '''
    pass


def _move_body(subject, world_, control, dt):
    '''Compute the new body state of the subject.

    subject -- a world {Ship, Pellet, Planet}

    world_ -- the world to use for collisions, etc.

    control -- Control.STATE to use to update a Ship

    dt -- timestep
    '''

    # 1. Test for collisions - except planets, which cannot collide
    if (isinstance(subject, (world.Ship, world.Pellet)) and
            _is_collision(subject, world_.objects.values())):
        raise _Destroy()

    # 2. Compute the new position & velocity
    accel = util.Vector.zero()

    if control is not None:
        forward = subject.max_thrust * np.clip(control['thrust'], 0, 1)
        accel += forward * util.direction(subject.orientation)

    # (massless objects experience no gravity)
    if subject.mass != 0:
        for other in world_.objects.values():
            if other is not subject:
                relative = other.position - subject.position
                accel += (
                    world_.space.gravity * other.mass / (relative ** 2).sum()
                ) * relative

    new_velocity = subject.velocity + dt * accel

    new_position = (subject.position +
                    (dt / 2) * subject.velocity +
                    (dt / 2) * new_velocity)

    # Ships should wrap around the world
    if isinstance(subject, world.Ship):
        new_position = new_position % world_.space.dimensions

    # Pellets are auto-destroyed when out-of-bounds (for efficiency)
    if isinstance(subject, world.Pellet) and \
       np.any(new_position < util.Vector.zero()) and \
       np.any(world_.space.dimensions <= new_position):
        raise _Destroy

    # 3. Compute the new orientation
    if control is not None:
        rotate = subject.max_rotate * np.clip(control['rotate'], -1, 1)
        new_orientation = (subject.orientation + dt * rotate) % (2 * np.pi)
    else:
        new_orientation = subject.orientation

    return dict(position=util.Vector.to_log(new_position),
                velocity=util.Vector.to_log(new_velocity),
                orientation=new_orientation)


def _update_weapon(weapon, control_fire, dt):
    '''Compute the update from a weapon - update temperature & reload,
    and return whether the weapon is actually able to fire.

    weapon -- a world.Weapon object to be updated

    control_fire -- True if the controller requests the weapon to firs

    dt -- timestep

    returns -- Weapon.STATE new state of the weapon
    '''
    reload = max(0, weapon.reload - dt)
    # Calculate the decay ratio needed to get the time spent above
    # max_temperature to == weapon.temperature_decay
    mr = weapon.max_temperature / (weapon.max_temperature + 1)
    decay_ratio = mr ** (dt / weapon.temperature_decay)
    temperature = decay_ratio * weapon.temperature

    fired = (control_fire and
             reload == 0 and
             temperature < weapon.max_temperature)
    if fired:
        reload = weapon.max_reload
        temperature += 1

    return dict(fired=fired, reload=reload, temperature=temperature)


def _fire_pellet(ship, body_state):
    '''Compute the 'create' event for a single pellet fired
    from a ship.

    ship -- the world.Ship that is firing

    body_state -- the ship's next body state (N.B. we use this to
    avoid "shooting ourselves" errors)

    returns -- a Pellet.CREATE event
    '''
    direction = util.direction(body_state['orientation'])
    # Use a small "fudge ratio" to spawn the pellet further away from the ship
    # (so we don't shoot ourselves).
    position = (util.Vector.create(body_state['position']) +
                1.01 * ship.radius * direction)
    velocity = (util.Vector.create(body_state['velocity']) +
                ship.weapon.speed * direction)
    return dict(
        body=dict(
            mass=0.0,
            radius=0.0,
            state=dict(
                position=util.Vector.to_log(position),
                velocity=util.Vector.to_log(velocity),
                orientation=body_state['orientation'],
            )),
        time_to_live=ship.weapon.time_to_live)


class Simulator:
    '''A simulator computes a single step, based on a world
    (which should be updated externally).
    '''
    def __init__(self, world, step_duration, object_id_gen):
        self._world = world
        self._step_duration = step_duration
        self._object_id_gen = object_id_gen

    def _update_object(self, id, control):
        obj = self._world.objects[id]
        try:
            state = dict(body=_move_body(obj,
                                         world_=self._world,
                                         control=control,
                                         dt=self._step_duration))

            if isinstance(obj, world.Ship):
                state['controller'] = control
                state['weapon'] = _update_weapon(obj.weapon,
                                                 control['fire'],
                                                 dt=self._step_duration)
                if state['weapon']['fired']:
                    yield dict(id=next(self._object_id_gen),
                               data=_fire_pellet(obj, state['body']))

            elif isinstance(obj, world.Pellet):
                state['time_to_live'] = obj.time_to_live - self._step_duration
                if state['time_to_live'] <= 0:
                    raise _Destroy()

            elif isinstance(obj, world.Planet):
                pass  # nothing else to update

            else:
                raise ValueError('Unknown object type %s' % type(obj))

            yield dict(id=id, data=state)

        except _Destroy:
            yield dict(id=id, data=dict())

    def __call__(self, controller_states):
        '''Return a list of events corresponding a single step of the simulation.
        '''
        return [event
                for id in self._world.objects
                for event in self._update_object(
                        id, controller_states.get(id))]


def _is_obscured(world_, src, dest):
    '''Only planets count as obscuring vision.
    '''
    los = dest.position - src.position
    los_distance = util.Vector.length(los)
    los_direction = los / los_distance

    for obj in world_.objects.values():
        if isinstance(obj, world.Planet):
            relative = obj.position - src.position
            d = np.dot(los_direction, relative)
            if 0 < d and d < los_distance and (
                    (relative ** 2).sum() < (d ** 2 + obj.radius ** 2)):
                return True
    return False


def _obscured_ships(world_, from_ship):
    '''Yield the object IDs of ships that are obscured from this one.
    '''
    for id, obj in world_.objects.items():
        if isinstance(obj, world.Ship):
            if obj is not from_ship and _is_obscured(world_, from_ship, obj):
                yield id


def _remove_ship_updates(step, ids):
    '''Remove updates pertaining to a certain set of ship IDs.
    '''
    ids = set(ids)
    if len(ids) == 0 and isinstance(step['data'], list):
        return step
    else:
        step = step.copy()
        # You can always see ship creation and destruction
        # (done by testing 'max_thrust' & empty-update),
        # otherwise exclude the obscured ships
        step['data'] = [d for d in step['data']
                        if d['id'] not in ids or
                        'max_thrust' in d['data'] or
                        len(d['data']) == 0]
        return step


class Controllers:
    DEFAULT_STATE = dict(
        fire=False,
        rotate=0.0,
        thrust=0.0,
    )

    def __init__(self, world_, id_to_bot):
        self._world = world_
        self._id_to_bot = id_to_bot
        self.control = {id: Controllers.DEFAULT_STATE
                        for id, bot in id_to_bot.items()}

    def _call_bot(self, id, step):
        try:
            return self._id_to_bot[id](step)
        except Exception as e:
            logging.error('Bot %d error %s', id, e)
            del self._id_to_bot[id]

    def __call__(self, step):
        # Must copy id_to_bot keys (to avoid concurrent modification)
        for id in list(self._id_to_bot):
            ship = self._world.objects.get(id)
            if ship is None:
                self._call_bot(id, dict(step=step, ship_id=None))
            else:
                # obscure vision of other ships
                ship_step = _remove_ship_updates(
                    step, _obscured_ships(self._world, ship))
                control = self._call_bot(id, dict(step=ship_step, ship_id=id))
                if control is not None:
                    self.control[id] = control


class Stop(Exception):
    '''Raised when the game should finish.
    '''
    def __init__(self, message, winner=None):
        self.message = message
        self.winner = winner

    def __str__(self):
        return 'game over: %s' % self.message


def stop_after(limit_time):
    '''Stop the game after a maximum time.
    '''
    def cond(world_):
        if limit_time <= world_.time:
            raise Stop('exceeded time limit %.2g' % limit_time)
    return cond


def stop_when_no_ships():
    '''Stop the game when there are no ships remaining.
    '''
    def cond(world_):
        if sum(1 for obj in world_.objects.values()
               if isinstance(obj, world.Ship)) == 0:
            raise Stop('no ships remaining')
    return cond


def stop_when_one_ship():
    '''Regular last-man-standing stopper - when there is just one surviving
    ship.
    '''
    def cond(world_):
        ships = [obj for obj in world_.objects.values()
                 if isinstance(obj, world.Ship)]
        if len(ships) == 0:
            raise Stop('no ships remaining (draw)')
        elif len(ships) == 1:
            ship = ships[0]
            winner = dict(name=ship.controller.name,
                          version=ship.controller.version)
            raise Stop('won by %s:v%d' % (winner['name'], winner['version']),
                       winner)
    return cond


def stop_when_any(*conditions):
    '''Stop when any of the conditions are met.
    '''
    def cond(world_):
        for f in conditions:
            f(world_)
    return cond


def run_game(map_spec, controller_bots, stop, step_duration):
    '''Create an iterable of game updates.

    map_spec -- should have properties (space, planets, ship)

    controller_bots -- a list of pairs (.schema.Controller.CREATE, .bot.Bot)

    stop -- a function(world) which raises Stop when the simulation should
    terminate

    step_duration -- period of time per step

    returns -- a sequence of log events (according to .schema.STEP)
    by running the game.

    '''
    # Objects needed for running the game
    object_id_gen = it.count()
    world_ = world.World()
    world_.clock = -1  # Advances to zero on first step
    simulator = Simulator(world_, step_duration, object_id_gen)

    # The initial state
    planets = [dict(id=next(object_id_gen), data=planet)
               for planet in map_spec.planets]

    ships = [dict(id=next(object_id_gen),
                  data=map_spec.ship(dict(state=Controllers.DEFAULT_STATE,
                                          **controller)))
             for controller, _ in controller_bots]

    controllers = Controllers(world_, {
        ship['id']: bot
        for ship, (_, bot) in zip(ships, controller_bots)
    })

    # Helper function - create a 'step' & update the simulation state
    def step(data):
        step_ = dict(clock=world_.clock + 1,
                     duration=step_duration,
                     data=data)
        world_(step_)
        controllers(step_)
        return step_

    # Run the game
    yield step(map_spec.space)
    yield step(planets + ships)
    while True:
        yield step(simulator(controllers.control))
        stop(world_)

'''Core game log schema.
'''

# N.B. When updating this file, make sure you also update the example
# data in .tests.test_schema & objects in .world

VECTOR = dict(
    type='record',
    name='Vector',
    namespace='photonai',
    fields=[
        dict(name='x', type='float'),
        dict(name='y', type='float'),
    ])


class Space:
    CREATE = dict(
        type='record',
        name='Create',
        namespace='photonai.space',
        doc='Global information for the game space',
        fields=[
            dict(name='dimensions', type=VECTOR),
            dict(name='gravity', type='float'),
        ])


# Sub-objects

class Body:
    STATE = dict(
        type='record',
        name='State',
        namespace='photonai.body',
        fields=[
            dict(name='position', type=VECTOR),
            dict(name='velocity', type=VECTOR),
            dict(name='orientation', type='float'),
        ])
    CREATE = dict(
        type='record',
        name='Create',
        namespace='photonai.body',
        fields=[
            dict(name='radius', type='float'),
            dict(name='mass', type='float'),
            dict(name='state', type=STATE),
        ])


class Weapon:
    STATE = dict(
        type='record',
        name='State',
        namespace='photonai.weapon',
        fields=[
            dict(name='fired', type='boolean',
                 doc='True if the weapon was fired on this timestep.'),
            dict(name='reload', type='float',
                 doc='Time until reloaded'),
            dict(name='temperature', type='float',
                 doc='Weapon temperature - cannot fire if too high'),
        ])
    CREATE = dict(
        type='record',
        name='Create',
        namespace='photonai.weapon',
        doc='Information about a Ship\'s weapons',
        fields=[
            dict(name='max_reload', type='float',
                 doc='Time between firing'),
            dict(name='max_temperature', type='float',
                 doc='Weapon cannot fire while above this temperature'),
            dict(name='temperature_decay', type='float',
                 doc='Time to decay from (max_temperature + 1) down'
                 ' to max_temperature'),
            dict(name='speed', type='float',
                 doc='Speed of ejected pellets'),
            dict(name='time_to_live', type='float',
                 doc='Time to live of ejected pellets'),
            dict(name='state', type=STATE),
        ])


class Controller:
    STATE = dict(
        type='record',
        name='State',
        namespace='photonai.controller',
        fields=[
            dict(name='fire', type='boolean',
                 doc='Fire the weapon, if possible'),
            dict(name='rotate', type='float',
                 doc='Rotate in this direction [-1, +1]'),
            dict(name='thrust', type='float',
                 doc='Apply this level of forward thrust [0, +1]'),
        ])
    CREATE = dict(
        type='record',
        name='Create',
        namespace='photonai.controller',
        doc='Information about a Ship\'s controller',
        fields=[
            dict(name='name', type='string'),
            dict(name='version', type='int'),
            dict(name='state', type=STATE),
        ])


# Top-level objects

class Planet:
    STATE = dict(
        type='record',
        name='State',
        namespace='photonai.planet',
        fields=[
            dict(name='body', type=Body.STATE),
        ])
    CREATE = dict(
        type='record',
        name='Create',
        namespace='photonai.planet',
        fields=[
            dict(name='body', type=Body.CREATE),
            dict(name='name', type='string'),
        ])


class Ship:
    STATE = dict(
        type='record',
        name='State',
        namespace='photonai.ship',
        fields=[
            dict(name='body', type=Body.STATE),
            dict(name='weapon', type=Weapon.STATE),
            dict(name='controller', type=Controller.STATE),
        ])
    CREATE = dict(
        type='record',
        name='Create',
        namespace='photonai.ship',
        fields=[
            dict(name='body', type=Body.CREATE),
            dict(name='weapon', type=Weapon.CREATE),
            dict(name='controller', type=Controller.CREATE),
            dict(name='max_thrust', type='float'),
            dict(name='max_rotate', type='float'),
        ])


class Pellet:
    STATE = dict(
        type='record',
        name='State',
        namespace='photonai.pellet',
        fields=[
            dict(name='body', type=Body.STATE),
            dict(name='time_to_live', type='float'),
        ])
    CREATE = dict(
        type='record',
        name='Create',
        namespace='photonai.pellet',
        fields=[
            dict(name='body', type=Body.CREATE),
            dict(name='time_to_live', type='float'),
        ])


class Object:
    DESTROY = dict(
        type='record',
        name='Destroy',
        namespace='photonai.object',
        fields=[])
    EVENT = dict(
        type='record',
        name='Event',
        namespace='photonai.object',
        doc='Records the update of an individual game object',
        fields=[
            dict(name='id', type='int'),
            dict(name='data', type=[
                # due to slightly broken duck-subtyping, it is safest
                # to put richest events first
                Ship.CREATE, Ship.STATE,
                Pellet.CREATE, Pellet.STATE,
                Planet.CREATE, Planet.STATE,
                DESTROY,
            ]),
        ])


# Toplevel schema

STEP = dict(
    type='record',
    name='Step',
    namespace='photonai',
    doc='A step of the game engine',
    fields=[
        dict(name='clock', type='int'),
        dict(name='duration', type='float'),
        dict(name='data', type=[
            Space.CREATE,
            dict(type='array', items=Object.EVENT),
        ])
    ])

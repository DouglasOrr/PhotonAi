from .. import bot
from . import bots, test_schema
import os
import sys
from nose.tools import eq_
from nose_parameterized import parameterized


def subprocess_bot(bot_module):
    project_path = os.path.abspath(os.path.join(__file__, '../../..'))
    return bot.SubprocessBot(
        ['env', 'PYTHONPATH=%s' % project_path,
         'python3', bot_module.__file__],
        stderr=sys.stderr,
        timeout=0.1)


# c.f. bots/nothing.py
ZERO_CONTROL = dict(fire=False, rotate=0.0, thrust=0.0)

# c.f. bots/spiral.py
SPIRAL_CONTROL = dict(fire=True, rotate=-1.0, thrust=1.0)


@parameterized([
    (lambda: bots.nothing.Bot(), ZERO_CONTROL),
    (lambda: subprocess_bot(bots.nothing), ZERO_CONTROL),
    (lambda: bots.spiral.Bot(), SPIRAL_CONTROL),
    (lambda: subprocess_bot(bots.spiral), SPIRAL_CONTROL),
])
def test_stateless_bot(create, expected_control):
    bot = create()

    eq_(None, bot(dict(
        step=dict(clock=0, duration=0.01, data=test_schema.Space.CREATE),
        ship_id=None)),
        'no ship to control yet')

    eq_(expected_control, bot(dict(
        step=dict(clock=1, duration=0.01,
                  data=[dict(id=246, data=test_schema.Ship.CREATE)]),
        ship_id=246)),
        'zero control to the ship')

    eq_(expected_control, bot(dict(
        step=dict(clock=2, duration=0.01,
                  data=[dict(id=246, data=test_schema.Ship.STATE)]),
        ship_id=246)),
        'still zero control to the ship')

    bot.close()

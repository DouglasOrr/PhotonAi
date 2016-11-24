from .. import bot
from . import nothing_bot, test_schema
import os
import sys
from nose.tools import eq_
from nose_parameterized import parameterized


PROJECT_PATH = os.path.abspath(os.path.join(__file__, '../../..'))


@parameterized([
    (lambda: nothing_bot.Bot(),),
    (lambda: bot.SubprocessBot(['env', 'PYTHONPATH=%s' % PROJECT_PATH,
                                'python', nothing_bot.__file__],
                               stderr=sys.stderr,),),
])
def test_nothing_bot(create):
    zero_control = dict(fire=False, rotate=0.0, thrust=0.0)
    bot = create()

    eq_(None, bot(dict(
        step=dict(clock=0, duration=0.01, data=test_schema.Space.CREATE),
        ship_id=None)),
        'no ship to control yet')

    eq_(zero_control, bot(dict(
        step=dict(clock=1, duration=0.01,
                  data=[dict(id=246, data=test_schema.Ship.CREATE)]),
        ship_id=246)),
        'zero control to the ship')

    bot.close()

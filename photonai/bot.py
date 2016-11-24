import fastavro
import sys
import subprocess
from . import schema, world


class Bot:
    '''A player-defined bot for controlling a ship in the game.
    '''
    REQUEST = dict(
        type='record',
        name='Request',
        namespace='photonai.bot',
        fields=[
            dict(name='step', type=schema.STEP,
                 doc='a game engine step - may not be "complete",'
                 ' e.g. if an enemy ship is obscured'),
            dict(name='ship_id', type=['int', 'null']),
        ])

    RESPONSE = [schema.Controller.STATE, 'null']

    def __call__(self, request):
        '''Run the bot for a single game step, and get the control output
        to control the Ship object ship_id.

        request -- schema.REQUEST -- the request for the controller - a
        step from the game engine, and the ship ID for which control is
        requested. Or `None`, in which case the bot is finished & should
        be destroyed

        returns -- Bot.RESPONSE -- the control to apply for the ship
        '''
        raise NotImplementedError

    def close(self):
        '''Dispose any resources associated with this bot.
        '''
        pass

    def run_loop(self):
        '''Run a loop, listening for requests on STDIN, and writing control
        responses to STDOUT.
        '''
        writer = fastavro._writer.Writer(sys.stdout.buffer, Bot.RESPONSE)
        # Make sure no-one else writes to stdout - that would be bad!
        sys.stdout = sys.stderr
        writer.flush()
        reader = fastavro.reader(sys.stdin.buffer)
        while True:
            try:
                request = next(reader)
            except IndexError as e:
                sys.stderr.write(
                    'swallowing possible exception (ignore if EOF):'
                    ' %r\n' % e)
                break
            writer.write(self(request))
            writer.flush()


class SimpleBot(Bot):
    '''A bot that presents an simple interface to subclasses.

    Accumulates game state updates into a `photonai.world.World`, and
    provides a simple way to respond with control signals `SimpleBot.Control`.
    '''
    class Control:
        __slots__ = ('fire', 'rotate', 'thrust')

        def __init__(self, fire=False, rotate=0.0, thrust=0.0):
            self.fire = fire
            self.rotate = rotate
            self.thrust = thrust

        def to_log(self):
            return dict(fire=bool(self.fire),
                        rotate=float(self.rotate),
                        thrust=float(self.thrust))

    def __init__(self):
        self._world = world.World()

    def __call__(self, request):
        self._world(request['step'])
        if request['ship_id'] is not None:
            ship = self._world.objects[request['ship_id']]
            return self.get_control(self._world, ship).to_log()

    def get_control(self, world, ship):
        '''Get the control signal for 'ship' in the current state of 'world'.

        world -- a photonai.world.World object containing all the known state

        ship -- a photonai.world.Ship object for the ship being controlled

        returns -- a SimpleBot.Control object for the ship being controlled
        '''
        raise NotImplementedError


class SubprocessBot(Bot):
    '''A bot that forwards to an Avro stdin/stdout streaming subprocess.
    '''
    def __init__(self, command, stderr=subprocess.DEVNULL):
        self._process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=stderr)
        self._request = fastavro._writer.Writer(
            self._process.stdin, Bot.REQUEST)
        self._request.flush()
        self._response = fastavro.reader(
            self._process.stdout)

    def close(self):
        try:
            self._process.communicate(timeout=1)
        except subprocess.TimeoutExpired:
            self._process.kill()

    def __call__(self, request):
        self._request.write(request)
        self._request.flush()
        return next(self._response)

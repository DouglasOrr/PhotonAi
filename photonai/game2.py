from . import world


class Game:
    '''The game engine.
    '''
    def __init__(self, map_spec, bots):
        self._world = world.World()

    def run(self):
        '''Get a sequence of log events (according to .schema.STEP) by
        running the game.
        '''
        pass

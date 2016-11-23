from . import world


class Bot:
    pass


class Game:
    '''The game engine.
    '''
    def __init__(self, map_spec, bots):
        self._world = world.World()

    def run(self):
        '''Get a sequence of log events (according to .schema) by
        running the game.
        '''
        pass

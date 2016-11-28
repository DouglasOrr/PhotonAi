import numpy as np


class Vector:
    '''Utilities for going between np.array and dict(x=, y=).
    '''
    @staticmethod
    def zero():
        return np.zeros(2, dtype=np.float)

    @staticmethod
    def up():
        return np.array([0, 1], dtype=np.float)

    @staticmethod
    def down():
        return np.array([0, -1], dtype=np.float)

    @staticmethod
    def right():
        return np.array([1, 0], dtype=np.float)

    @staticmethod
    def left():
        return np.array([-1, 0], dtype=np.float)

    @staticmethod
    def unit(v):
        return v / Vector.length(v)

    @staticmethod
    def length(v):
        return np.sqrt((v ** 2).sum())

    @staticmethod
    def to_log(v):
        assert v.shape == (2,), 'Expected a 2D numpy.array'
        return dict(x=float(v[0]), y=float(v[1]))

    @staticmethod
    def create(d):
        return np.array([d['x'], d['y']], dtype=np.float)


def direction(orientation):
    '''Create a unit direction vector from an orientation "bearing",
    where orientation=0 is defined as +Y (UP), increases clockwise.
    '''
    return np.array([np.sin(orientation), np.cos(orientation)],
                    dtype=np.float)

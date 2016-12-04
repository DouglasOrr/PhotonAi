import copy
import yaml


def load(default, path=None, args=None):
    '''Load a YAML configuration file.
    '''
    result = copy.deepcopy(default)
    if path is not None:
        with open(path, 'r') as f:
            result.update(yaml.load(f.read()))
    if args is not None:
        for k, v in args.items():
            if v is not None:
                result[k] = v
    return result


def select(d, *keys):
    '''Select keys from a dictionary, and create a new dictionary.
    '''
    return {key: d[key] for key in keys}

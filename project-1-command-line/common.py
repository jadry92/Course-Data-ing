import yaml

__config = None


def config():
    global __config
    if not __config:
        with open('config.yaml', mode='r') as FILE:
            __config = yaml.load(FILE, Loader=yaml.SafeLoader)

    return __config

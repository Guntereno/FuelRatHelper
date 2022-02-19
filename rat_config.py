import json
import os

_app_folder = os.path.join(os.getenv('APPDATA'), 'FuelRatHelper')
_config_file_path = os.path.join(_app_folder, 'rat_config.json')
_values = None

def dump():
    print(f"Rat Config:\n{json.dumps(_values)}")

def init(default):
    global _values

    if os.path.exists(_config_file_path):
        try:
            with open(_config_file_path) as file:
                _values = json.load(file)
                dump()
            return
        except:
            print('Failed to open config file!')

    _values = default
    dump()

def save():
    if _values is None:
        return

    if not os.path.exists(_app_folder):
        os.makedirs(_app_folder)

    with open(_config_file_path, 'w') as file:
        json.dump(_values, file)


def get(id):
    return _values[id]


def set(id, value):
    previous = get(id)
    _values[id] = value
    if(previous != value):
        save()

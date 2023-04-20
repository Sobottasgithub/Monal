import math
from .ast import BuiltinFunction

# returns next numerical index of a given dict
def nextMapIndex(m):
    keys = [k for k in list(m.keys()) if type(k) == int or type(k) == float]
    if len(keys) == 0:
        return 0
    keys.sort()
    return int(keys[-1]) + 1

def mapKeys(m):
    return list(m.keys())

def mapValues(m):
    return list(m.values())

# exports used by ast.py
corelangExports = {
    "len": BuiltinFunction(["map"], [], len),
    # next free numerical key of a map (non-numerical keys are ignored)
    "next": BuiltinFunction(["map"], [], nextMapIndex),
    # list of map keys (numerical and non-numerical ones)
    "keys": BuiltinFunction(["map"], [], mapKeys),
    # list of map values (numerical and non-numerical ones)
    "values": BuiltinFunction(["map"], [], mapValues),
}

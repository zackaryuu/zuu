
from zuu.nested_dict import flatten_dict, unflatten_dict

def test_flatten_dict_deep_complex():
    d = {
        'a': {
            'b': {
                'c': 1,
                'd': {'e': 2, 'f': {'g': 3}}
            },
            'h': 4
        },
        'i': {'j': 5},
        'k': 6
    }
    flat = flatten_dict(d)
    assert flat == {
        'a.b.c': 1,
        'a.b.d.e': 2,
        'a.b.d.f.g': 3,
        'a.h': 4,
        'i.j': 5,
        'k': 6
    }

def test_flatten_dict_with_list_values():
    d = {'a': {'b': [1, 2]}, 'c': {'d': {'e': [3, 4]}}}
    flat = flatten_dict(d)
    assert flat == {'a.b': [1, 2], 'c.d.e': [3, 4]}

def test_flatten_dict_max_depth_complex():
    d = {'x': {'y': {'z': {'w': 10}}}}
    flat = flatten_dict(d, maxDepth=2)
    assert flat == {'x.y.z': {'w': 10}}

def test_unflatten_dict_deep_complex():
    flat = {
        'a.b.c': 1,
        'a.b.d.e': 2,
        'a.b.d.f.g': 3,
        'a.h': 4,
        'i.j': 5,
        'k': 6
    }
    nested = unflatten_dict(flat)
    assert nested == {
        'a': {
            'b': {
                'c': 1,
                'd': {'e': 2, 'f': {'g': 3}}
            },
            'h': 4
        },
        'i': {'j': 5},
        'k': 6
    }

def test_unflatten_dict_with_list_values():
    flat = {'a.b': [1, 2], 'c.d.e': [3, 4]}
    nested = unflatten_dict(flat)
    assert nested == {'a': {'b': [1, 2]}, 'c': {'d': {'e': [3, 4]}}}

def test_flatten_unflatten_roundtrip_complex():
    d = {
        'root': {
            'branch1': {'leaf': 1},
            'branch2': {'leaf': 2, 'subleaf': {'x': 3}}
        },
        'other': 99
    }
    flat = flatten_dict(d)
    nested = unflatten_dict(flat)
    assert nested == d

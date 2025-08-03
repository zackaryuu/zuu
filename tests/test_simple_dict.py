import pytest
from zuu.simple_dict import deep_get, deep_set

def test_deep_get_dict():
    data = {'a': {'b': {'c': 42}}}
    assert deep_get(data, 'a/b/c') == 42

def test_deep_get_list():
    data = {'a': [10, 20, {'b': 30}]}
    assert deep_get(data, 'a/2/b') == 30
    assert deep_get(data, 'a/0') == 10

def test_deep_get_missing_key():
    data = {'a': {'b': 1}}
    with pytest.raises(KeyError):
        deep_get(data, 'a/x')

def test_deep_get_default():
    data = {'a': {'b': 1}}
    assert deep_get(data, 'a/x', default='missing') == 'missing'

def test_deep_set_dict():
    data = {}
    deep_set(data, 'a/b/c', 99)
    assert data == {'a': {'b': {'c': 99}}}

def test_deep_set_list():
    data = {'a': [0, {}, {}]}
    deep_set(data, 'a/1/b', 123)
    assert data['a'][1]['b'] == 123

def test_deep_set_index_error():
    data = {'a': [1]}
    with pytest.raises(IndexError):
        deep_set(data, 'a/5/b', 1)

def test_deep_set_key_error():
    data = 42
    with pytest.raises(KeyError):
        deep_set(data, 'a/b', 1)

def test_deep_pop_dict():
    from zuu.simple_dict import deep_pop
    data = {'a': {'b': {'c': 42}}}
    val = deep_pop(data, 'a/b/c')
    assert val == 42
    assert 'c' not in data['a']['b']

def test_deep_pop_list():
    from zuu.simple_dict import deep_pop
    data = {'a': [10, 20, 30]}
    val = deep_pop(data, 'a/1')
    assert val == 20
    assert data['a'] == [10, 30]

def test_deep_pop_missing():
    from zuu.simple_dict import deep_pop
    data = {'a': {'b': 1}}
    with pytest.raises(KeyError):
        deep_pop(data, 'a/x')
    assert deep_pop(data, 'a/x', default='missing') == 'missing'

def test_deep_setdefault_dict():
    from zuu.simple_dict import deep_setdefault
    data = {'a': {}}
    val = deep_setdefault(data, 'a/b', 123)
    assert val == 123
    assert data['a']['b'] == 123
    # Should not overwrite existing
    val2 = deep_setdefault(data, 'a/b', 999)
    assert val2 == 123

def test_deep_setdefault_list():
    from zuu.simple_dict import deep_setdefault
    data = {'a': [None, 42]}
    val = deep_setdefault(data, 'a/0', 99)
    assert val == 99
    assert data['a'][0] == 99
    # Should not overwrite existing
    val2 = deep_setdefault(data, 'a/1', 100)
    assert val2 == 42


def test_deep_get_2_batch():
    from zuu.simple_dict import deep_get_2
    data = [
        {'x': {'x': 1}},
        {'x': {'x': 2}},
        {'x': {'x': 3}}
    ]
    assert deep_get_2(data, 'x/x') == [1, 2, 3]

def test_deep_get_2_nested_batch():
    from zuu.simple_dict import deep_get_2
    data = {'a': [
        {'b': {'c': 10}},
        {'b': {'c': 20}},
        {'b': {'c': 30}}
    ]}
    assert deep_get_2(data, 'a/b/c') == [10, 20, 30]

def test_deep_get_2_missing_key():
    from zuu.simple_dict import deep_get_2
    data = [
        {'x': {'x': 1}},
        {'y': {'x': 2}},
        {'x': {'x': 3}}
    ]
    # Should fail if any mapping is missing
    with pytest.raises(KeyError):
        deep_get_2(data, 'x/x')
    # With default, should return [1, None, 3]
    assert deep_get_2(data, 'x/x', default=None) == [1, None, 3]

def test_deep_get_2_non_dict_in_list():
    from zuu.simple_dict import deep_get_2
    data = [
        {'x': 1},
        42,
        {'x': 3}
    ]
    # Should fail if any item is not a dict
    with pytest.raises(KeyError):
        deep_get_2(data, 'x')


def test_deep_get_2_multi_level_batch():
    from zuu.simple_dict import deep_get_2
    data = [
        {'a': [{'b': 1}, {'b': 2}]},
        {'a': [{'b': 3}, {'b': 4}]}
    ]
    # Should batch twice: first over top-level, then over 'a' lists
    result = deep_get_2(data, 'a/b')
    assert result == [[1, 2], [3, 4]]

def test_deep_get_2_deeply_nested():
    from zuu.simple_dict import deep_get_2
    data = {
        'root': [
            {'branch': [
                {'leaf': 1},
                {'leaf': 2}
            ]},
            {'branch': [
                {'leaf': 3},
                {'leaf': 4}
            ]}
        ]
    }
    # Should batch over root, then branch, then leaf
    assert deep_get_2(data, 'root/branch/leaf') == [[1, 2], [3, 4]]

def test_deep_delete_dict():
    from zuu.simple_dict import deep_delete
    data = {'a': {'b': {'c': 42}}}
    deep_delete(data, 'a/b/c')
    assert 'c' not in data['a']['b']
    assert data == {'a': {'b': {}}}

def test_deep_delete_list():
    from zuu.simple_dict import deep_delete
    data = {'a': [10, 20, 30]}
    deep_delete(data, 'a/1')
    assert data['a'] == [10, 30]

def test_deep_delete_missing():
    from zuu.simple_dict import deep_delete
    data = {'a': {'b': 1}}
    with pytest.raises(KeyError):
        deep_delete(data, 'a/x')

def test_deep_delete_nested():
    from zuu.simple_dict import deep_delete
    data = {'a': {'b': [1, {'c': 2}, 3]}}
    deep_delete(data, 'a/b/1/c')
    assert data == {'a': {'b': [1, {}, 3]}}

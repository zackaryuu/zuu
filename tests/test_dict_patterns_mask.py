from zuu.dict_patterns import iter_nested_keys

def test_iter_nested_keys_key():
    data = {'a': {'b': 1}, 'c': [2, 3]}
    keys = set(iter_nested_keys(data))
    assert keys == {'a/b', 'c/0', 'c/1'}

def test_iter_nested_keys_value():
    data = {'a': {'b': 1}, 'c': [2, 3]}
    values = set(iter_nested_keys(data, iter_type='value'))
    assert values == {1, 2, 3}

def test_iter_nested_keys_both():
    data = {'a': {'b': 1}, 'c': [2, 3]}
    pairs = set(iter_nested_keys(data, iter_type='both'))
    assert pairs == {('a/b', 1), ('c/0', 2), ('c/1', 3)}

def test_iter_nested_keys_mask_simple():
    data = {'a': {'b': 1}, 'c': [2, 3], 'd': 4}
    # Mask out all keys starting with 'c'
    keys = set(iter_nested_keys(data, masks=['c*']))
    assert keys == {'a/b', 'd'}

def test_iter_nested_keys_mask_nested():
    data = {'a': {'b': 1, 'c': 2}, 'd': {'e': 3}}
    # Mask out all keys ending with '/c'
    keys = set(iter_nested_keys(data, masks=['*/c']))
    assert keys == {'a/b', 'd/e'}

def test_iter_nested_keys_mask_multiple():
    data = {'a': {'b': 1, 'c': 2}, 'd': {'e': 3}, 'f': 4}
    # Mask out 'a/b' and 'f'
    keys = set(iter_nested_keys(data, masks=['a/b', 'f']))
    assert keys == {'a/c', 'd/e'}

def test_iter_nested_keys_mask_value():
    data = {'a': {'b': 1, 'c': 2}, 'd': {'e': 3}}
    # Mask out 'a/c', get values only
    values = set(iter_nested_keys(data, masks=['a/c'], iter_type='value'))
    assert values == {1, 3}

def test_iter_nested_keys_mask_both():
    data = {'a': {'b': 1, 'c': 2}, 'd': {'e': 3}}
    # Mask out 'd/e', get both
    pairs = set(iter_nested_keys(data, masks=['d/e'], iter_type='both'))
    assert pairs == {('a/b', 1), ('a/c', 2)}

def test_iter_nested_keys_mask_list():
    data = {'a': [1, 2, 3], 'b': 4}
    # Mask out 'a/1'
    keys = set(iter_nested_keys(data, masks=['a/1']))
    assert keys == {'a/0', 'a/2', 'b'}

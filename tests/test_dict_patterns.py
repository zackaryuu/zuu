from zuu.dict_patterns import extract_nested_keys

def test_extract_nested_keys_dict():
    data = {'a': {'b': {'c': 1}, 'd': 2}, 'e': 3}
    keys = set(extract_nested_keys(data))
    assert keys == {'a/b/c', 'a/d', 'e'}

def test_extract_nested_keys_list():
    data = [10, {'a': 20}, [30, 40]]
    keys = set(extract_nested_keys(data))
    assert keys == {'0', '1/a', '2/0', '2/1'}

def test_extract_nested_keys_mixed():
    data = {'x': [{'y': 1}, {'z': 2}], 'w': 3}
    keys = set(extract_nested_keys(data))
    assert keys == {'x/0/y', 'x/1/z', 'w'}

def test_extract_nested_keys_custom_separator():
    data = {'a': {'b': 1}}
    keys = set(extract_nested_keys(data, separator='.'))
    assert keys == {'a.b'}

def test_extract_nested_keys_empty():
    assert set(extract_nested_keys({})) == set()
    assert set(extract_nested_keys([])) == set()

def test_extract_nested_keys_deep_nesting():
    # Create a dict nested 50 levels deep: {'a': {'a': ... {'a': 1} ... }}
    depth = 50
    value = 1
    d = value
    for _ in range(depth):
        d = {'a': d}

    d["www"] = "www"
    
    keys = set(extract_nested_keys(d))
    # The only key should be 'a/a/a/.../a' (50 times)
    expected_key = '/'.join(['a'] * depth)
    assert keys == {expected_key, 'www'}

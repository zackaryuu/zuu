import pytest
from zuu.simple_dict import merge_dict

def test_merge_dict_basic():
    d1 = {'a': 1, 'b': 2}
    d2 = {'b': 3, 'c': 4}
    result = merge_dict(d1.copy(), d2)
    assert result == {'a': 1, 'b': 3, 'c': 4}

def test_merge_dict_keep():
    d1 = {'a': 1, 'b': 2}
    d2 = {'b': 3, 'c': 4}
    result = merge_dict(d1.copy(), d2, dict_merge_method='keep')
    assert result == {'a': 1, 'b': 2, 'c': 4}

def test_merge_dict_merge():
    d1 = {'a': 1, 'b': 2}
    d2 = {'b': 3, 'c': 4}
    result = merge_dict(d1.copy(), d2, dict_merge_method='merge')
    assert result == {'a': 1, 'b': [2, 3], 'c': 4}

def test_merge_dict_nested():
    d1 = {'a': {'x': 1}, 'b': 2}
    d2 = {'a': {'y': 2}, 'b': 3}
    result = merge_dict(d1.copy(), d2)
    assert result == {'a': {'x': 1, 'y': 2}, 'b': 3}

def test_merge_dict_list_extend():
    d1 = {'a': [1, 2]}
    d2 = {'a': [3, 4]}
    result = merge_dict(d1.copy(), d2, list_merge_method='extend')
    assert result == {'a': [1, 2, 3, 4]}

def test_merge_dict_list_replace():
    d1 = {'a': [1, 2]}
    d2 = {'a': [3, 4]}
    result = merge_dict(d1.copy(), d2, list_merge_method='replace')
    assert result == {'a': [3, 4]}

def test_merge_dict_list_keep():
    d1 = {'a': [1, 2]}
    d2 = {'a': [3, 4]}
    result = merge_dict(d1.copy(), d2, list_merge_method='keep')
    assert result == {'a': [1, 2]}

def test_merge_dict_list_merge():
    d1 = {'a': [{'x': 1}, {'y': 2}]}
    d2 = {'a': [{'x': 10}, {'y': 20}]}
    result = merge_dict(d1.copy(), d2, list_merge_method='merge')
    assert result == {'a': [[1, 10], [2, 20]]} or result == {'a': [[{'x': 1}, {'x': 10}], [{'y': 2}, {'y': 20}]]}

def test_merge_dict_type_error():
    d1 = {'a': 1}
    d2 = {'a': [1, 2]}
    with pytest.raises(TypeError):
        merge_dict(d1, d2)

def test_merge_dict_empty():
    assert merge_dict() == {}
    assert merge_dict({'a': 1}) == {'a': 1}

def test_merge_dict_list_top_level():
    l1 = [1, 2]
    l2 = [3, 4]
    result = merge_dict(l1.copy(), l2)
    assert result == [1, 2, 3, 4]

def test_merge_dict_multiple_dicts():
    d1 = {'a': 1}
    d2 = {'b': 2}
    d3 = {'c': 3}
    result = merge_dict(d1.copy(), d2, d3)
    assert result == {'a': 1, 'b': 2, 'c': 3}

def test_merge_dict_multiple_lists():
    l1 = [1]
    l2 = [2]
    l3 = [3]
    result = merge_dict(l1.copy(), l2, l3)
    assert result == [1, 2, 3]

def test_merge_dict_deep_merge():
    d1 = {'a': {'b': {'c': 1}}}
    d2 = {'a': {'b': {'d': 2}}}
    result = merge_dict(d1.copy(), d2)
    assert result == {'a': {'b': {'c': 1, 'd': 2}}}

def test_merge_dict_error_on_type_mismatch():
    d1 = {'a': {'b': 1}}
    d2 = {'a': {'b': [1, 2]}}
    with pytest.raises(TypeError):
        merge_dict(d1, d2)

def test_merge_dict_error_on_non_dict_list():
    with pytest.raises(TypeError):
        merge_dict({'a': 1}, 42)
    with pytest.raises(AssertionError):
        merge_dict(42, {'a': 1})


def test_merge_dict_deeply_nested():
    d1 = {'a': {'b': {'c': {'d': {'e': 1}}}}}
    d2 = {'a': {'b': {'c': {'d': {'f': 2}}}}}
    result = merge_dict(d1.copy(), d2)
    assert result == {'a': {'b': {'c': {'d': {'e': 1, 'f': 2}}}}}

def test_merge_dict_large_lists():
    d1 = {'a': list(range(100))}
    d2 = {'a': list(range(100, 200))}
    result = merge_dict(d1.copy(), d2, list_merge_method='extend')
    assert result['a'] == list(range(200))

def test_merge_dict_large_dicts():
    d1 = {str(i): i for i in range(100)}
    d2 = {str(i): i+100 for i in range(50, 150)}
    result = merge_dict(d1.copy(), d2)
    for i in range(50):
        assert result[str(i)] == i
    for i in range(50, 100):
        assert result[str(i)] == i+100
    for i in range(100, 150):
        assert result[str(i)] == i+100

def test_merge_dict_mixed_types():
    d1 = {'a': [{'x': 1}, {'y': 2}], 'b': {'z': [1, 2, 3]}}
    d2 = {'a': [{'x': 10}, {'y': 20}], 'b': {'z': [4, 5]}}
    result = merge_dict(d1.copy(), d2, list_merge_method='extend')
    assert result['a'] == [{'x': 1}, {'y': 2}, {'x': 10}, {'y': 20}]
    assert result['b']['z'] == [1, 2, 3, 4, 5]

def test_merge_dict_merge_mode_complex():
    d1 = {'a': [{'x': 1, 'y': 2}, {'z': 3}]}
    d2 = {'a': [{'x': 10, 'y': 20}, {'z': 30}]}
    result = merge_dict(d1.copy(), d2, list_merge_method='merge')
    assert result['a'] == [
        [{'x': 1, 'y': 2}, {'x': 10, 'y': 20}],
        [{'z': 3}, {'z': 30}]
    ]

def test_merge_dict_edge_empty_dicts():
    d1 = {}
    d2 = {'a': 1}
    result = merge_dict(d1.copy(), d2)
    assert result == {'a': 1}

def test_merge_dict_edge_empty_lists():
    d1 = {'a': []}
    d2 = {'a': [1, 2, 3]}
    result = merge_dict(d1.copy(), d2, list_merge_method='extend')
    assert result == {'a': [1, 2, 3]}

def test_merge_dict_edge_none_values():
    d1 = {'a': None}
    d2 = {'a': 1}
    result = merge_dict(d1.copy(), d2)
    assert result == {'a': 1}


def test_merge_dict_multiple_deep_dicts():
    d1 = {'a': {'b': 1}}
    d2 = {'a': {'c': 2}}
    d3 = {'a': {'d': 3}}
    d4 = {'a': {'e': 4}}
    result = merge_dict(d1.copy(), d2, d3, d4)
    assert result == {'a': {'b': 1, 'c': 2, 'd': 3, 'e': 4}}

def test_merge_dict_multiple_lists_extend():
    l1 = [1, 2]
    l2 = [3, 4]
    l3 = [5, 6]
    l4 = [7, 8]
    result = merge_dict(l1.copy(), l2, l3, l4)
    assert result == [1, 2, 3, 4, 5, 6, 7, 8]

def test_merge_dict_multiple_dicts_complex():
    d1 = {'x': {'y': [1]}}
    d2 = {'x': {'y': [2]}}
    d3 = {'x': {'y': [3]}}
    d4 = {'x': {'z': 4}}
    result = merge_dict(d1.copy(), d2, d3, d4, list_merge_method='extend')
    assert result == {'x': {'y': [1, 2, 3], 'z': 4}}

def test_merge_dict_multiple_dicts_merge_mode():
    d1 = {'a': 1}
    d2 = {'a': 2}
    d3 = {'a': 3}
    result = merge_dict(d1.copy(), d2, d3, dict_merge_method='merge')
    print(result)  # Debugging output
    assert result == {'a': [1, 2, 3]}  

def test_complex_1():
    d1 = {
        "a" : { 
            "b" : [
                {"c": 1},
                {"d": 2}
            ]
        }
    }

    d2 = {
        "a" : { 
            "b" : [
                {"c": 3},
                {"e": 4}
            ]
        }
    }
    d3 = {
        "a" : {
            "b" : [
                {"f": 5}
            ]
        }
    }

    result = merge_dict(d1.copy(), d2, d3, list_merge_method='extend', dict_merge_method='merge')
    assert result == {
        "a": {
            "b": [
                {"c": 1},
                {"d": 2},
                {"c": 3},
                {"e": 4},
                {"f": 5}
            ]
        }
    }
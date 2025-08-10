import pytest
from zuu.simple_string import simple_match

def test_simple_match_exact():
    assert simple_match('abc', 'abc')
    assert not simple_match('abc', 'abcd')
    assert not simple_match('abc', 'ab')

def test_simple_match_wildcard_start():
    assert simple_match('*xyz', 'abcxyz')
    assert simple_match('*xyz', 'xyz')
    assert not simple_match('*xyz', 'xyza')

def test_simple_match_wildcard_end():
    assert simple_match('abc*', 'abcxyz')
    assert simple_match('abc*', 'abc')
    assert not simple_match('abc*', 'aabc')

def test_simple_match_wildcard_middle():
    assert simple_match('ab*yz', 'ab123yz')
    assert simple_match('ab*yz', 'abyz')
    assert not simple_match('ab*yz', 'ab123y')
    assert not simple_match('ab*yz', 'aab123yz')

def test_simple_match_no_wildcard():
    assert simple_match('hello', 'hello')
    assert not simple_match('hello', 'hell')

def test_simple_match_multiple_wildcards():
    with pytest.raises(ValueError):
        simple_match('a*b*c', 'abc')

def test_simple_match_empty_pattern():
    assert simple_match('', '')
    assert not simple_match('', 'a')

def test_simple_match_empty_value():
    assert not simple_match('a*', '')
    assert not simple_match('*a', '')
    assert not simple_match('a', '')

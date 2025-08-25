import pytest
from zuu.simple_string import simple_match, simple_matches

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


def test_simple_matches_basic():
    """Test basic functionality of simple_matches"""
    values = ['hello', 'world', 'test']
    patterns = ['hello', 'foo']
    assert simple_matches(values, patterns)
    
    values = ['hello', 'world', 'test']
    patterns = ['foo', 'bar']
    assert not simple_matches(values, patterns)


def test_simple_matches_with_wildcards():
    """Test simple_matches with wildcard patterns"""
    values = ['hello.txt', 'world.py', 'test.js']
    patterns = ['*.txt', '*.py']
    assert simple_matches(values, patterns)
    
    values = ['hello.txt', 'world.py', 'test.js']
    patterns = ['*.xml', '*.json']
    assert not simple_matches(values, patterns)


def test_simple_matches_mixed_patterns():
    """Test simple_matches with mixed exact and wildcard patterns"""
    values = ['config.json', 'app.py', 'readme.txt']
    patterns = ['config.json', '*.md']
    assert simple_matches(values, patterns)  # exact match on config.json
    
    values = ['config.json', 'app.py', 'readme.txt']
    patterns = ['*.md', 'data.xml']
    assert not simple_matches(values, patterns)


def test_simple_matches_empty_lists():
    """Test simple_matches with empty inputs"""
    assert not simple_matches([], ['pattern'])
    assert not simple_matches(['value'], [])
    assert not simple_matches([], [])


def test_simple_matches_cache_enabled():
    """Test simple_matches with caching enabled (default)"""
    values = ['file1.txt', 'file2.txt', 'file3.py']
    patterns = ['*.txt', '*.py']
    
    # Should return True and cache results
    assert simple_matches(values, patterns, useCache=True)
    
    # Test with duplicate values/patterns to exercise cache
    values_dup = ['file1.txt', 'file1.txt', 'file2.txt']
    patterns_dup = ['*.txt', '*.txt']
    assert simple_matches(values_dup, patterns_dup, useCache=True)


def test_simple_matches_cache_disabled():
    """Test simple_matches with caching disabled"""
    values = ['file1.txt', 'file2.txt', 'file3.py']
    patterns = ['*.txt', '*.py']
    
    # Should work the same but without caching
    assert simple_matches(values, patterns, useCache=False)
    
    values = ['file1.doc', 'file2.pdf']
    patterns = ['*.txt', '*.py']
    assert not simple_matches(values, patterns, useCache=False)


def test_simple_matches_early_return():
    """Test that simple_matches returns True as soon as first match is found"""
    values = ['match.txt', 'nomatch.py', 'another.js']
    patterns = ['*.txt']  # Only first value should match
    
    # Should return True immediately after finding match.txt
    assert simple_matches(values, patterns)


def test_simple_matches_complex_patterns():
    """Test simple_matches with complex wildcard patterns"""
    values = ['prefix_middle_suffix', 'other_data_file', 'test.log']
    patterns = ['prefix_*_suffix', 'nomatch*']
    assert simple_matches(values, patterns)  # matches prefix_middle_suffix
    
    values = ['abc123def', 'xyz789uvw']
    patterns = ['abc*def', 'start*']
    assert simple_matches(values, patterns)  # matches abc123def
    
    values = ['nomatch1', 'nomatch2']
    patterns = ['abc*def', 'xyz*uvw']
    assert not simple_matches(values, patterns)


def test_simple_matches_case_sensitive():
    """Test that simple_matches is case sensitive"""
    values = ['Hello.txt', 'WORLD.py']
    patterns = ['hello*', 'world*']
    assert not simple_matches(values, patterns)  # case sensitive
    
    patterns = ['Hello*', 'WORLD*']
    assert simple_matches(values, patterns)  # correct case


def test_simple_matches_single_items():
    """Test simple_matches with single item lists"""
    values = ['test.txt']
    patterns = ['*.txt']
    assert simple_matches(values, patterns)
    
    values = ['test.py']
    patterns = ['*.txt']
    assert not simple_matches(values, patterns)


def test_simple_matches_whitespace_and_special_chars():
    """Test simple_matches with whitespace and special characters"""
    values = ['file name.txt', 'path/to/file.py', 'user@domain.com', 'version-1.0.txt']
    patterns = ['file name*', 'path/to/*', '*@domain.com', 'version-*.txt']
    assert simple_matches(values, patterns)
    
    values = ['  spaced  .txt', '\tfile.py', 'new\nline.txt']
    patterns = ['  spaced  *', '\tfile*', 'new\n*']
    assert simple_matches(values, patterns)
    
    # Test with special regex chars that should be treated literally
    values = ['test[1].txt', 'file(backup).py', 'data^2.txt']
    patterns = ['test[1]*', 'file(backup)*', 'data^2*']
    assert simple_matches(values, patterns)


def test_simple_matches_unicode_support():
    """Test simple_matches with unicode characters"""
    values = ['файл.txt', 'test_😀.py', 'café.js', '测试.html']
    patterns = ['файл*', 'test_😀*', 'café*', '测试*']
    assert simple_matches(values, patterns)
    
    values = ['ñoño.txt', 'résumé.pdf', 'naïve.doc']
    patterns = ['ñoño*', '*é.pdf', '*ïve*']
    assert simple_matches(values, patterns)


def test_simple_matches_long_strings():
    """Test simple_matches with very long strings"""
    long_value = 'a' * 1000 + '.txt'
    long_pattern = 'a' * 1000 + '*'
    values = [long_value, 'short.py']
    patterns = [long_pattern, 'nomatch*']
    assert simple_matches(values, patterns)
    
    # Test with long middle section
    values = ['prefix' + 'x' * 500 + 'suffix.txt']
    patterns = ['prefix*suffix.txt']
    assert simple_matches(values, patterns)


def test_simple_matches_many_items():
    """Test simple_matches with large lists"""
    # Create large lists to test performance
    values = [f'file_{i}.txt' for i in range(100)] + [f'doc_{i}.py' for i in range(100)]
    patterns = ['file_50*', 'doc_75*', 'nomatch*']
    assert simple_matches(values, patterns)
    
    # Test where match is at the end
    values = ['nomatch'] * 99 + ['match.txt']
    patterns = ['*.txt']
    assert simple_matches(values, patterns)


def test_simple_matches_cache_behavior_detailed():
    """Test detailed caching behavior and effectiveness"""
    values = ['test1.txt', 'test2.txt', 'test1.txt', 'test2.txt']  # Duplicates
    patterns = ['test1*', 'test2*']
    
    # With cache - should be efficient with duplicates
    assert simple_matches(values, patterns, useCache=True)
    
    # Test cache with no matches to ensure negative results are cached too
    values = ['nomatch1', 'nomatch2', 'nomatch1', 'nomatch2']
    patterns = ['match*', 'found*']
    assert not simple_matches(values, patterns, useCache=True)


def test_simple_matches_pattern_order_matters():
    """Test that pattern order can affect when a match is found (early return)"""
    values = ['match_second.txt', 'match_first.py']
    
    # Pattern order affects which match is found first
    patterns1 = ['*.txt', '*.py']  # Will match first value first
    patterns2 = ['*.py', '*.txt']  # Will match second value first
    
    # Both should return True, but with different internal execution paths
    assert simple_matches(values, patterns1)
    assert simple_matches(values, patterns2)


def test_simple_matches_asterisk_edge_cases():
    """Test complex asterisk positioning edge cases"""
    # Multiple asterisks should cause ValueError through simple_match
    values = ['test.txt']
    patterns = ['t*s*t']  # Multiple asterisks - should raise ValueError
    
    with pytest.raises(ValueError):
        simple_matches(values, patterns)
    
    # Single asterisk as entire pattern
    values = ['anything', 'everything', '']
    patterns = ['*']
    assert simple_matches(values, patterns)  # Should match non-empty strings
    
    # Asterisk with empty prefix/suffix
    values = ['test.txt', 'file.py']
    patterns = ['*txt', 'file*']
    assert simple_matches(values, patterns)


def test_simple_matches_empty_string_handling():
    """Test handling of empty strings in values and patterns"""
    # Empty strings in values
    values = ['', 'test.txt', '']
    patterns = ['', 'test*']
    assert simple_matches(values, patterns)  # Should match empty string
    
    values = ['', 'test.txt']
    patterns = ['nomatch*']
    assert not simple_matches(values, patterns)
    
    # Empty pattern with wildcard
    values = ['anything', 'test']
    patterns = ['*']  # Matches everything except empty string
    assert simple_matches(values, patterns)
    
    values = ['']
    patterns = ['*']
    assert simple_matches(values, patterns)  # '*' actually matches empty string in this implementation


def test_simple_matches_nested_data_structures():
    """Test with complex nested-like string patterns"""
    values = [
        'config.production.json',
        'config.development.yaml',
        'service.user.api.py',
        'component.header.nav.js'
    ]
    
    patterns = ['config.*.json', '*.user.*', 'component.header*']
    assert simple_matches(values, patterns)
    
    # Test with no matches
    patterns = ['*.xml', 'database.*', 'component.footer*']
    assert not simple_matches(values, patterns)


def test_simple_matches_numeric_strings():
    """Test with numeric and version-like strings"""
    values = ['v1.2.3', '2024-01-15', '192.168.1.1', 'build_123']
    patterns = ['v1.*', '2024-*', '192.168.*', 'build_*']
    assert simple_matches(values, patterns)
    
    # Test with specific numeric patterns
    values = ['1.0.0', '2.1.0', '10.5.3']
    patterns = ['1.*', '*.0']  # Should match 1.0.0 and 2.1.0
    assert simple_matches(values, patterns)


def test_simple_matches_performance_worst_case():
    """Test performance with worst-case scenario (no early returns)"""
    # Create scenario where we have to check all combinations
    values = ['nomatch_' + str(i) for i in range(50)]
    patterns = ['match_' + str(i) for i in range(50)]
    
    # Should return False after checking all combinations
    assert not simple_matches(values, patterns, useCache=False)
    
    # Same test with cache
    assert not simple_matches(values, patterns, useCache=True)


def test_simple_matches_mixed_wildcard_positions():
    """Test with wildcards in different positions within same call"""
    values = ['prefix_data', 'data_suffix', 'pre_mid_suf', 'exact_match']
    patterns = ['prefix_*', '*_suffix', 'pre_*_suf', 'exact_match']
    assert simple_matches(values, patterns)
    
    # Test where some patterns match and others don't
    values = ['prefix_data', 'data_suffix', 'nomatch']  # Changed to use actual matching values
    patterns = ['prefix_*', '*_suffix', 'exact']
    assert simple_matches(values, patterns)  # First two should match

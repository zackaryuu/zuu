
from zuu.json_io import read_json, write_json, overwrite_json

def test_overwrite_json_preserve(tmp_path):
    # Create original file
    orig = {"a": 1, "b": {"c": 2, "d": 3}, "e": [4, 5]}
    file_path = tmp_path / "test.json"
    write_json(str(file_path), orig)

    # New data to overwrite
    new_data = {"a": 100, "b": {"c": 200, "d": 300}, "e": [400, 500]}
    preserve = ["b/c", "e/1"]
    overwrite_json(str(file_path), new_data, preserve=preserve)
    result = read_json(str(file_path))
    # All keys matching any mask in preserve should be preserved from orig
    from zuu.dict_patterns import iter_nested_keys
    for k, v in iter_nested_keys(orig, iter_type="both", masks=preserve):
        # Get value from result using key path
        parts = k.split("/")
        r = result
        for part in parts[:-1]:
            r = r[part] if not part.isdigit() else r[int(part)]
        last = parts[-1]
        r_val = r[last] if not last.isdigit() else r[int(last)]
        assert r_val == v


def test_overwrite_json_no_preserve(tmp_path):
    orig = {"x": 1, "y": 2}
    file_path = tmp_path / "test2.json"
    write_json(str(file_path), orig)
    new_data = {"x": 10, "y": 20}
    overwrite_json(str(file_path), new_data)
    result = read_json(str(file_path))
    assert result == new_data


def test_overwrite_json_preserve_missing_key(tmp_path):
    orig = {"a": 1}
    file_path = tmp_path / "test3.json"
    write_json(str(file_path), orig)
    new_data = {"a": 2, "b": 3}
    # Preserve a key that doesn't exist in orig
    overwrite_json(str(file_path), new_data, preserve=["b"])
    result = read_json(str(file_path))
    # Should not fail, b should remain as in new_data
    assert result["b"] == 3

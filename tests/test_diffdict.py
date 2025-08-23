import pytest
from zuu.diffdict import DiffDict


class TestDiffDict:
    """Test cases for DiffDict class"""

    def test_init_empty(self):
        """Test initialization with empty dict"""
        dd = DiffDict()
        assert dd._DiffDict__data == {}
        assert dd._DiffDict__changes == []
        assert dd._DiffDict__separator == "/"

    def test_init_with_data(self):
        """Test initialization with existing data"""
        data = {"a": {"b": 1}}
        dd = DiffDict(data)
        assert dd._DiffDict__data == data

    def test_init_custom_separator(self):
        """Test initialization with custom separator"""
        dd = DiffDict(separator=".")
        assert dd._DiffDict__separator == "."

    def test_setitem_new_key(self):
        """Test setting a new key"""
        dd = DiffDict()
        dd["test/key"] = "value"
        
        assert dd._DiffDict__data == {"test": {"key": "value"}}
        assert len(dd._DiffDict__changes) == 1
        
        change = dd._DiffDict__changes[0]
        assert change["key"] == "test/key"
        assert change["previous"] is None
        assert change["new"] == "value"
        assert isinstance(change["stamp"], float)

    def test_setitem_simple_key(self):
        """Test setting a simple (non-nested) key"""
        dd = DiffDict()
        dd["simple"] = "value"
        
        assert dd._DiffDict__data == {"simple": "value"}
        assert len(dd._DiffDict__changes) == 1
        
        change = dd._DiffDict__changes[0]
        assert change["key"] == "simple"
        assert change["previous"] is None
        assert change["new"] == "value"

    def test_setitem_update_existing(self):
        """Test updating an existing key"""
        dd = DiffDict()
        dd["test"] = "old_value"
        dd["test"] = "new_value"
        
        assert dd._DiffDict__data == {"test": "new_value"}
        assert len(dd._DiffDict__changes) == 2
        
        # First change: new key
        change1 = dd._DiffDict__changes[0]
        assert change1["previous"] is None
        assert change1["new"] == "old_value"
        
        # Second change: update
        change2 = dd._DiffDict__changes[1]
        assert change2["previous"] == "old_value"
        assert change2["new"] == "new_value"

    def test_setitem_same_value_no_change(self):
        """Test setting same value doesn't create change record"""
        dd = DiffDict()
        dd["test"] = "value"
        initial_changes = len(dd._DiffDict__changes)
        
        dd["test"] = "value"  # Same value
        assert len(dd._DiffDict__changes) == initial_changes

    def test_setitem_numeric_values(self):
        """Test setting numeric values"""
        dd = DiffDict()
        dd["int"] = 42
        dd["float"] = 3.14
        
        assert len(dd._DiffDict__changes) == 2
        assert dd._DiffDict__changes[0]["new"] == "42"
        assert dd._DiffDict__changes[1]["new"] == "3.14"

    def test_getitem_existing_key(self):
        """Test getting existing keys"""
        dd = DiffDict()
        dd["test/nested"] = "value"
        dd["simple"] = "simple_value"
        
        assert dd["test/nested"] == "value"
        assert dd["simple"] == "simple_value"

    def test_getitem_missing_key(self):
        """Test getting missing key raises KeyError"""
        dd = DiffDict()
        
        with pytest.raises(KeyError, match="Key 'missing' not found"):
            dd["missing"]

    def test_contains_existing_keys(self):
        """Test __contains__ with existing keys"""
        dd = DiffDict()
        dd["test/nested"] = "value"
        dd["simple"] = "simple_value"
        
        assert "test/nested" in dd
        assert "simple" in dd
        assert "test" in dd  # Partial path should exist

    def test_contains_missing_keys(self):
        """Test __contains__ with missing keys"""
        dd = DiffDict()
        dd["test/nested"] = "value"
        
        assert "missing" not in dd
        assert "test/missing" not in dd

    def test_len(self):
        """Test __len__ method"""
        dd = DiffDict()
        assert len(dd) == 0
        
        dd["key1"] = "value1"
        assert len(dd) == 1
        
        dd["nested/key"] = "value2"
        assert len(dd) == 2  # nested creates new top-level key

    def test_delitem_existing_key(self):
        """Test deleting existing key"""
        dd = DiffDict()
        dd["test/nested"] = "value"
        dd["simple"] = "simple_value"
        
        del dd["simple"]
        
        assert "simple" not in dd._DiffDict__data
        assert len(dd._DiffDict__changes) == 3  # 2 sets + 1 delete
        
        delete_change = dd._DiffDict__changes[-1]
        assert delete_change["key"] == "simple"
        assert delete_change["previous"] == "simple_value"
        assert delete_change["new"] is None

    def test_delitem_nested_key(self):
        """Test deleting nested key"""
        dd = DiffDict()
        dd["test/nested"] = "value"
        
        del dd["test/nested"]
        
        assert dd._DiffDict__data == {"test": {}}
        
        delete_change = dd._DiffDict__changes[-1]
        assert delete_change["key"] == "test/nested"
        assert delete_change["previous"] == "value"
        assert delete_change["new"] is None

    def test_delitem_missing_key(self):
        """Test deleting missing key raises KeyError"""
        dd = DiffDict()
        
        with pytest.raises(KeyError, match="Key 'missing' not found"):
            del dd["missing"]

    def test_pop_existing_key(self):
        """Test popping existing key"""
        dd = DiffDict()
        dd["test"] = "value"
        
        result = dd.pop("test")
        
        assert result == "value"
        assert "test" not in dd._DiffDict__data
        assert len(dd._DiffDict__changes) == 2  # 1 set + 1 pop

    def test_pop_missing_key_no_default(self):
        """Test popping missing key without default raises KeyError"""
        dd = DiffDict()
        
        with pytest.raises(KeyError, match="Key 'missing' not found"):
            dd.pop("missing")

    def test_pop_missing_key_with_default(self):
        """Test popping missing key with default returns default"""
        dd = DiffDict()
        
        result = dd.pop("missing", "default_value")
        
        assert result == "default_value"
        assert len(dd._DiffDict__changes) == 0  # No change recorded

    def test_pop_nested_key(self):
        """Test popping nested key"""
        dd = DiffDict()
        dd["test/nested"] = "nested_value"
        
        result = dd.pop("test/nested")
        
        assert result == "nested_value"
        assert dd._DiffDict__data == {"test": {}}

    def test_use_hex_check_property(self):
        """Test useHexCheck property getter/setter"""
        dd = DiffDict()
        
        assert not dd.useHexCheck
        
        dd.useHexCheck = True
        assert dd.useHexCheck

    def test_no_timestamp(self):
        """Test initialization without timestamps"""
        dd = DiffDict(stamp=False)
        dd["test"] = "value"
        
        change = dd._DiffDict__changes[0]
        assert change["stamp"] is None

    def test_custom_separator(self):
        """Test custom separator usage"""
        dd = DiffDict(separator=".")
        dd["test.nested.key"] = "value"
        
        assert dd._DiffDict__data == {"test": {"nested": {"key": "value"}}}
        assert dd["test.nested.key"] == "value"
        assert "test.nested.key" in dd

    def test_complex_object_hashing(self):
        """Test setting complex objects that require hashing"""
        dd = DiffDict()
        complex_obj = {"nested": ["list", "data"], "other": 123}
        
        dd["complex"] = complex_obj
        
        change = dd._DiffDict__changes[0]
        assert change["key"] == "complex"
        assert change["previous"] is None
        # Should be a hash string for complex objects
        assert isinstance(change["new"], str)
        assert len(change["new"]) > 10  # Hash should be reasonably long

    def test_multiple_operations_sequence(self):
        """Test a sequence of multiple operations"""
        dd = DiffDict()
        
        # Set initial values
        dd["user/name"] = "John"
        dd["user/age"] = 25
        dd["settings/theme"] = "dark"
        
        # Update a value
        dd["user/name"] = "Jane"
        
        # Delete a value
        del dd["settings/theme"]
        
        # Pop a value
        age = dd.pop("user/age")
        
        # Verify final state
        assert dd._DiffDict__data == {"user": {"name": "Jane"}, "settings": {}}
        assert age == 25
        assert len(dd._DiffDict__changes) == 6  # 3 sets + 1 update + 1 delete + 1 pop
        
        # Verify all changes are recorded
        changes = dd._DiffDict__changes
        assert changes[0]["key"] == "user/name" and changes[0]["new"] == "John"
        assert changes[1]["key"] == "user/age" and changes[1]["new"] == "25"
        assert changes[2]["key"] == "settings/theme" and changes[2]["new"] == "dark"
        assert changes[3]["key"] == "user/name" and changes[3]["previous"] == "John" and changes[3]["new"] == "Jane"
        assert changes[4]["key"] == "settings/theme" and changes[4]["new"] is None
        assert changes[5]["key"] == "user/age" and changes[5]["new"] is None

    def test_diffset_type_validation(self):
        """Test that changes conform to DiffSet TypedDict structure"""
        dd = DiffDict()
        dd["test"] = "value"
        
        change = dd._DiffDict__changes[0]
        
        # Verify all required keys are present
        assert "key" in change
        assert "stamp" in change
        assert "previous" in change
        assert "new" in change
        
        # Verify types
        assert isinstance(change["key"], str)
        assert isinstance(change["stamp"], (float, type(None)))
        assert change["previous"] is None or isinstance(change["previous"], str)
        assert change["new"] is None or isinstance(change["new"], str)


class TestDiffDictNewFeatures:
    """Test cases for new DiffDict features"""

    def test_prune_changes(self):
        """Test pruning changes to keep only recent ones"""
        dd = DiffDict()
        
        # Add many changes
        for i in range(100):
            dd[f"key{i}"] = f"value{i}"
        
        assert len(dd.changes["all"]) == 100
        
        # Prune to keep only 10
        dd.prune_changes(10)
        
        assert len(dd.changes["all"]) == 10
        # Should keep the last 10
        assert dd.changes["all"][0]["key"] == "key90"
        assert dd.changes["all"][-1]["key"] == "key99"

    def test_add_callback(self):
        """Test adding and triggering callbacks"""
        dd = DiffDict()
        callback_calls = []
        
        def test_callback(diff_dict):
            callback_calls.append(len(diff_dict.changes["all"]))
        
        dd.add_callback(test_callback)
        
        dd["test1"] = "value1"
        dd["test2"] = "value2"
        dd.pop("test1")
        
        # Should have been called 3 times
        assert callback_calls == [1, 2, 3]

    def test_changes_property(self):
        """Test the changes property returns correct structure"""
        dd = DiffDict()
        
        # Initially empty
        assert dd.changes["all"] == []
        assert dd.changes["last"] is None
        
        dd["test"] = "value"
        
        # After one change
        assert len(dd.changes["all"]) == 1
        assert dd.changes["last"]["key"] == "test"
        
        dd["test2"] = "value2"
        
        # After two changes
        assert len(dd.changes["all"]) == 2
        assert dd.changes["last"]["key"] == "test2"

    def test_changes_property_immutable(self):
        """Test that changes property returns read-only data"""
        dd = DiffDict()
        dd["test"] = "value"
        
        changes = dd.changes
        
        # The MappingProxyType should prevent modification of the mapping itself
        with pytest.raises(TypeError):
            changes["new_key"] = "should_fail"


class TestDiffDictStress:
    """Stress tests for DiffDict performance and reliability"""

    def test_large_number_of_operations(self):
        """Test handling thousands of operations"""
        dd = DiffDict()
        
        # Perform 10,000 operations
        operations = 10000
        for i in range(operations):
            if i % 3 == 0:
                dd[f"key{i}"] = f"value{i}"
            elif i % 3 == 1 and i > 0:
                # Update existing key
                dd[f"key{i-1}"] = f"updated_value{i}"
            else:
                # Try to delete (may not exist, that's ok)
                try:
                    del dd[f"key{i-2}"]
                except KeyError:
                    pass
        
        # Verify we have the expected number of changes
        assert len(dd.changes["all"]) > 0
        assert len(dd.changes["all"]) <= operations
        
        # Test pruning works with large datasets
        dd.prune_changes(100)
        assert len(dd.changes["all"]) == 100

    def test_deep_nested_keys_stress(self):
        """Test with very deeply nested keys"""
        dd = DiffDict()
        
        # Create deeply nested keys
        depth = 50
        for i in range(100):
            key_parts = [f"level{j}" for j in range(depth)]
            key = "/".join(key_parts) + f"/final{i}"
            dd[key] = f"deep_value_{i}"
        
        # Verify all keys exist and can be retrieved
        for i in range(100):
            key_parts = [f"level{j}" for j in range(depth)]
            key = "/".join(key_parts) + f"/final{i}"
            assert key in dd
            assert dd[key] == f"deep_value_{i}"
        
        # Test deletion of deeply nested keys
        for i in range(0, 100, 2):  # Delete every other key
            key_parts = [f"level{j}" for j in range(depth)]
            key = "/".join(key_parts) + f"/final{i}"
            del dd[key]
            assert key not in dd

    def test_large_data_structures(self):
        """Test with large complex data structures"""
        dd = DiffDict()
        
        # Create large complex objects
        for i in range(100):
            large_dict = {
                f"subkey_{j}": {
                    "data": list(range(100)),
                    "metadata": {
                        "timestamp": f"2024-01-{j:02d}T00:00:00",
                        "tags": [f"tag{k}" for k in range(20)],
                        "nested": {"deep": {"deeper": f"value_{i}_{j}"}}
                    }
                } for j in range(10)
            }
            dd[f"complex_object_{i}"] = large_dict
        
        # Verify objects are stored and hashed correctly
        assert len(dd.changes["all"]) == 100
        
        # Update some objects (create new objects instead of modifying in place)
        for i in range(0, 100, 10):
            key = f"complex_object_{i}"
            current = dd[key].copy()  # Make a copy to ensure new object
            current["new_field"] = "added_data"
            dd[key] = current
        
        # Should have 10 additional changes
        assert len(dd.changes["all"]) == 110

    def test_rapid_key_creation_and_deletion(self):
        """Test rapid creation and deletion of keys"""
        dd = DiffDict()
        
        # Rapidly create keys
        for cycle in range(10):
            # Create 1000 keys
            for i in range(1000):
                dd[f"temp_{cycle}_{i}"] = f"value_{cycle}_{i}"
            
            # Delete half of them
            for i in range(0, 1000, 2):
                del dd[f"temp_{cycle}_{i}"]
            
            # Update the remaining ones
            for i in range(1, 1000, 2):
                dd[f"temp_{cycle}_{i}"] = f"updated_value_{cycle}_{i}"
        
        # Should have a lot of changes
        assert len(dd.changes["all"]) > 10000
        
        # Prune to manageable size
        dd.prune_changes(1000)
        assert len(dd.changes["all"]) == 1000

    def test_callback_stress(self):
        """Test callback performance with many callbacks and operations"""
        dd = DiffDict()
        callback_counts = []
        
        # Add multiple callbacks
        for i in range(10):
            counter = [0]  # Use list to make it mutable in closure
            
            def make_callback(counter_ref, callback_id):
                def callback(diff_dict):
                    counter_ref[0] += 1
                return callback
            
            callback = make_callback(counter, i)
            dd.add_callback(callback)
            callback_counts.append(counter)
        
        # Perform many operations
        for i in range(500):
            dd[f"stress_key_{i}"] = f"stress_value_{i}"
            if i % 10 == 0 and i > 0:
                del dd[f"stress_key_{i-10}"]
        
        # Each callback should have been called for each change
        expected_calls = len(dd.changes["all"])
        for counter in callback_counts:
            assert counter[0] == expected_calls

    def test_memory_efficiency_with_pruning(self):
        """Test memory efficiency when using change pruning"""
        dd = DiffDict()
        
        # Generate many changes
        for i in range(5000):
            dd[f"key_{i}"] = f"value_{i}"
            
            # Prune every 100 operations to keep memory usage down
            if i % 100 == 99:
                dd.prune_changes(50)
                assert len(dd.changes["all"]) == 50
        
        # Final check
        assert len(dd.changes["all"]) == 50
        # Should contain the most recent changes
        last_change = dd.changes["last"]
        assert last_change["key"] == "key_4999"
        assert last_change["new"] == "value_4999"

    def test_edge_case_separators(self):
        """Test with unusual separators and key patterns"""
        separators = [".", "->", "::", "|||", "🔑"]
        
        for sep in separators:
            dd = DiffDict(separator=sep)
            
            # Create keys with the separator
            test_key = f"root{sep}middle{sep}leaf"
            dd[test_key] = "separator_test"
            
            assert dd[test_key] == "separator_test"
            assert test_key in dd
            
            # Test deletion
            del dd[test_key]
            assert test_key not in dd

    def test_concurrent_like_operations(self):
        """Test operations that might simulate concurrent access patterns"""
        dd = DiffDict()
        
        # Simulate multiple "threads" working on different key spaces
        operations_per_thread = 1000
        num_simulated_threads = 5
        
        for thread_id in range(num_simulated_threads):
            for op_id in range(operations_per_thread):
                key_base = f"thread_{thread_id}_key_{op_id}"
                
                # Mix of operations
                if op_id % 4 == 0:
                    dd[key_base] = f"value_{thread_id}_{op_id}"
                elif op_id % 4 == 1:
                    dd[f"{key_base}_nested/deep"] = f"nested_{thread_id}_{op_id}"
                elif op_id % 4 == 2 and op_id > 0:
                    try:
                        prev_key = f"thread_{thread_id}_key_{op_id-1}"
                        if prev_key in dd:
                            dd[prev_key] = f"updated_{thread_id}_{op_id}"
                    except KeyError:
                        pass
                else:
                    try:
                        if op_id > 3:
                            del_key = f"thread_{thread_id}_key_{op_id-4}"
                            if del_key in dd:
                                del dd[del_key]
                    except KeyError:
                        pass
        
        # Should have processed many operations successfully
        total_expected_ops = operations_per_thread * num_simulated_threads
        assert len(dd.changes["all"]) > 0
        assert len(dd.changes["all"]) <= total_expected_ops
        
        # Test that we can still access and modify data correctly
        dd["final_test"] = "final_value"
        assert dd["final_test"] == "final_value"

    def test_hash_collision_resistance(self):
        """Test behavior with potential hash collisions"""
        dd = DiffDict()
        
        # Create many similar objects that might cause hash collisions
        base_obj = {"common_field": "common_value"}
        
        for i in range(1000):
            obj = base_obj.copy()
            obj[f"unique_field_{i}"] = f"unique_value_{i}"
            # Add slight variations
            obj["variation"] = i % 100
            obj["data"] = [i, i*2, i*3]
            
            dd[f"collision_test_{i}"] = obj
        
        # Verify all objects are correctly stored and differentiated
        for i in range(1000):
            retrieved = dd[f"collision_test_{i}"]
            assert retrieved[f"unique_field_{i}"] == f"unique_value_{i}"
            assert retrieved["variation"] == i % 100
            assert retrieved["data"] == [i, i*2, i*3]
        
        # Test updates to ensure hash comparison works
        for i in range(0, 1000, 100):
            key = f"collision_test_{i}"
            obj = dd[key].copy()  # Create a new object to ensure change detection
            obj["updated"] = True
            dd[key] = obj  # Should trigger a change since object is modified
        
        # Should have 1000 initial + 10 updates = 1010 changes
        assert len(dd.changes["all"]) == 1010

import pytest
from zuu.diffdict import DiffDict


class TestDiffDictAdvancedFeatures:
    """Test cases for advanced DiffDict features like callbacks, pruning, updateAtKey"""

    def test_updateatkey_basic_functionality(self):
        """Test basic updateAtKey functionality"""
        dd = DiffDict()
        
        # Set initial data
        test_list = [1, 2, 3]
        test_dict = {"a": 1, "b": 2}
        
        dd["my_list"] = test_list
        dd["nested/dict"] = test_dict
        
        initial_changes = len(dd.changes["all"])
        assert initial_changes == 2
        
        # Modify objects externally
        stored_list = dd["my_list"]
        stored_dict = dd["nested/dict"]
        
        stored_list.append(4)
        stored_dict["c"] = 3
        
        # Changes shouldn't be detected yet
        assert len(dd.changes["all"]) == initial_changes
        
        # Use updateAtKey to detect changes
        dd.updateAtKey("my_list")
        assert len(dd.changes["all"]) == initial_changes + 1
        
        change = dd.changes["last"]
        assert change["key"] == "my_list"
        assert change["previous"] != change["new"]  # Should be different hashes
        
        dd.updateAtKey("nested/dict")
        assert len(dd.changes["all"]) == initial_changes + 2
        
        change = dd.changes["last"]
        assert change["key"] == "nested/dict"

    def test_updateatkey_no_change_detection(self):
        """Test updateAtKey when no changes have been made"""
        dd = DiffDict()
        dd["test"] = [1, 2, 3]
        
        initial_changes = len(dd.changes["all"])
        
        # Call updateAtKey without modifying the object
        dd.updateAtKey("test")
        
        # Should not add a new change since the object hasn't changed
        assert len(dd.changes["all"]) == initial_changes

    def test_updateatkey_missing_key(self):
        """Test updateAtKey with non-existent key"""
        dd = DiffDict()
        
        with pytest.raises(KeyError, match="Key 'nonexistent' not found"):
            dd.updateAtKey("nonexistent")
        
        with pytest.raises(KeyError, match="Key 'nested/missing' not found"):
            dd.updateAtKey("nested/missing")

    def test_updateatkey_with_nested_keys(self):
        """Test updateAtKey with deeply nested keys"""
        dd = DiffDict()
        
        nested_data = {
            "level1": {
                "level2": {
                    "data": [1, 2, 3],
                    "info": {"count": 3}
                }
            }
        }
        
        dd["deep/nested/structure"] = nested_data
        initial_changes = len(dd.changes["all"])
        
        # Modify the nested structure
        retrieved = dd["deep/nested/structure"]
        retrieved["level1"]["level2"]["data"].append(4)
        retrieved["level1"]["level2"]["info"]["count"] = 4
        retrieved["level1"]["new_field"] = "added"
        
        # Detect the change
        dd.updateAtKey("deep/nested/structure")
        assert len(dd.changes["all"]) == initial_changes + 1
        
        change = dd.changes["last"]
        assert change["key"] == "deep/nested/structure"
        assert change["previous"] != change["new"]

    def test_updateatkey_with_callbacks(self):
        """Test updateAtKey triggers callbacks"""
        dd = DiffDict()
        callback_calls = []
        
        def test_callback(diff_dict):
            callback_calls.append({
                "change_count": len(diff_dict.changes["all"]),
                "last_key": diff_dict.changes["last"]["key"] if diff_dict.changes["last"] else None
            })
        
        dd.add_callback(test_callback)
        
        # Set initial data
        dd["test"] = {"data": [1, 2, 3]}
        assert len(callback_calls) == 1
        
        # Modify externally and use updateAtKey
        dd["test"]["data"].append(4)
        dd.updateAtKey("test")
        
        assert len(callback_calls) == 2
        assert callback_calls[-1]["last_key"] == "test"

    def test_updateatkey_multiple_modifications(self):
        """Test updateAtKey with multiple modifications to the same object"""
        dd = DiffDict()
        
        test_obj = {"items": [], "counter": 0}
        dd["tracker"] = test_obj
        
        initial_changes = len(dd.changes["all"])
        
        # Make multiple modifications
        stored_obj = dd["tracker"]
        stored_obj["items"].extend([1, 2, 3])
        stored_obj["counter"] = 3
        
        dd.updateAtKey("tracker")
        assert len(dd.changes["all"]) == initial_changes + 1
        
        # Make more modifications
        stored_obj["items"].append(4)
        stored_obj["counter"] = 4
        stored_obj["new_field"] = "test"
        
        dd.updateAtKey("tracker")
        assert len(dd.changes["all"]) == initial_changes + 2
        
        # Each change should have different hashes (the new hash from first change should be previous hash of second)
        changes = dd.changes["all"][-2:]
        # The sequence should be: old -> new (first change), then new -> newer (second change)
        # So changes[0]["new"] should equal changes[1]["previous"]
        assert changes[0]["new"] == changes[1]["previous"]
        assert changes[1]["previous"] != changes[1]["new"]

    def test_updateatkey_with_different_object_types(self):
        """Test updateAtKey with various object types"""
        dd = DiffDict()
        
        # Test with different mutable object types
        test_data = {
            "list": [1, 2, 3],
            "dict": {"a": 1},
            "nested": {"list": [{"inner": "value"}]},
            "set_like": {"unique", "values"},  # This will be converted to string
        }
        
        for key, value in test_data.items():
            dd[key] = value
        
        initial_changes = len(dd.changes["all"])
        
        # Modify each type
        dd["list"].append(4)
        dd["dict"]["b"] = 2
        dd["nested"]["list"][0]["inner"] = "modified"
        # set_like can't be modified in place since it becomes a string representation
        
        # Check each modification
        dd.updateAtKey("list")
        dd.updateAtKey("dict")
        dd.updateAtKey("nested")
        
        # Should have 3 additional changes
        assert len(dd.changes["all"]) == initial_changes + 3

    def test_prune_changes_advanced(self):
        """Test advanced pruning scenarios"""
        dd = DiffDict()
        
        # Create many changes
        for i in range(1000):
            dd[f"key{i}"] = f"value{i}"
        
        assert len(dd.changes["all"]) == 1000
        
        # Prune to different sizes
        dd.prune_changes(500)
        assert len(dd.changes["all"]) == 500
        assert dd.changes["all"][0]["key"] == "key500"
        assert dd.changes["all"][-1]["key"] == "key999"
        
        # Add more changes and prune again
        for i in range(1000, 1100):
            dd[f"key{i}"] = f"value{i}"
        
        assert len(dd.changes["all"]) == 600  # 500 + 100
        
        dd.prune_changes(50)
        assert len(dd.changes["all"]) == 50
        assert dd.changes["all"][0]["key"] == "key1050"
        assert dd.changes["all"][-1]["key"] == "key1099"

    def test_prune_changes_edge_cases(self):
        """Test pruning edge cases"""
        dd = DiffDict()
        
        # Test pruning when there are fewer changes than keep
        dd["test1"] = "value1"
        dd["test2"] = "value2"
        
        dd.prune_changes(10)  # Keep more than we have
        assert len(dd.changes["all"]) == 2
        
        # Test pruning to 0
        dd.prune_changes(0)
        assert len(dd.changes["all"]) == 0
        
        # Add more changes after pruning to 0
        dd["test3"] = "value3"
        assert len(dd.changes["all"]) == 1

    def test_multiple_callbacks_advanced(self):
        """Test advanced callback scenarios"""
        dd = DiffDict()
        
        # Different types of callbacks
        callback_logs = {
            "counter": [0],
            "key_tracker": [],
            "change_analyzer": []
        }
        
        def counter_callback(diff_dict):
            callback_logs["counter"][0] += 1
        
        def key_tracker_callback(diff_dict):
            if diff_dict.changes["last"]:
                callback_logs["key_tracker"].append(diff_dict.changes["last"]["key"])
        
        def change_analyzer_callback(diff_dict):
            last_change = diff_dict.changes["last"]
            if last_change:
                callback_logs["change_analyzer"].append({
                    "type": "new" if last_change["previous"] is None else "update" if last_change["new"] is not None else "delete",
                    "key": last_change["key"]
                })
        
        # Add all callbacks
        dd.add_callback(counter_callback)
        dd.add_callback(key_tracker_callback)
        dd.add_callback(change_analyzer_callback)
        
        # Perform various operations
        dd["new_item"] = "value"
        dd["new_item"] = "updated_value"
        del dd["new_item"]
        
        # Test with updateAtKey
        dd["mutable"] = [1, 2, 3]
        dd["mutable"].append(4)
        dd.updateAtKey("mutable")
        
        # Verify all callbacks were called correctly
        assert callback_logs["counter"][0] == 5  # 5 operations
        assert callback_logs["key_tracker"] == ["new_item", "new_item", "new_item", "mutable", "mutable"]
        assert len(callback_logs["change_analyzer"]) == 5
        assert callback_logs["change_analyzer"][0]["type"] == "new"
        assert callback_logs["change_analyzer"][1]["type"] == "update"
        assert callback_logs["change_analyzer"][2]["type"] == "delete"

    def test_changes_property_advanced(self):
        """Test advanced usage of changes property"""
        dd = DiffDict()
        
        # Test with empty changes
        changes = dd.changes
        assert changes["all"] == []
        assert changes["last"] is None
        
        # Add some changes
        dd["item1"] = "value1"
        dd["item2"] = {"nested": "data"}
        
        changes = dd.changes
        assert len(changes["all"]) == 2
        assert changes["last"]["key"] == "item2"
        
        # Test immutability - should not be able to modify the proxy
        with pytest.raises(TypeError):
            changes["new_field"] = "should_fail"
        
        # Test that the proxy is a snapshot, not live updating
        dd["item3"] = "value3"
        # Need to get a fresh reference to see the new changes
        new_changes = dd.changes
        assert len(new_changes["all"]) == 3  # Fresh reference shows updates
        assert new_changes["last"]["key"] == "item3"

    def test_integration_updateatkey_with_all_features(self):
        """Integration test combining updateAtKey with all other features"""
        dd = DiffDict(stamp=True)
        
        # Set up callbacks
        operation_log = []
        
        def logger_callback(diff_dict):
            last = diff_dict.changes["last"]
            if last:
                operation_log.append(f"{last['key']}: {last['previous']} -> {last['new']}")
        
        dd.add_callback(logger_callback)
        
        # Create complex nested structure
        complex_data = {
            "users": [
                {"id": 1, "name": "Alice", "settings": {"theme": "dark"}},
                {"id": 2, "name": "Bob", "settings": {"theme": "light"}}
            ],
            "metadata": {"version": "1.0", "features": ["auth", "dashboard"]}
        }
        
        dd["app_state"] = complex_data
        assert len(operation_log) == 1
        
        # Modify the structure externally
        app_data = dd["app_state"]
        app_data["users"][0]["name"] = "Alice Updated"
        app_data["users"].append({"id": 3, "name": "Charlie", "settings": {"theme": "auto"}})
        app_data["metadata"]["features"].append("notifications")
        app_data["metadata"]["version"] = "1.1"
        
        # Use updateAtKey to detect changes
        dd.updateAtKey("app_state")
        assert len(operation_log) == 2
        
        # Prune changes to keep memory usage low
        dd.prune_changes(10)
        
        # Add more changes
        for i in range(20):
            dd[f"temp_{i}"] = f"temp_value_{i}"
        
        # Should have triggered callbacks for each
        assert len(operation_log) >= 22
        
        # Final prune
        dd.prune_changes(5)
        assert len(dd.changes["all"]) == 5
        
        # Verify the system still works after pruning
        dd["final_test"] = "final_value"
        assert dd["final_test"] == "final_value"
        assert len(operation_log) >= 23

    def test_updateatkey_performance_simulation(self):
        """Simulate performance scenarios with updateAtKey"""
        dd = DiffDict()
        
        # Create many objects that will be modified externally
        for i in range(100):
            dd[f"object_{i}"] = {"data": list(range(10)), "metadata": {"id": i}}
        
        initial_changes = len(dd.changes["all"])
        
        # Simulate external modifications to many objects
        for i in range(0, 100, 5):  # Every 5th object
            obj = dd[f"object_{i}"]
            obj["data"].extend(range(10, 15))
            obj["metadata"]["modified"] = True
            obj["new_field"] = f"added_{i}"
        
        # Use updateAtKey to detect all changes
        modified_count = 0
        for i in range(0, 100, 5):
            old_len = len(dd.changes["all"])
            dd.updateAtKey(f"object_{i}")
            if len(dd.changes["all"]) > old_len:
                modified_count += 1
        
        # Should have detected all 20 modifications
        assert modified_count == 20
        assert len(dd.changes["all"]) == initial_changes + 20
        
        # Test that unmodified objects don't create changes
        for i in range(1, 100, 5):  # Objects we didn't modify
            old_len = len(dd.changes["all"])
            dd.updateAtKey(f"object_{i}")
            assert len(dd.changes["all"]) == old_len  # Should be same

    def test_updateatkey_with_custom_separator(self):
        """Test updateAtKey with custom separator"""
        dd = DiffDict(separator=".")
        
        test_data = {"nested": {"deep": {"value": [1, 2, 3]}}}
        dd["root.data"] = test_data
        
        initial_changes = len(dd.changes["all"])
        
        # Modify the nested structure
        retrieved = dd["root.data"]
        retrieved["nested"]["deep"]["value"].append(4)
        retrieved["nested"]["new"] = "added"
        
        # Use updateAtKey with dot separator
        dd.updateAtKey("root.data")
        
        assert len(dd.changes["all"]) == initial_changes + 1
        change = dd.changes["last"]
        assert change["key"] == "root.data"

    def test_update_all_basic_functionality(self):
        """Test update_all method detects all external changes"""
        dd = DiffDict()
        
        # Add multiple mutable objects
        list1 = [1, 2, 3]
        list2 = ["a", "b"]
        dict1 = {"count": 0}
        primitive = "unchanged"
        
        dd["list1"] = list1
        dd["list2"] = list2
        dd["dict1"] = dict1
        dd["primitive"] = primitive
        
        initial_changes = len(dd.changes["all"])
        assert initial_changes == 4
        
        # Make external modifications to some objects
        list1.append(4)
        list1.extend([5, 6])
        dict1["count"] = 10
        dict1["new_field"] = "added"
        # list2 and primitive remain unchanged
        
        # Call update_all - now returns a dict
        result = dd.update_all()
        changed_keys = result["changed"]
        
        # Should detect changes in list1 and dict1, but not list2 or primitive
        assert len(changed_keys) == 2
        assert "list1" in changed_keys
        assert "dict1" in changed_keys
        assert "list2" not in changed_keys
        assert "primitive" not in changed_keys
        
        # Total changes should have increased by 2
        assert len(dd.changes["all"]) == initial_changes + 2

    def test_update_all_no_changes(self):
        """Test update_all when no external changes have been made"""
        dd = DiffDict()
        
        dd["test1"] = [1, 2, 3]
        dd["test2"] = {"key": "value"}
        dd["test3"] = "string"
        
        initial_changes = len(dd.changes["all"])
        
        # Call update_all without making any external changes
        result = dd.update_all()
        changed_keys = result["changed"]
        
        assert changed_keys == []
        assert len(dd.changes["all"]) == initial_changes

    def test_update_all_empty_dict(self):
        """Test update_all on empty DiffDict"""
        dd = DiffDict()
        
        result = dd.update_all()
        
        assert result["changed"] == []
        assert result["new_tracked"] == []
        assert result["orphaned"] == []
        assert len(dd.changes["all"]) == 0

    def test_update_all_with_deleted_keys(self):
        """Test update_all handles keys that were deleted externally"""
        dd = DiffDict()
        
        # Add some data
        dd["key1"] = [1, 2, 3]
        dd["key2"] = {"data": "test"}
        
        # Simulate external deletion by removing from internal data
        # (This is an edge case that shouldn't normally happen, but we should handle it gracefully)
        dd._DiffDict__data.pop("key1", None)
        
        # update_all should handle the missing key gracefully
        result = dd.update_all()
        
        # key1 should be in orphaned since it was deleted
        # key2 should not be in changed since it wasn't modified
        assert "key1" not in result["changed"]
        assert "key2" not in result["changed"]
        assert "key1" in result["orphaned"]

    def test_update_all_with_callbacks(self):
        """Test update_all triggers callbacks for detected changes"""
        dd = DiffDict()
        callback_calls = []
        
        def track_changes(diff_dict):
            callback_calls.append(diff_dict.changes["last"]["key"])
        
        dd.add_callback(track_changes)
        
        # Add data
        list_data = [1, 2, 3]
        dict_data = {"count": 0}
        dd["list_data"] = list_data
        dd["dict_data"] = dict_data
        
        # Clear callback history after initial setup
        callback_calls.clear()
        
        # Make external changes
        list_data.append(4)
        dict_data["count"] = 5
        
        # Call update_all
        result = dd.update_all()
        changed_keys = result["changed"]
        
        # Callbacks should have been triggered for each detected change
        assert len(callback_calls) == len(changed_keys)
        assert "list_data" in callback_calls
        assert "dict_data" in callback_calls

    def test_update_all_with_dataref_manipulation(self):
        """Test update_all with dataref.update() and include_new_keys parameter"""
        dd = DiffDict()
        
        # Normal tracked data
        dd["tracked"] = [1, 2, 3]
        
        # Add untracked data via dataref
        dd.dataref.update({"untracked": [4, 5, 6]})
        
        # Modify both
        dd["tracked"].append(99)
        dd.dataref["untracked"].append(88)
        
        # Basic update_all should only detect tracked changes
        result = dd.update_all()
        assert len(result["changed"]) == 1
        assert "tracked" in result["changed"]
        assert len(result["new_tracked"]) == 0
        
        # Enhanced update_all should detect and track new keys
        result = dd.update_all(include_new_keys=True)
        assert len(result["new_tracked"]) == 1
        assert "untracked" in result["new_tracked"]

    def test_update_all_simple_backward_compatibility(self):
        """Test update_all_simple() method for backward compatibility"""
        dd = DiffDict()
        
        dd["test1"] = [1, 2, 3]
        dd["test2"] = {"count": 0}
        
        # Make changes
        dd["test1"].append(4)
        dd["test2"]["count"] = 10
        
        # Test the simple method
        changed_keys = dd.update_all_simple()
        
        assert len(changed_keys) == 2
        assert "test1" in changed_keys
        assert "test2" in changed_keys

    def test_update_all_orphaned_keys_cleanup(self):
        """Test that orphaned keys are properly cleaned up"""
        dd = DiffDict()
        
        dd["keep"] = [1, 2, 3]
        dd["remove"] = {"will": "be deleted"}
        
        initial_tracked = len(dd._DiffDict__keysums)
        assert initial_tracked == 2
        
        # Delete from dataref
        del dd.dataref["remove"]
        
        # Update should detect and clean up orphaned key
        result = dd.update_all()
        
        assert "remove" in result["orphaned"]
        assert len(dd._DiffDict__keysums) == initial_tracked - 1
        assert "remove" not in dd._DiffDict__keysums

    def test_update_all_complete_dataref_replacement(self):
        """Test update_all after complete dataref replacement"""
        dd = DiffDict()
        
        dd["original"] = [1, 2, 3]
        
        # Replace entire dataref
        dd.dataref = {"new": [7, 8, 9]}
        
        # Should detect orphaned original and optionally track new
        result = dd.update_all(include_new_keys=True)
        
        assert "original" in result["orphaned"]
        assert "new" in result["new_tracked"]
        
        # Should now be tracking only the new key
        assert list(dd._DiffDict__keysums.keys()) == ["new"]

import pytest
import json
import os
import tempfile
import shutil
from src.zuu.syncdict import SyncDict


class TestSyncDict:
    """Test suite for the enhanced SyncDict with structural change synchronization"""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test files"""
        temp_dir = tempfile.mkdtemp(prefix="test_syncdict_")
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def sample_files(self, temp_dir):
        """Create sample JSON files with identical structure"""
        structure = {
            "x": {
                "y": "base_y",
                "z": {
                    "w": "base_w"
                }
            },
            "other": "value"
        }
        
        files = {}
        for name in ["base.json", "file1.json", "file2.json"]:
            file_path = os.path.join(temp_dir, name)
            test_data = json.loads(json.dumps(structure))  # Deep copy
            if name != "base.json":
                # Different values, same structure
                test_data["x"]["y"] = f"{name}_y"
                test_data["x"]["z"]["w"] = f"{name}_w"
                test_data["other"] = f"{name}_other"
            
            with open(file_path, 'w') as f:
                json.dump(test_data, f, indent=2)
            files[name] = file_path
        
        return files
    
    def test_syncdict_initialization(self, sample_files):
        """Test SyncDict initializes correctly with a base file"""
        sync_dict = SyncDict(sample_files["base.json"])
        
        # Should be able to access data
        assert sync_dict["x/y"] == "base_y"
        assert sync_dict["x/z/w"] == "base_w"
        assert "x/y" in sync_dict
        
    def test_add_watch_identical_structure(self, sample_files):
        """Test adding files with identical structure to watch list"""
        sync_dict = SyncDict(sample_files["base.json"])
        
        sync_dict.add_watch(sample_files["file1.json"])
        sync_dict.add_watch(sample_files["file2.json"])
        
        assert len(sync_dict.watched_files) == 2
        assert len(sync_dict.desynced_files) == 0
        
    def test_structural_change_propagation(self, sample_files):
        """Test that structural changes propagate to watched files"""
        sync_dict = SyncDict(sample_files["base.json"])
        sync_dict.add_watch(sample_files["file1.json"])
        sync_dict.add_watch(sample_files["file2.json"])
        
        # Make structural change: move w from nested to top level
        w_value = sync_dict["x/z/w"]
        del sync_dict["x/z/w"]
        sync_dict["w"] = w_value
        
        # Monitor changes and apply them
        sync_dict.monitor()
        sync_dict.applyChanges()
        
        # Changes should propagate to watched files
        # Check file1
        with open(sample_files["file1.json"], 'r') as f:
            file1_data = json.load(f)
        
        assert "w" in file1_data  # New top-level key
        assert "z" not in file1_data["x"]  # Entire z structure removed
        assert file1_data["w"] == "file1.json_w"  # Preserves original value
        
        # Check file2
        with open(sample_files["file2.json"], 'r') as f:
            file2_data = json.load(f)
        
        assert "w" in file2_data
        assert "z" not in file2_data["x"]  # Entire z structure removed
        assert file2_data["w"] == "file2.json_w"
        
    def test_adding_new_nested_structure(self, sample_files):
        """Test adding completely new nested structures"""
        sync_dict = SyncDict(sample_files["base.json"])
        sync_dict.add_watch(sample_files["file1.json"])
        
        # Add new nested structure
        sync_dict["config/database/host"] = "localhost"
        sync_dict["config/database/port"] = 5432
        sync_dict["config/app/name"] = "test_app"
        
        # Monitor changes and apply them
        sync_dict.monitor()
        sync_dict.applyChanges()
        
        # Check propagation
        with open(sample_files["file1.json"], 'r') as f:
            file1_data = json.load(f)
        
        assert "config" in file1_data
        assert file1_data["config"]["database"]["host"] == "localhost"
        assert file1_data["config"]["database"]["port"] == 5432
        assert file1_data["config"]["app"]["name"] == "test_app"
        
    def test_deletion_propagation(self, sample_files):
        """Test that deletions propagate to watched files"""
        sync_dict = SyncDict(sample_files["base.json"])
        sync_dict.add_watch(sample_files["file1.json"])
        
        # Delete nested structure
        del sync_dict["x/z"]
        
        # Monitor changes and apply them
        sync_dict.monitor()
        sync_dict.applyChanges()
        
        # Check propagation
        with open(sample_files["file1.json"], 'r') as f:
            file1_data = json.load(f)
        
        assert "z" not in file1_data["x"]
        # Other data should remain intact
        assert file1_data["x"]["y"] == "file1.json_y"
        assert file1_data["other"] == "file1.json_other"
        
    def test_change_history_tracking(self, sample_files):
        """Test that changes are properly tracked"""
        sync_dict = SyncDict(sample_files["base.json"])
        
        initial_changes = len(sync_dict.changes["all"])
        
        # Make several changes
        sync_dict["new_key"] = "new_value"
        sync_dict["x/y"] = "updated_value"
        del sync_dict["other"]
        
        changes = sync_dict.changes["all"]
        assert len(changes) == initial_changes + 3
        
        # Check last change
        last_change = sync_dict.changes["last"]
        assert last_change["key"] == "other"
        assert last_change["new"] is None  # Deletion
        
    def test_save_functionality(self, sample_files):
        """Test that save() writes changes to the base file"""
        sync_dict = SyncDict(sample_files["base.json"])
        
        sync_dict["test_key"] = "test_value"
        sync_dict.save()
        
        # Read base file directly
        with open(sample_files["base.json"], 'r') as f:
            base_data = json.load(f)
        
        assert base_data["test_key"] == "test_value"
        
    def test_desynced_files_handling(self, temp_dir, sample_files):
        """Test handling of files with different structures"""
        # Create a file with different structure
        different_structure = {
            "completely": {
                "different": "structure"
            }
        }
        
        different_file = os.path.join(temp_dir, "different.json")
        with open(different_file, 'w') as f:
            json.dump(different_structure, f)
        
        sync_dict = SyncDict(sample_files["base.json"])
        sync_dict.add_watch(different_file)
        
        assert len(sync_dict.desynced_files) == 1
        assert different_file in sync_dict.desynced_files
        assert len(sync_dict.watched_files) == 0

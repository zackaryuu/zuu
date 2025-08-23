import os
from zuu.dict_patterns import extract_nested_keys
from zuu.json_io import read_json, write_json
from zuu.diffdict import DiffDict
from zuu.simple_dict import deep_get, deep_set, deep_pop
import copy


class SyncDictMeta(type):
    _fileCache = {}
    _fileModifiedStamp = {}
    _maxSize = 256

    def _getCacheFile(self, path: str):
        recordedStamp = self._fileModifiedStamp.get(path)
        if (
            recordedStamp is not None
            and path in self._fileCache
            and os.path.getmtime(path) == recordedStamp
        ):
            return self._fileCache.get(path)

        raw = read_json(path)
        self._fileCache[path] = raw
        self._fileModifiedStamp[path] = os.path.getmtime(path)

        while len(self._fileCache) > self._maxSize:
            self._fileCache.popitem()

        return raw

class SyncDict(metaclass=SyncDictMeta):
    def __init__(self, path: str, separator: str = "/"):
        assert os.path.exists(path), f"Base path '{path}' does not exist"
        self.__path = os.path.abspath(path)
        self.__separator = separator
        self.__desynced_list = []
        self.__watch_list = []
        
        # Initialize DiffDict with the base file data
        base_data = self.__class__._getCacheFile(self.__path)
        self.__diffdict = DiffDict(data=copy.deepcopy(base_data), separator=separator)
        
        # Store baseline structure for change detection
        self.__baseline_keysums = self.__diffdict.update_keysums()

    def add_watch(self, path: str):
        assert os.path.exists(path), f"Path '{path}' does not exist"
        path = os.path.abspath(path)
        if path in self.__watch_list or path == self.__path:
            return
            
        watched_data = self.__class__._getCacheFile(path)
        watched_keys = set(extract_nested_keys(watched_data, self.__separator))
        
        # Compare with current base structure
        base_keys = set(extract_nested_keys(self.__diffdict.dataref, self.__separator))
        
        if base_keys != watched_keys:
            self.__desynced_list.append(path)
        else:
            self.__watch_list.append(path)

    def add_watchfolder(self, folder: str):
        assert os.path.exists(folder), f"Folder '{folder}' does not exist"
        assert os.path.isdir(folder), f"Path '{folder}' is not a folder"
        folder = os.path.abspath(folder)
        
        for root, dirs, files in os.walk(folder):
            for filename in files:
                file_path = os.path.join(root, filename)
                if file_path.endswith('.json'):  # Only process JSON files
                    try:
                        self.add_watch(file_path)
                    except (AssertionError, Exception):
                        # Skip files that can't be processed
                        pass

    # Dict-like interface - just operates on source data
    def __getitem__(self, key):
        return self.__diffdict[key]
        
    def __setitem__(self, key, value):
        self.__diffdict[key] = value
        
    def __delitem__(self, key):
        del self.__diffdict[key]
    
    def __contains__(self, key):
        return key in self.__diffdict

    def monitor(self):
        """Track structural changes and detect moves using checksums"""
        current_keysums = self.__diffdict.update_keysums()
        
        # Compare baseline vs current to detect structural changes
        baseline_keys = set(self.__baseline_keysums.keys())
        current_keys = set(current_keysums.keys())
        
        added_keys = current_keys - baseline_keys
        removed_keys = baseline_keys - current_keys
        
        # Detect moves by matching checksums: same checksum at different key = move
        self.__moves = {}  # removed_key -> added_key
        remaining_added = set(added_keys)
        remaining_removed = set(removed_keys)
        
        # Build reverse lookup: checksum -> key for current keysums
        current_checksum_to_key = {checksum: key for key, checksum in current_keysums.items()}
        
        for removed_key in removed_keys:
            removed_checksum = self.__baseline_keysums[removed_key]
            
            # Look for the same checksum in current keysums at a different location
            if removed_checksum in current_checksum_to_key:
                added_key = current_checksum_to_key[removed_checksum]
                
                # Verify this added_key is actually new (not just unchanged)
                if added_key in remaining_added:
                    # This is a move: same content, different location
                    self.__moves[removed_key] = added_key
                    remaining_added.discard(added_key)
                    remaining_removed.discard(removed_key)
        
        # What's left are true additions and removals
        self.__true_additions = remaining_added
        self.__true_removals = remaining_removed
        
        # Update baseline for next comparison
        self.__baseline_keysums = current_keysums
        
        return {
            'added': self.__true_additions,
            'removed': self.__true_removals,
            'moved': self.__moves
        }

    def applyChanges(self):
        """Apply structural changes while preserving existing translations"""
        if not hasattr(self, '_SyncDict__moves'):
            return  # No changes detected
            
        for watch_path in self.__watch_list[:]:  # Copy to avoid modification during iteration
            try:
                # Load current watched file data
                watched_data = self.__class__._getCacheFile(watch_path)
                original_data = copy.deepcopy(watched_data)
                
                # Apply moves first (preserve translated content during restructuring)
                for removed_key, added_key in self.__moves.items():
                    # Get the translated value from the old location
                    translated_value = deep_get(original_data, removed_key, self.__separator, default=None)
                    if translated_value is not None:
                        # Move the translated value to new location
                        deep_set(watched_data, added_key, translated_value, self.__separator)
                        # Remove from old location
                        deep_pop(watched_data, removed_key, self.__separator, default=None)
                
                # Apply true additions (new keys that didn't exist before)
                for added_key in self.__true_additions:
                    existing_value = deep_get(original_data, added_key, self.__separator, default=None)
                    
                    if existing_value is None:
                        # New key - use base value as placeholder
                        base_value = deep_get(self.__diffdict.dataref, added_key, self.__separator)
                        deep_set(watched_data, added_key, base_value, self.__separator)
                
                # Apply true removals (keys that were deleted, not moved)
                for removed_key in self.__true_removals:
                    deep_pop(watched_data, removed_key, self.__separator, default=None)
                
                # Clean up empty parent containers after removals
                self._cleanup_empty_containers(watched_data)
                
                # Write back to file
                write_json(watch_path, watched_data)
                
            except Exception:
                # Move to desynced if operation fails
                if watch_path in self.__watch_list:
                    self.__watch_list.remove(watch_path)
                if watch_path not in self.__desynced_list:
                    self.__desynced_list.append(watch_path)

    def _cleanup_empty_containers(self, data):
        """Remove empty containers after deletions"""
        def _cleanup_recursive(obj, path_parts):
            if not isinstance(obj, dict):
                return False
                
            keys_to_remove = []
            for key, value in obj.items():
                if isinstance(value, dict):
                    if not value:  # Empty dict
                        keys_to_remove.append(key)
                    elif _cleanup_recursive(value, path_parts + [key]):
                        keys_to_remove.append(key)
            
            for key in keys_to_remove:
                del obj[key]
            
            return len(obj) == 0
        
        _cleanup_recursive(data, [])

    def save(self):
        """Save changes to the base file"""
        write_json(self.__path, self.__diffdict.dataref)

    @property
    def changes(self):
        """Access to DiffDict change tracking"""
        return self.__diffdict.changes
        
    @property
    def watched_files(self):
        """List of successfully synchronized files"""
        return self.__watch_list.copy()
        
    @property 
    def desynced_files(self):
        """List of files that couldn't be synchronized"""
        return self.__desynced_list.copy()
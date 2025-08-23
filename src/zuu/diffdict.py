import datetime
from types import MappingProxyType
from typing import TypedDict
from zuu.simple_dict import deep_get, deep_set, deep_pop
from hashlib import sha1
import os

_doesNotExist = object()


class DiffSet(TypedDict):
    """
    Structure representing a single change record in DiffDict.

    Each change made to a DiffDict is recorded as a DiffSet containing
    information about what changed, when it changed, and the before/after values.

    Attributes:
        key (str): The key that was modified
        stamp (int | None): Timestamp of the change, or None if timestamps disabled
        previous (str | None): Hash/value before the change, or None for new keys
        new (str | None): Hash/value after the change, or None for deletions

    Note:
        For primitive types (str, int, float), the actual values are stored.
        For complex objects, SHA1 hashes of their string representations are stored.
    """

    key: str
    stamp: int | None
    previous: str | None
    new: str | None


class DiffDict:
    """
    A dictionary-like container that tracks all changes made to its data.

    DiffDict provides a full dictionary interface while maintaining a complete history
    of all modifications, including additions, updates, and deletions. It supports
    nested keys using configurable separators and can detect external modifications
    to stored mutable objects through the updateAtKey method.

    Features:
        - Full dict-like interface (__getitem__, __setitem__, __contains__, etc.)
        - Change tracking with timestamps and hash comparison
        - Support for nested keys with configurable separators
        - Callback system for change notifications
        - Change history pruning for memory management
        - External modification detection for mutable objects
        - Configurable hashing functions and timestamp options

    Args:
        data (dict, optional): Initial data to populate the dictionary. Defaults to empty dict.
        hashFunc (callable, optional): Hash function for change detection. Defaults to sha1.
        stamp (bool, optional): Whether to include timestamps in change records. Defaults to True.
        separator (str, optional): Separator for nested keys. Defaults to "/".

    Example:
        >>> dd = DiffDict()
        >>> dd["user/name"] = "Alice"
        >>> dd["user/age"] = 25
        >>> dd["user/name"] = "Bob"  # Update existing
        >>> len(dd.changes["all"])   # 3 changes recorded
        3
        >>> dd.changes["last"]["key"]
        'user/name'

        # External modification tracking
        >>> my_list = [1, 2, 3]
        >>> dd["data"] = my_list
        >>> my_list.append(4)  # Modify externally
        >>> dd.updateAtKey("data")  # Notify of change
    """

    @property
    def dataref(self):
        return self.__data
    
    @dataref.setter
    def dataref(self, value):
        assert isinstance(value, dict), "Data reference must be a dictionary"
        self.__data = value

    def __init__(
        self,
        data: dict = None,
        hashFunc: callable = sha1,
        stamp: bool = True,
        separator: str = "/",
    ):
        """
        Initialize a new DiffDict instance.

        Args:
            data (dict, optional): Initial data to populate the dictionary.
                If None, starts with an empty dictionary. Defaults to None.
            hashFunc (callable, optional): Hash function used for change detection.
                Must return an object with a hexdigest() method. Defaults to sha1.
            stamp (bool, optional): Whether to include timestamps in change records.
                If True, each change includes a timestamp. Defaults to True.
            separator (str, optional): String used to separate nested key components.
                For example, "/" allows keys like "user/profile/name". Defaults to "/".
        """
        if data is None:
            data = {}
        self.__data = data
        self.__changes: list[DiffSet] = []
        self.__keysums = {}
        self.__hashFunc = hashFunc
        self.__DoStamp = stamp
        self.__useHexCheck = False
        self.__separator = separator
        self.__callbacks = []

    def prune_changes(self, keep: int = 256):
        """
        Remove old change records to manage memory usage.

        Keeps only the most recent 'keep' number of changes and discards older ones.
        This is useful for long-running applications where the full change history
        is not needed and memory usage is a concern.

        Args:
            keep (int, optional): Number of recent changes to retain.
                If 0 or negative, removes all changes. Defaults to 256.

        Example:
            >>> dd = DiffDict()
            >>> for i in range(1000):
            ...     dd[f"key{i}"] = f"value{i}"
            >>> len(dd.changes["all"])  # 1000 changes
            1000
            >>> dd.prune_changes(100)
            >>> len(dd.changes["all"])  # Only last 100 kept
            100
        """
        if keep <= 0:
            self.__changes = []
        else:
            self.__changes = self.__changes[-keep:]

    def add_callback(self, callback: callable):
        """
        Add a callback function that is called whenever a change is recorded.

        The callback function will be invoked after each change is recorded in the
        change history. Multiple callbacks can be added and will be called in the
        order they were added.

        Args:
            callback (callable): Function to call on each change. The function should
                accept one argument: the DiffDict instance. It will be called after
                each change is recorded, allowing inspection of the current state
                and change history.

        Example:
            >>> def on_change(diff_dict):
            ...     print(f"Change detected: {diff_dict.changes['last']['key']}")
            >>> dd = DiffDict()
            >>> dd.add_callback(on_change)
            >>> dd["test"] = "value"  # Prints: "Change detected: test"
        """
        self.__callbacks.append(callback)

    @property
    def changes(self):
        """
        Get a read-only view of the change history.

        Returns a MappingProxyType containing the complete change history and
        quick access to the most recent change. The returned object is immutable
        to prevent accidental modification of the change history.

        Returns:
            MappingProxyType: Dictionary-like object with keys:
                - "all": List of all change records (DiffSet objects)
                - "last": Most recent change record, or None if no changes

        Note:
            The returned object is a snapshot. If more changes are made after
            getting this property, you need to access the property again to
            see the new changes.

        Example:
            >>> dd = DiffDict()
            >>> dd["key"] = "value"
            >>> changes = dd.changes
            >>> len(changes["all"])  # 1
            >>> changes["last"]["key"]  # "key"
            >>> changes["last"]["new"]  # "value"
        """
        return MappingProxyType(
            {
                "all": self.__changes,
                "last": self.__changes[-1] if self.__changes else None,
            }
        )

    @property
    def useHexCheck(self):
        """
        Get the current hex check setting.

        Returns:
            bool: True if hex checking is enabled, False otherwise.
        """
        return self.__useHexCheck

    @useHexCheck.setter
    def useHexCheck(self, value):
        """
        Set whether to use hex checking for change detection.

        When enabled, forces hash-based comparison even for primitive types
        that would normally use direct value comparison.

        Args:
            value (bool): True to enable hex checking, False to disable.
        """
        self.__useHexCheck = value

    def __compare(self, key, val1, val2, hash1=_doesNotExist, hash2=_doesNotExist, callback : bool = True):
        """
        Internal method to compare two values and record changes.

        This method handles the core logic of change detection by comparing
        hash values of old and new values. It updates internal state and
        records changes when differences are detected.

        Args:
            key (str): The key being modified
            val1: Previous value (or _doesNotExist for new keys)
            val2: New value (or _doesNotExist for deletions)
            hash1: Pre-computed hash of val1 (optional)
            hash2: Pre-computed hash of val2 (optional)

        Returns:
            bool: True if a change was recorded, False if values are identical
        """
        if key in self.__keysums:
            hash1 = self.__keysums[key]

        if val1 is not _doesNotExist and hash1 is _doesNotExist:
            if isinstance(val1, (str, int, float)):
                hash1 = str(val1)
            else:
                hash1 = self.__hashFunc(str(val1).encode()).hexdigest()

        if val2 is not _doesNotExist and hash2 is _doesNotExist:
            if isinstance(val2, (str, int, float)):
                hash2 = str(val2)
            else:
                hash2 = self.__hashFunc(str(val2).encode()).hexdigest()

        if hash1 is not _doesNotExist and hash2 is not _doesNotExist:
            if hash1 == hash2:
                return False

        # Update keysums before recording the change
        if hash1 is not _doesNotExist and val2 is _doesNotExist:
            # deletion
            self.__keysums.pop(key, None)
        elif hash2 is not _doesNotExist:
            self.__keysums[key] = hash2

        self.__changes.append(
            DiffSet(
                key=key,
                stamp=datetime.datetime.now().timestamp() if self.__DoStamp else None,
                previous=hash1 if hash1 is not _doesNotExist else None,
                new=hash2 if hash2 is not _doesNotExist else None,
            )
        )
        if callback and len(self.__callbacks) > 0:
            for callback in self.__callbacks:
                callback(self)

        return True

    def updateAtKey(self, key: str):
        """
        Notify the DiffDict that an object at the given key has been modified externally.
        This will trigger a hash comparison and record a change if the object has indeed changed.

        Args:
            key: The key where the object was modified

        Raises:
            KeyError: If the key doesn't exist in the dictionary
        """
        current_value = deep_get(self.__data, key, self.__separator, _doesNotExist)
        if current_value is _doesNotExist:
            raise KeyError(f"Key '{key}' not found")

        # Get the stored hash and force a comparison with the current value
        # This will detect if the object has been modified externally
        old_hash = self.__keysums.get(key, _doesNotExist)
        self.__compare(key, current_value, current_value, hash1=old_hash)

    def update_all(self, include_new_keys: bool = False):
        """
        Check all existing keys for external modifications and record any changes found.
        
        This method iterates through all keys that have been previously stored in the
        DiffDict and checks if their values have been modified externally (e.g., if
        a stored list was mutated, or a nested dict was changed). Any detected changes
        are recorded in the change history.
        
        Args:
            include_new_keys (bool, optional): If True, also check keys that exist in
                the data but aren't being tracked (e.g., keys added via dataref.update()).
                These keys will be added to tracking if they're found. Defaults to False.
        
        Returns:
            dict: Dictionary with keys:
                - "changed": List of tracked keys that were found to have changed externally
                - "new_tracked": List of previously untracked keys that are now being tracked
                    (only populated when include_new_keys=True)
                - "orphaned": List of tracked keys that no longer exist in the data
        
        Example:
            >>> dd = DiffDict()
            >>> my_list = [1, 2, 3]
            >>> dd["data"] = my_list
            >>> dd["other"] = {"count": 0}
            >>> 
            >>> # External modifications
            >>> my_list.append(4)
            >>> dd["other"]["count"] = 5
            >>> 
            >>> result = dd.update_all()  # Detects both changes
            >>> len(result["changed"])  # 2
            >>> "data" in result["changed"]  # True
            >>> "other" in result["changed"]  # True
            
            # With dataref manipulation
            >>> dd.dataref.update({"new_key": [7, 8, 9]})
            >>> result = dd.update_all(include_new_keys=True)
            >>> "new_key" in result["new_tracked"]  # True
        """
        result = {
            "changed": [],
            "new_tracked": [],
            "orphaned": []
        }
        
        # Get a copy of the keys to avoid mutation during iteration
        tracked_keys = list(self.__keysums.keys())
        
        # Check existing tracked keys
        for key in tracked_keys:
            try:
                # updateAtKey will only record a change if the hash differs
                changes_before_key = len(self.__changes)
                self.updateAtKey(key)
                
                # Check if a change was actually recorded
                if len(self.__changes) > changes_before_key:
                    result["changed"].append(key)
                    
            except KeyError:
                # Key was deleted externally, mark as orphaned
                result["orphaned"].append(key)
                # Remove from tracking since it no longer exists
                self.__keysums.pop(key, None)
        
        # Optionally check for new keys in the data that aren't being tracked
        if include_new_keys:
            data_keys = set(self.__data.keys()) if hasattr(self.__data, 'keys') else set()
            tracked_keys_set = set(self.__keysums.keys())
            new_keys = data_keys - tracked_keys_set
            
            for key in new_keys:
                try:
                    # Start tracking this key by treating it as a "new" assignment
                    value = self.__data[key]
                    self.__compare(key, _doesNotExist, value)
                    result["new_tracked"].append(key)
                except (KeyError, TypeError):
                    # Skip if we can't access the key or data structure is incompatible
                    continue
        
        return result

    def update_all_simple(self):
        """
        Simplified version of update_all() that returns only changed keys (backward compatibility).
        
        Returns:
            list[str]: List of keys that were found to have changed externally.
        
        Example:
            >>> dd = DiffDict()
            >>> dd["data"] = [1, 2, 3]
            >>> dd["data"].append(4)  # External change
            >>> changed_keys = dd.update_all_simple()
            >>> "data" in changed_keys  # True
        """
        result = self.update_all()
        return result["changed"]

    def __setitem__(self, key, value):
        """
        Set a value for the given key, recording the change.

        Implements the dictionary interface for assignment operations (dd[key] = value).
        Supports nested keys using the configured separator. Records a change
        unless the new value is identical to the existing value.

        Args:
            key (str): Key to set. Can be nested using the separator (e.g., "user/name").
            value: Value to store. Can be any type.

        Example:
            >>> dd = DiffDict()
            >>> dd["simple"] = "value"
            >>> dd["nested/key"] = {"data": [1, 2, 3]}
        """
        # get the previous value
        previousVal = self.__data.get(key, _doesNotExist)
        if not self.__useHexCheck and previousVal == value:
            return

        # Check if the value is the same
        if self.__compare(key, previousVal, value):
            deep_set(self.__data, key, value, self.__separator)

    def pop(self, key, default=_doesNotExist):
        """
        Remove and return the value for the given key, recording the change.

        Similar to dict.pop(), removes the key from the dictionary and returns
        its value. The removal is recorded as a change in the history.

        Args:
            key (str): Key to remove. Can be nested using the separator.
            default: Value to return if key is not found. If not provided
                and key is missing, raises KeyError.

        Returns:
            The value that was stored at the key.

        Raises:
            KeyError: If key is not found and no default is provided.

        Example:
            >>> dd = DiffDict()
            >>> dd["temp"] = "temporary"
            >>> value = dd.pop("temp")  # Returns "temporary"
            >>> "temp" in dd  # False
        """
        previousVal = deep_get(self.__data, key, self.__separator, _doesNotExist)
        if previousVal is _doesNotExist:
            if default is _doesNotExist:
                raise KeyError(f"Key '{key}' not found")
            return default
        self.__compare(key, previousVal, _doesNotExist)
        deep_pop(self.__data, key, self.__separator)
        return previousVal

    def __getitem__(self, key):
        """
        Get the value for the given key.

        Implements the dictionary interface for access operations (dd[key]).
        Supports nested keys using the configured separator.

        Args:
            key (str): Key to retrieve. Can be nested using the separator.

        Returns:
            The value stored at the key.

        Raises:
            KeyError: If the key is not found.

        Example:
            >>> dd = DiffDict()
            >>> dd["user/profile/name"] = "Alice"
            >>> name = dd["user/profile/name"]  # "Alice"
        """
        res = deep_get(self.__data, key, self.__separator, _doesNotExist)
        if res is _doesNotExist:
            raise KeyError(f"Key '{key}' not found")
        return res

    def __contains__(self, key):
        """
        Check if a key exists in the dictionary.

        Implements the dictionary interface for membership testing (key in dd).
        Supports nested keys and partial paths.

        Args:
            key (str): Key to check. Can be nested using the separator.

        Returns:
            bool: True if the key exists, False otherwise.

        Example:
            >>> dd = DiffDict()
            >>> dd["user/profile/name"] = "Alice"
            >>> "user/profile/name" in dd  # True
            >>> "user/profile" in dd       # True (partial path)
            >>> "user/email" in dd         # False
        """
        return (
            deep_get(self.__data, key, self.__separator, _doesNotExist)
            is not _doesNotExist
        )

    def __delitem__(self, key):
        """
        Delete a key from the dictionary, recording the change.

        Implements the dictionary interface for deletion operations (del dd[key]).
        This is equivalent to calling pop(key) but doesn't return the value.

        Args:
            key (str): Key to delete. Can be nested using the separator.

        Raises:
            KeyError: If the key is not found.

        Example:
            >>> dd = DiffDict()
            >>> dd["temporary"] = "value"
            >>> del dd["temporary"]  # Records deletion change
        """
        self.pop(key)

    def __len__(self):
        """
        Get the number of top-level keys in the dictionary.

        Returns:
            int: Number of keys at the top level of the dictionary structure.

        Note:
            This returns the count of top-level keys only. Nested keys created
            through the separator syntax are not counted separately.

        Example:
            >>> dd = DiffDict()
            >>> dd["key1"] = "value1"
            >>> dd["nested/key2"] = "value2"  # Creates top-level "nested" key
            >>> len(dd)  # 2 (key1 and nested)
            2
        """
        return len(self.__data)

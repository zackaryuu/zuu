
import os


def is_obsidian_vault(path : str):
    try:
        assert os.path.exists(path)
        assert os.path.isdir(path)
        assert os.path.exists(os.path.join(path, '.obsidian'))
        assert os.path.isdir(os.path.join(path, '.obsidian'))
        return True
    except AssertionError:
        return False
    


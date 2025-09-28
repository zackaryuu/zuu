"""Steam process management utilities.

This module provides functions to check, manage, and interact with Steam processes
on the system using the psutil library.
"""

import psutil

def steam_is_running() -> bool:
    """Check if Steam is currently running.
    
    Iterates through all running processes to determine if steam.exe is active.
    
    Returns:
        bool: True if Steam is running, False otherwise.
    """
    for process in psutil.process_iter(['name']):
        if process.info['name'] == 'steam.exe':
            return True
    return False 

def steam_process() -> psutil.Process | None:
    """Get the Steam process object if it's running.
    
    Searches through all running processes to find the steam.exe process.
    
    Returns:
        psutil.Process | None: The Steam process object if found, None otherwise.
    """
    for process in psutil.process_iter(['name']):
        if process.info['name'] == 'steam.exe':
            return process
    return None

def kill_steam() -> None:
    """Terminate the Steam process if it's running.
    
    Finds the Steam process and gracefully terminates it, then waits for
    the process to fully exit.
    
    Note:
        This function will wait indefinitely for the process to terminate.
        If Steam doesn't respond to the terminate signal, this may hang.
    """
    process = steam_process()
    if process:
        process.terminate()
        process.wait()

def get_steam_path() -> str | None:
    """Get the executable path of the running Steam process.
    
    Retrieves the full path to the Steam executable if Steam is currently running.
    
    Returns:
        str | None: The full path to steam.exe if Steam is running, None otherwise.
        
    Raises:
        psutil.AccessDenied: If the current user doesn't have permission to access
            the process information.
        psutil.NoSuchProcess: If the process terminates between finding it and
            getting its executable path.
    """
    process = steam_process()
    if process:
        return process.exe()
    return None


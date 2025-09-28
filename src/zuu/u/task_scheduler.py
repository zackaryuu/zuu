import win32com.client
import pythoncom

def create_everyday_task(task_name, command, start_time, repetition_interval=None, repetition_duration=None):
    """
    Create a Windows scheduled task that runs every day at the specified time.
    Args:
        task_name (str): Name of the task.
        command (str): Command to run.
        start_time (str): Time in HH:MM format (24h).
        repetition_interval (str, optional): ISO 8601 duration string for repetition interval (e.g., "PT1H" for 1 hour).
        repetition_duration (str, optional): ISO 8601 duration string for how long to repeat the task (e.g., "PT8H" for 8 hours).
    """
    pythoncom.CoInitialize()
    scheduler = win32com.client.Dispatch('Schedule.Service')
    scheduler.Connect()
    rootFolder = scheduler.GetFolder("\\")
    taskDef = scheduler.NewTask(0)
    taskDef.RegistrationInfo.Description = f"Run {command} every day at {start_time}"
    taskDef.Principal.LogonType = 3  # Interactive
    trigger = taskDef.Triggers.Create(1)  # Daily trigger
    # Ensure start_time is HH:MM and StartBoundary is valid ISO format
    trigger.StartBoundary = f"2025-01-01T{start_time}:00"
    # Set DaysInterval if available (COM interface may differ)
    try:
        trigger.DaysInterval = 1
    except AttributeError:
        print("DaysInterval not supported, using default daily trigger.")
    # Set repetition if requested
    if repetition_interval:
        trigger.Repetition.Interval = repetition_interval
    if repetition_duration:
        trigger.Repetition.Duration = repetition_duration
    action = taskDef.Actions.Create(0)
    action.Path = command
    rootFolder.RegisterTaskDefinition(task_name, taskDef, 6, None, None, 3)

def create_onlogin_task(task_name, command, description="Run {command} on user logon"):
    """
    Create a Windows scheduled task that runs on user logon.
    Args:
        task_name (str): Name of the task.
        command (str): Command to run.
    """
    pythoncom.CoInitialize()
    scheduler = win32com.client.Dispatch('Schedule.Service')
    scheduler.Connect()
    rootFolder = scheduler.GetFolder("\\")
    taskDef = scheduler.NewTask(0)
    taskDef.RegistrationInfo.Description = description if description else f"Run {command} on user logon"
    taskDef.Principal.LogonType = 3
    taskDef.Triggers.Create(9)  # Logon
    action = taskDef.Actions.Create(0)
    action.Path = command
    rootFolder.RegisterTaskDefinition(task_name, taskDef, 6, None, None, 3)

def get_current_tasks():
    """
    Get a list of all current scheduled tasks (names).
    Returns:
        list[str]: List of task names.
    """
    pythoncom.CoInitialize()
    scheduler = win32com.client.Dispatch('Schedule.Service')
    scheduler.Connect()
    rootFolder = scheduler.GetFolder("\\")
    tasks = rootFolder.GetTasks(0)
    return [t for t in tasks]

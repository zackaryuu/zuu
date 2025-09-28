import datetime
import logging
import re
from typing import TypedDict
import psutil
import sched

scheduler = sched.scheduler()

class ProcessCtx(TypedDict):
    process: psutil.Process | str
    pid : int | None
    lifetime: int

def new_ctx(process: psutil.Process | str, lifetime: int,  pid: int | None = None) -> ProcessCtx:
    """
    Create a new process context.

    Args:
        process (psutil.Process | str): The process to watch.
        pid (int | None): The process ID.
        lifetime (int): The lifetime of the process.

    Returns:
        ProcessCtx: The new process context.
    """
    return ProcessCtx(process=process, pid=pid, lifetime=lifetime)

def match_process(ctx : ProcessCtx) -> psutil.Process | None:
    """
    Match a process based on the context provided.
    
    Args:
        ctx (ProcessCtx): Context containing process information.
        
    Returns:
        psutil.Process | None: The matched process or None if not found.
    """
    if isinstance(ctx['process'], psutil.Process):
        return ctx['process']
    elif isinstance(ctx['process'], str):
        for proc in psutil.process_iter(['pid', 'name']):
            if re.match(ctx['process'], proc.info['name'].lower()):
                return proc
            if ctx['pid'] is not None and proc.info['pid'] == ctx['pid']:
                return proc
    return None

def get_process_name(ctx : ProcessCtx) -> str:
    """
    Get the name of the process from the context.
    
    Args:
        ctx (ProcessCtx): Context containing process information.
        
    Returns:
        str: The name of the process.
    """
    if isinstance(ctx['process'], psutil.Process):
        return ctx['process'].name()
    elif isinstance(ctx['process'], str):
        return ctx['process']
    
    if ctx['pid'] is not None:
        return f"Process({ctx['pid']})"

    return "Unknown Process"


def process_watchdog(
    ctx: ProcessCtx,
    interval: int = 5,
    on_match: callable = None,
    on_timeout: callable = None
) -> None:
    """
    Watchdog for a process, checking if it matches the context.
    
    Args:
        ctx (ProcessCtx): Context containing process information.
        interval (int): Time in seconds between checks.
        on_match (callable): Function to call when a match is found.
        on_timeout (callable): Function to call when the process is not found within lifetime.
        
    Returns:
        None
    """
    
    def check_process(ctx, time_to_kill: datetime.datetime):
        logging.debug(f"[PWatchdog] heartbeat {get_process_name(ctx)}, to be killed at {time_to_kill}")
        proc = match_process(ctx)
        if not proc:
            return
        scheduler.enter(ctx["interval"], 1, check_process, (ctx, time_to_kill))
        if on_match:
            on_match(proc, ctx)
        if on_timeout and datetime.datetime.now() > time_to_kill:
            on_timeout(proc, ctx)

    ctx["interval"] = interval
    time_to_kill = datetime.datetime.now() + datetime.timedelta(seconds=ctx['lifetime'])
    scheduler.enter(ctx["interval"], 1, check_process, (ctx, time_to_kill))
    scheduler.run(blocking=False)


def process_watchdog_block():
    scheduler.run(blocking=True)
        
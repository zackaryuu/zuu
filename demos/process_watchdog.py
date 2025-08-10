
import logging
import sys
import psutil
from zuu.process_watchdog import new_ctx, process_watchdog, process_watchdog_block

def on_match(proc : psutil.Process, ctx):
    print(f"Matched process: {proc.name()}")

def on_timeout(proc : psutil.Process, ctx):
    proc.kill()

logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)

process_watchdog(
    ctx=new_ctx("notepad*", lifetime=10), 
    on_match=on_match, 
    on_timeout=on_timeout,
    interval=2
)

process_watchdog_block()
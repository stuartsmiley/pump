import asyncio
import datetime
import functools
import os
import signal
import re

WAIT_INCREMENT = 10
RUN_INCREMENT = 1
DATA_FILE = '/home/pi/dev/workfile'

def last_line():
    last = None
    with open(DATA_FILE) as f:
        for last in (line for line in f if line.rstrip('\n')):
            pass
    return last

def time_to_next(last_log_messsage):
    p =  re.compile('o.* (20.*)')
    m = p.match(last)
    last_run = m.group(1)
    print('Last run at ' + last_run)
    last_run_date = datetime.datetime.strptime(last_run, "%Y-%m-%d %H:%M:%S.%f")
    now = datetime.datetime.now()
    current_delta = now - last_run_date
    next_run = 0
    max_delta = datetime.timedelta(seconds=WAIT_INCREMENT)
    if current_delta < max_delta:
        next_run = current_delta.total_seconds()        
    return next_run


def ask_exit(signame):
    f = open(DATA_FILE, 'a')
    f.write('off and shutdown ' + str(datetime.datetime.now()) + '\n')
    f.close()
    print("got signal %s: exit" % signame)
    loop.stop()


def execute(status, loop):
    f = open(DATA_FILE, 'a')
    ssr = 'off'
    increment = WAIT_INCREMENT
    if status:
        status = False
    else:
        ssr = 'on'
        increment = RUN_INCREMENT
        status = True
    f.write(ssr + ' ' + str(datetime.datetime.now()) + '\n')
    f.close()
    loop.call_later(increment, execute, status, loop)

loop = asyncio.get_event_loop()
for signame in ('SIGINT', 'SIGTERM'):
    loop.add_signal_handler(getattr(signal, signame),
                            functools.partial(ask_exit, signame))
last = last_line();
next = time_to_next(last)
print("Next run starting in seconds: " + str(next))
print("Event loop running forever, press Ctrl+C to interrupt.")
print("pid %s: send SIGINT or SIGTERM to exit." % os.getpid())
loop.call_later(next, execute, False, loop) 

try:
    loop.run_forever()
finally:
    loop.close()

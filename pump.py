import asyncio
import configparser
import datetime
import functools
import os
import signal
import re
import time
import logging

CFG_NAME = '/home/pi/dev/pump/pump.cfg'
CFG_INCREMENT = 60 * 5
CONFIG_STAMP = os.stat(CFG_NAME).st_mtime
WAIT_INCREMENT = 0
RUN_INCREMENT = 0
DATA_FILE = os.path.join("/", "home", "pi", "whatever")
INITIAL_SLEEP_TIME = 0
LAST_RUN_DATETIME = datetime.datetime.now()

def initialize():
    config = configparser.ConfigParser()
    config.read(CFG_NAME)
    global WAIT_INCREMENT
    global RUN_INCREMENT
    global INITIAL_SLEEP_TIME
    global DATA_FILE
    WAIT_INCREMENT = int(config['DEFAULT']['RestTime'])
    RUN_INCREMENT = int(config['DEFAULT']['RunTime'])
    INITIAL_SLEEP_TIME = int(config['DEFAULT']['InitialRestTime'])
    DATA_FILE = config['DEFAULT']['DataFile']

def check_data_file():
    global LAST_RUN_DATETIME
    if os.path.isfile(DATA_FILE):
        logger.info("Found expected data file")
        last = last_line()
        LAST_RUN_DATETIME = last_run(last)
    else:
        logger.info("Did NOT Find expected data file " + DATA_FILE)
        logger.info("Seeding " + DATA_FILE)
        seconds_in_day = 60 * 60 * 24
        seed_delta = datetime.timedelta(seconds=seconds_in_day)
        LAST_RUN_DATETIME = datetime.datetime.now() - seed_delta
        update_data_file('off ' + str(LAST_RUN_DATETIME) + '\n')

def last_line():
    last = None
    with open(DATA_FILE) as f:
        for last in (line for line in f if line.rstrip('\n')):
            pass
    return last

def roll():
    last_run_date = LAST_RUN_DATETIME.date()
    today = datetime.date.today()
    logger.debug("Comparing " + str(last_run_date) + " vs " + str(today))
    if last_run_date != today:
        os.rename(DATA_FILE, DATA_FILE + "." + str(last_run_date)) 
        logger.info("rolled " + DATA_FILE)

def last_run(last_log_message):
    p =  re.compile('o.* (20.*)')
    m = p.match(last_log_message)
    last_run = m.group(1)
    logger.debug('Last run at ' + last_run)
    last_run_date = datetime.datetime.strptime(last_run, "%Y-%m-%d %H:%M:%S.%f")
    return last_run_date

def time_to_next(last_log_message):
    logger.debug('Last message: ' + last_log_message)
    last_run_date = last_run(last_log_message)
    now = datetime.datetime.now()
    current_delta = now - last_run_date
    next_run = 0
    max_delta = datetime.timedelta(seconds=WAIT_INCREMENT)
    if current_delta < max_delta:
        next_run = current_delta.total_seconds()        
    return next_run

def ask_exit(signame):
    update_data_file('off and shutdown ' + str(datetime.datetime.now()) + '\n')
    logger.info("got signal %s: exit" % signame)
    loop.stop()
    cfg_loop.stop()


def execute(status, loop):
    roll()
    global LAST_RUN_DATETIME
    ssr = 'off'
    increment = WAIT_INCREMENT
    if status:
        # turn pump off
        status = False
    else:
        # turn pump on
        ssr = 'on'
        increment = RUN_INCREMENT
        status = True
    now = datetime.datetime.now()
    update_data_file(ssr + ' ' + str(now) + '\n')
    LAST_RUN_DATETIME = now
    loop.call_later(increment, execute, status, loop)

def update_data_file(line):
    with open(DATA_FILE, 'a') as f:
        f.write(line)

def check_configuration(loop):
    global CONFIG_STAMP
    current_stamp = os.stat(CFG_NAME).st_mtime
    if CONFIG_STAMP != current_stamp:
        logger.info("Configuration changed: re-initializing")
        initialize()
        CONFIG_STAMP = current_stamp
    loop.call_later(CFG_INCREMENT, check_configuration, loop)

initialize()
if RUN_INCREMENT == 0:
    raise SystemExit
# Next thing is sleep for a bit since the pi boots up faster
# than the router and we want the pi to set its clock time
# with ntp correctly when the power comes back on before we
# start doing time comparisons.
time.sleep(INITIAL_SLEEP_TIME)

loop = asyncio.get_event_loop()
cfg_loop = asyncio.get_event_loop()
for signame in ('SIGINT', 'SIGTERM'):
    loop.add_signal_handler(getattr(signal, signame),
                            functools.partial(ask_exit, signame))
    cfg_loop.add_signal_handler(getattr(signal, signame),
                            functools.partial(ask_exit, signame))

logger = logging.getLogger('pump_application')
logger.setLevel(logging.DEBUG)
fh = logging.FileHandler('/home/pi/pump.log')
formatter = logging.Formatter('%(asctime)s - %(threadName)s %(levelname)s : %(message)s')
fh.setFormatter(formatter)
logger.addHandler(fh)

check_data_file()
last = last_line()
logger.debug(last)
next = time_to_next(last)
logger.debug("Next run starting in seconds: " + str(next))
logger.debug("Event loop running forever, press Ctrl+C to interrupt.")
logger.debug("pid %s: send SIGINT or SIGTERM to exit." % os.getpid())
loop.call_later(next, execute, False, loop) 
cfg_loop.call_later(CFG_INCREMENT, check_configuration, cfg_loop)
try:
    loop.run_forever()
    cfg_loop.run_forever()
finally:
    loop.close()
    cfg_loop.close()

import codecs
import datetime
import json
import logging
import os

from Core.sqlops import Base, engine


def js_r(filename):
    with open(filename, encoding='utf-8') as fh:
        return json.load(fh)


def js_w(filename, data):
    with codecs.open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4, default=str)


class Consolelogging(object):
    """
    Creates Loggers to log the code and redirect it to log file and std.out
    """

    def __init__(self):
        if not os.path.exists("data/logs/console"):
            os.makedirs("data/logs/console")
        initializedtime = datetime.datetime.now()
        tim_e = "[" + str(initializedtime)[0:16].replace(":",
                                                         "-").replace(" ", "][") + "]"
        # set up logging to file
        logging.basicConfig(level=logging.INFO,
                            format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                            datefmt='%m-%d %H:%M',
                            filename='data/logs/console/' + tim_e + '.log',
                            filemode='w')
        # define a Handler which writes INFO messages or higher to the
        # sys.stderr
        console = logging.StreamHandler()
        console.setLevel(logging.DEBUG)
        # set a format which is simpler for console use
        formatter = logging.Formatter(
            '%(asctime)s %(name)-20s %(levelname)-8s %(message)s')
        # tell the handler to use this format
        console.setFormatter(formatter)
        # add the handler to the root logger
        logging.getLogger('').addHandler(console)
        # Now, we can log to the root logger, or any other logger. First the
        # root...


datalog = Consolelogging()
logging.info("Running pre-boot checks...")
logging.info("Checking Imports...")


def filecheck(path=None):
    if path is not None:
        if not os.path.exists(path):
            open(path, "w+").close()
    # Core File Check
    filechecklist = ["data/logs/", "modules", "settings.json"]
    for files in filechecklist:
        if "." in files:
            if not os.path.exists(files):
                open(files, "w+").close()
        else:
            if not os.path.exists(files):
                os.makedirs(files)
    if not os.path.exists('data/data.db'):
        Base.metadata.create_all(engine)


# Runtime File Checks
logFile = ""
logging.info("Checking File systems...")
try:
    filecheck()
    logging.info('File systems check Complete')
    logging.info("BOOTING.......")
except Exception as e:
    logging.error(e)
    logging.error("File System Check failed .. proceed with cation")


def checksettings(self):
    try:
        self.Settings = js_r("settings.json")
    except json.decoder.JSONDecodeError:
        logging.error("Default settings empty or corrupted!...Overwriting..")
        defaultsettings = {
            "owner": 138684247853498369, "default_storage": True}
        js_w("settings.json", defaultsettings)
        self.Settings = js_r("settings.json")

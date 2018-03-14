import logging
import sys
import os
from os import path, environ
import ConfigParser

logging.basicConfig(level=logging.DEBUG)

cache = False

bm_integration = True

bm_refresh_interval = 10

threads_per_page = 15.0

theme = "Classic"


def getConfigFolder():
    appfolder = "PyBitmessage"
    dataFolder = None
    if "BITMESSAGE_HOME" in environ:
        dataFolder = environ["BITMESSAGE_HOME"]
        if dataFolder[-1] not in [os.path.sep, os.path.altsep]:
            dataFolder += os.path.sep
    elif sys.platform == 'darwin':
        if "HOME" in environ:
            dataFolder = path.join(os.environ["HOME"], "Library/Application Support/", appfolder) + '/'
    elif 'win32' in sys.platform or 'win64' in sys.platform:
        dataFolder = path.join(environ['APPDATA'].decode(sys.getfilesystemencoding(), 'ignore'), appfolder) + path.sep
    else:
        try:
            dataFolder = path.join(environ["XDG_CONFIG_HOME"], appfolder)
        except KeyError:
            dataFolder = path.join(environ["HOME"], ".config", appfolder)
        dataFolder += '/'
    return dataFolder


cp = ConfigParser.SafeConfigParser()
cp.read(getConfigFolder() + 'keys.dat')

settings_section = 'bitmessagesettings'


def getBMConfig(setting_key):
    value = None
    try:
        value = cp.get(settings_section, setting_key)
    except Exception as e:
        pass
    return value

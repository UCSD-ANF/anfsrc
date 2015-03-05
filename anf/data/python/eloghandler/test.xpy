import logging
import anf.eloghandler

logging.basicConfig()
rootlogger=logging.getLogger()
handler = anf.eloghandler.ElogHandler()
rootlogger.handlers=[]
rootlogger.addHandler(handler)

rootlogger.debug("debug message 1 should not print")
rootlogger.info("info message 1 should not print")
rootlogger.warning("warning message 1 should print")
rootlogger.error("error message 1 should print")
rootlogger.critical("critical message 1 should print")

rootlogger.setLevel(logging.DEBUG)

rootlogger.debug("debug message 2 should print")
rootlogger.info("info message 2 should print")
rootlogger.warning("warning message 2 should print")
rootlogger.error("error message 2 should print")
rootlogger.critical("critical message 2 should print")

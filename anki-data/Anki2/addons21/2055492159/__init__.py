from aqt import mw
from . import web
from . import util

def start_server():
    web_server = web.WebServer(util.handle_request)
    web_server.start()

mw.addonManager.addonLoadedHook = lambda *args: start_server()

# Web module for Raspberry Pi Pico W Drag Race Controller
# This file makes the directory a package

from web.server import start_server as start_web_server

__all__ = ['start_web_server']

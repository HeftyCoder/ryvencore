"""Gathers all the built-in Addons in a list"""
from .logging import LoggingAddon
from .variables import VarsAddon
 

built_in_addons = (LoggingAddon, VarsAddon)
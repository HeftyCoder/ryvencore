from .info_msgs import InfoMsgs
from .rc import *
from .session import Session
from .flow import Flow
from .data.base import Data
from .addons.base import AddOn
from .node import Node
from .port import PortConfig
from .utils import serialize, deserialize

def set_complete_data_func(func):
    from .base import Base
    Base.complete_data_function = func

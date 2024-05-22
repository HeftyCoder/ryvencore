from abc import ABC, abstractmethod
from .base import Event, NoArgsEvent
from enum import Enum, auto
from dataclasses import dataclass
from enum import IntEnum
from typing import Callable

from .node import (
    Node,
    FrameNode,
)

from .flow import Flow
import time
import traceback

class GraphActionResponse(IntEnum):
    """
    An enum indicating a response to an action for a graph requested on the Session
    """
    
    NO_GRAPH = auto()
    """No graph found to play"""
    NOT_ALLOWED = auto()
    """The action requested (play, pause, stop) is being invoked already"""
    SUCCESS = auto()
    """The action was succesful"""
    
    
class GraphState(Enum):
    """Enum that represents a graph player's state."""
    
    PLAYING = auto()
    PAUSED = auto()
    STOPPED = auto()

class GraphStateEvent:
    """Represents a change event"""
    
    def __init__(self, old_state: GraphState, new_state: GraphState):
        self.old_state = old_state
        self.new_state = new_state
    
    def __str__(self):
        return f"Old State: {self.old_state}, New State: {self.new_state}"
        
class GraphEvents:
    """All the events that a player may have. Hides invocation"""
        
    def __init__(self):
        self.reset()
            
    def sub_state_changed(self, func: Callable[[GraphStateEvent], None], 
                          nice=0, one_off=False):
        
        self._state_changed.sub(func, nice, one_off)
        
    def unsub_state_changed(self, func: Callable[[GraphStateEvent], None]):
        self._state_changed.unsub(func)
        
    def sub_event(self, e_type: GraphState | str, func, nice=0, one_off=False):
        e = self._get_event(e_type)
        if not e:
            return

        e.sub(func, nice, one_off)
    
    def unsub_event(self, e_type: GraphState | str, func):
        e = self._get_event(e_type)
        if e:
            e.unsub(func)
            
    def reset(self):
        self._state_changed = Event[GraphStateEvent]()
        
        self._on_play = NoArgsEvent()
        self._on_pause = NoArgsEvent()
        self._on_stop = NoArgsEvent()
        
        self._type_events = {
            GraphState.PLAYING: self._on_play,
            GraphState.PAUSED: self._on_pause,
            GraphState.STOPPED: self._on_stop
        }
        
        self._str_events = {
            'play': self._on_play,
            'pause': self._on_pause,
            'stop': self._on_stop
        }
    
    def _invoke_params(self, old_state: GraphState, new_state: GraphState):
        self._invoke(GraphStateEvent(old_state, new_state))
        
    def _invoke(self, state_event: GraphStateEvent):
        e = self._get_event(state_event.new_state)
        if e:
            e.emit()
        self._state_changed.emit(state_event)
        
    def _get_event(self, e_type: GraphState | str) -> Event:
        if e_type in self._type_events:
            return self._type_events[e_type]
        elif e_type in self._str_events:
            return self._str_events[e_type]
        else:
            return None
        
    
        
@dataclass
class GraphTime:
    """
    A class that wraps all time related information for a graph player.
    (fps, delta_time, time, etc)
    
    This class only makes sense if the graph has frame nodes.
    """
    
    _frames: int = 30
    _frame_count: int = 0
    _time: float = 0.0
    _delta_time: float = 0.0
    
    @property
    def frames(self):
        """The frame-rate this player will attempt to follow."""
        return self._frames
    
    @property
    def frame_count(self):
        """Frame count since time has started. Incremented at the start of each frame"""
        return self._frame_count
    
    @property
    def time(self):
        """Time (seconds) since the player has started."""
        return self._time
    
    @property
    def delta_time(self):
        """Interval (seconds) between the current frame and the last."""
        return self._delta_time

    def _set_delta_time(self, delta_time: float):
        """Sets the current delta time and adds it to the overall time."""
        self._delta_time = delta_time
        self._time += delta_time
        
    def frame_dur(self):
        """Frame duration the player will attempt to uphold."""
        return 1 / self._frames
    
    def avg_fps(self):
        """The average frames per second since the start of time."""
        if self._time == 0.0:
            return 0.0
        return self._frame_count / self._time
    
    def current_fps(self):
        """The current frames per second"""
        if self._delta_time == 0.0:
            return 0.0
        return 1 / self._delta_time
    
    def reset(self):
        self._frame_count = 0
        self._time = 0.0
        self._delta_time = 0.0
 
 
class GraphPlayer(ABC):
    """
    A player is a class that handles the life-time of a node program.
    In ryvencore's context, the executor should always be naive.
    """
    
    def __init__(self, frames: int = 30):
        super().__init__()
        # constructing
        self._flow = None
        self._state = GraphState.STOPPED
        
        # internal
        self._graph_time = GraphTime(_frames=frames)
        self._events = GraphEvents()
    
    @property
    def flow(self):
        """The flow for this player."""
        return self._flow
    
    @flow.setter
    def flow(self, value: Flow):
        if self._flow:
            self.stop()
        self._flow = value
    
    @property
    def graph_time(self):
        """Time information for this player"""
        return self._graph_time
    
    @property
    def graph_events(self):
        """Events for this graph"""
        return self._events
    
    def set_frames(self, value: int):
        if self._state != GraphState.STOPPED:
            return
        self._graph_time._frames = value
    
    @property
    def state(self):
        """The state of the player."""
        return self._state
    
    @abstractmethod
    def play(self):
        pass
    
    @abstractmethod
    def pause(self):
        pass
    
    @abstractmethod
    def resume(self):
        pass
    
    @abstractmethod
    def stop(self):
        pass
    
    def __is_stopped(self):
        return self._state == GraphState.STOPPED


class FlowPlayer(GraphPlayer):
    """The default implementation of a Graph Player in CogniX"""
    
    def __init__(self, frames: int = 35):
        super().__init__(frames)
        self._frame_nodes: list[FrameNode] = []
        self._nodes: list[Node] = []
        self._stop_flag = False
    
    def play(self):
        try:
            self.__play()
        except Exception as e:
            traceback.print_exc()
            raise e
        finally:
            self.__on_stop()
    
    def __play(self):
        # gather cognix nodes
        if self._state != GraphState.STOPPED:
            return
        
        self._stop_flag = False
        self._state = GraphState.PLAYING
        self.__gather_nodes()
        self._events._invoke_params(GraphState.STOPPED, GraphState.PLAYING)
        
        for node in self._nodes:
            node.reset()
        
        for node in self._nodes:
            node.start()
        
        if not self._frame_nodes:
            self.__on_stop()
            self._state = GraphState.STOPPED
            return
        
        while True:
            if self._stop_flag:
                break
            elif self._state == GraphState.PAUSED:
                time.sleep(self._graph_time.frame_dur())
                continue
            
            self._graph_time._frame_count += 1 # current frame
            start_time = time.perf_counter()
            for node in self.__gather_frame_nodes():
                node.frame_update()
            
            wait_time = self._graph_time.frame_dur() - (time.perf_counter() - start_time)
            if wait_time > 0:
                time.sleep(wait_time)
            
            # time info
            delta_time = time.perf_counter() - start_time
            self._graph_time._set_delta_time(delta_time)
                
        self.__on_stop()
        
    def pause(self):
        if self._state == GraphState.PLAYING:
            old_state = self._state
            self._state = GraphState.PAUSED
            self._events._invoke_params(old_state, GraphState.PAUSED)
    
    def resume(self):
        if self._state == GraphState.PAUSED:
            old_state = self._state
            self._state = GraphState.PLAYING
            self._events._invoke_params(old_state, GraphState.PLAYING)
    
    def stop(self):
        if self._state != GraphState.STOPPED:
            self._stop_flag = True
    
    def __gather_nodes(self):
        self._frame_nodes.clear()
        self._nodes.clear()
        
        for node in self._flow.nodes:
            if not isinstance(node, Node):
                continue
            self._nodes.append(node)
            if isinstance(node, FrameNode) and not node.is_finished:
                self._frame_nodes.append(node)
    
    def __gather_frame_nodes(self):
        return (node for node in self._flow.nodes if isinstance(node, FrameNode) and not node.is_finished)

    def __on_stop(self):
        """Only invoked when the player enters the STOPPED state."""
        if self._state == GraphState.STOPPED:
            return
        old_state = self._state
        self._state = GraphState.STOPPED
        for node in self._nodes:
            node.stop()
        self._events._invoke_params(old_state, GraphState.STOPPED)
        self._graph_time.reset()
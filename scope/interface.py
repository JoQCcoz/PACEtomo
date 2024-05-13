from abc import ABC, abstractmethod
from ..data.state import State

class Microscope(ABC):
    state: State = State()

    def set_tilt_angle(self, tilt_angle:float):
        self.state.set_tilt_angle(tilt_angle)

    def set_starting_angle(self, tilt_angle):
        self.state.set_starting_angle(tilt_angle)
    
    @abstractmethod
    def print(self, message):
        pass

    @abstractmethod
    def initialize(self):
        pass

    @abstractmethod
    def tilt_to_angle(self, tilt_angle):
        pass

    @abstractmethod
    def initial_realignment(self, tgt):
        pass

    @abstractmethod
    def delay_tilt(self, delay):
        pass


    @abstractmethod
    def reset_exposure_time(self):
        pass

    def update_state(self,**kwargs):
        for k,v in kwargs.items():
            k = f'_{k}'
            if not hasattr(self.state,k):
                raise AttributeError
            setattr(self.state,k,v)

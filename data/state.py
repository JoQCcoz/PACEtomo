from dataclasses import dataclass
from typing import Tuple

@dataclass
class State:
    _ISX0: float = None
    _ISY0: float = None
    _SSX0: float = None
    _SSY0: float = None
    _focus0: float = None
    _min_focus0:float = None
    _position_focus:float = None

    _fileStem: str = None
    _fileExt: str = None
    _curDir: str = None

    _current_tilt_angle: float = None
    _previous_tilt_angle_positive: float = None
    _previous_tilt_angle_negative: float = None
    _starting_tilt_angle: float = None
   
    @property
    def current_tilt_angle(self):
        return self._current_tilt_angle
    
    @property
    def starting_tilt_angle(self):
        if self.starting_tilt_angle is None:
            raise ValueError(f'_starting_tilt_angle not set. Use the set_starting_angle method first.')
        return self._current_tilt_angle

    def set_starting_angle(self, angle:float):
        self._starting_tilt_angle = angle
        if self._current_tilt_angle is None:
            self._current_tilt_angle = angle

    def set_tilt_angle(self,angle:float):
        previous = '_previous_tilt_angle_positive'
        if angle > 0:
            previous = '_previous_tilt_angle_negative'
        setattr(self,previous,self._current_tilt_angle)
        self._current_tilt_angle = angle

    def set_starting_image_shift(self, ISX0:float, ISY0:float):
        self._ISX0 = ISX0
        self._ISY0 = ISY0

    def set_starting_speciment_shift(self, SSX0:float, SSY0:float):
        self._SSX0 = SSX0
        self._SSY0 = SSY0

    def set_starting_focus(self, focus0, minFocus0):
        self._focus0 = focus0
        self._position_focus = focus0
        self._min_focus0 = minFocus0

    @property
    def previous_tilt_angle(self):
        previous = '_previous_tilt_angle_positive'
        if self._current_tilt_angle > 0:
            previous = '_previous_tilt_angle_negative'
        return getattr(self,previous)

    def get_step(self):
        return self._current_tilt_angle - self.previous_tilt_angle

        


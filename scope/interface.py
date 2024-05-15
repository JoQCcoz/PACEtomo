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
    def suppress_reports(self):
        pass

    @abstractmethod
    def get_current_item(self):
        pass

    @abstractmethod
    def report_directory(self):
        pass

    @abstractmethod
    def exit_warning(self):
        pass

    @abstractmethod
    def binary_choice(self):
        pass

    @abstractmethod
    def reset_exposure_time(self):
        pass

    @abstractmethod
    def exit(self):
        pass

    @abstractmethod
    def refresh_log_file(self, filename):
        pass

    @abstractmethod
    def user_set_directory(self):
        pass

    @abstractmethod
    def reset_clock(self):
        pass

    @abstractmethod
    def set_property(self, property_key, value):
        pass

    @abstractmethod
    def move_to_item(self):
        pass

    @abstractmethod
    def refine_eucentricity(self):
        pass

    @abstractmethod
    def realign_to_item(self):
        pass

    @abstractmethod
    def correct_intial_backlash(self,step=3):
        pass

    @abstractmethod
    def realign_preview(self):
        pass

    @abstractmethod
    def get_initial_focus(self, max_defocus, min_defocus):
        pass

    @abstractmethod
    def report_image_shift(self):
        pass

    @abstractmethod
    def report_specimen_shift(self):
        pass

    def get_starting_image_shift(self):
        ISX0, ISY0, *_ = self.report_image_shift()
        self.state.set_starting_image_shift(ISX0,ISY0)
    
    def get_starting_specimen_shift(self):
        SSX0, SSY0 = self.report_specimen_shift()
        self.state.set_starting_speciment_shift(SSX0,SSY0)

    def set_target_defocus(self, defocus:float) -> float:
        return defocus

    def update_state(self,**kwargs):
        for k,v in kwargs.items():
            k = f'_{k}'
            if not hasattr(self.state,k):
                raise AttributeError
            setattr(self.state,k,v)

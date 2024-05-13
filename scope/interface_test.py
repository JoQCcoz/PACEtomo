
from .interface import Microscope

class TestInterface(Microscope):

    def print(self, message:str) -> None:
        print(message)

    def initialize(self):
        self.update_state(fileStem='test',fileExt='.test',curDir='./')

    def delay_tilt(self, delay):
        return super().delay_tilt(delay)
    
    def initial_realignment(self, tgt):
        return super().initial_realignment(tgt)
    
    def reset_exposure_time(self):
        return super().reset_exposure_time()
    
    def tilt_to_angle(self, tilt_angle):
        return super().tilt_to_angle(tilt_angle)
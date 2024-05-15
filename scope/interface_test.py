import sys
import time
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
    
    def suppress_reports(self):
        self.print('Calling suppress report')

    def get_current_item(self):
        return super().get_current_item()
    
    def report_directory(self):
        return super().report_directory()
    
    def exit_warning(self,msg):
        self.print(msg)
        sys.exit(1)

    def binary_choice(self, msg):
        choice = input(msg + "\nYes:1\nNo:0")
        return bool(int(choice))
    
    def user_set_directory(self):
        return super().user_set_directory()
    
    def refresh_log_file(self, filename):
        return super().refresh_log_file(filename)
    
    def reset_clock(self):
        self.reset_time(time.time())

    def set_property(self, property_key, value):
        return super().set_property(property_key, value)
    
    def move_to_item(self):
        return super().move_to_item()
    
    def refine_eucentricity(self):
        return super().refine_eucentricity()
    
    def realign_to_item(self):
        return super().realign_to_item()
    
    def correct_intial_backlash(self, step=3):
        return super().correct_intial_backlash(step)
    
    def realign_preview(self):
        return super().realign_preview()
    
    def report_image_shift(self):
        return super().report_image_shift()
    
    def report_specimen_shift(self):
        return super().report_specimen_shift()
    
    def get_initial_focus(self, max_defocus, min_defocus):
        return super().get_initial_focus()
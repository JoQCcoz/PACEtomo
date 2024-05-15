
import os
from .interface import Microscope
import serialem as sem

class SerialemInterface(Microscope):

    def print(self, message:str) -> None:
        sem.Echo(message)

    def initialize(self):
        sem.SuppressReports()
        sem.ReportNavItem()
        navNote = sem.GetVariable("navNote")
        fileStem, fileExt = os.path.splitext(navNote)
        curDir = sem.ReportDirectory()
        self.update_state(fileStem=fileStem,fileExt=fileExt,curDir=curDir)


    def tilt(self):
        sem.TiltTo(self.state.current_tilt_angle)
        if self.state.current_tilt_angle < self.state.starting_tilt_angle:
            sem.TiltBy(-3)
            sem.TiltTo(self.state.current_tilt_angle)
            pn = 2
            return
        if slowTilt:										# on bad stages, better to do backlash as well to enhance accuracy
            sem.TiltBy(-3)
            sem.TiltTo(self.state.current_tilt_angle)
            pn = 1

    def set_exposure_time(self, exposure_time):
        if exposure_time > 0 and tilt_angle == startTilt:
            sem.SetExposure("R", exposure_time)

    def realign_preview(self):
        sem.LoadNavMap("O")									# preview ali before first tilt image is taken
        sem.Preview()
        sem.AlignTo("O")

    def report_image_shift(self):
        return sem.ReportImageShift()
    
    def report_specimen_shift(self):
        return sem.ReportSpecimenShift()
    
    def get_initial_focus(self, max_defocus, min_defocus):
        sem.G()
        focus0 = float(sem.ReportDefocus())
        # position_focus = focus0 										# set maxDefocus as focus0 and add focus steps in loop
        min_focus0 = focus0 - max_defocus + min_defocus
        self.state.set_starting_focus(focus0, min_focus0)

    def reset_exposure_time(self):
        ##I DON'T THING THE CHECK MATTERS
        # if zeroExpTime > 0 and tilt_angle == startTilt:
        sem.RestoreCameraSet("R")

    def suppress_reports(self):
        sem.SuppressReports()

    def get_current_item(self):
        sem.ReportNavItem()
        return sem.GetVariable("navNote")

    def report_directory(self):
        sem.ReportDirectory()

    def delay_tilt(self, delay):
        sem.Delay(delay)

    def exit_warning(self, msg):
        sem.OkBox(msg)
        sem.Exit()

    def binary_choice(self, msg) -> bool:
        choice = sem.YesNoBox(msg)
        return bool(choice)
    
    def exit(self):
        sem.Exit()

    def user_set_directory(self,msg):
        sem.UserSetDirectory(msg)
    
    def refresh_log_file(self,filename):
        sem.SaveLogOpenNew(filename)

    def reset_clock(self):
        sem.ResetClock()

    def set_target_defocus(self, defocus: float) -> float:
         sem.SetTargetDefocus(defocus)
         return super().set_target_defocus(defocus)
    
    def set_property(self, property_key, value):
        sem.SetProperty(property_key, value)
             
    def move_to_item(self):
        sem.MoveToNavItem()

    def refine_eucentricity(self):
        sem.SetCameraArea("V", "F")									# set View to Full for Eucentricity
        sem.Eucentricity(1)
        sem.UpdateItemZ()
        sem.RestoreCameraSet("V")

    def realign_to_item(self):
        sem.RealignToNavItem(1)

    def correct_initial_backlash(self, step=3):
        sem.V()
        sem.Copy("A", "O")

        sem.TiltBy(-2 * step)
        if slowTilt:
            sem.TiltBy(step)
        sem.TiltTo(self.state.starting_tilt_angle)

        sem.V()
        sem.AlignTo("O")
        sem.GoToLowDoseArea("R")
        

    def initial_realignment(self, tgt):
        sem.ImageShiftByMicrons(float(tgt["SSX"]), float(tgt["SSY"]) * tiltScaling)		# apply relative shifts to find out absolute IS after realign to item
        if settings.previewAli:										# adds initial dose, but makes sure start tilt image is on target
            if alignToP:
                sem.V()
                sem.AlignTo("P")
                sem.GoToLowDoseArea("R")
            elif "tgtfile" in tgt.keys():
                sem.ReadOtherFile(0, "O", tgt["tgtfile"])				# reads tgt file for first AlignTo instead
                sem.L()
                sem.AlignTo("O")	
        ISXset, ISYset, *_ = sem.ReportImageShift()
        SSX, SSY = sem.ReportSpecimenShift()
        sem.SetImageShift(ISX0, ISY0)
        return ISXset, ISYset, SSX, SSY

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

    def reset_exposure_time(self):
        ##I DON'T THING THE CHECK MATTERS
        # if zeroExpTime > 0 and tilt_angle == startTilt:
        sem.RestoreCameraSet("R")

    def delay_tilt(self, delay):
        sem.Delay(delay)

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
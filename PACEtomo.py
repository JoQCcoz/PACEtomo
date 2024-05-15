#!Python
# ===================================================================
#ScriptName	PACEtomo
# Purpose:	Runs parallel dose-symmetric tilt series on many targets with geometrical predictions using the first target as tracking tilt series.
# 		Make sure to run selectTargets script first to generate compatible Navigator settings and a target file.
#		More information at http://github.com/eisfabian/PACEtomo
# Author:	Fabian Eisenstein
# Created:	2021/04/16
# Revision:	v1.4.4
# Last Change:	2023/04/27: fixed addAF for negative branch
#		2022/10/14: fixed set dir loop, fixed premature completion
# ===================================================================

# ############ SETTINGS ############ 

# startTilt	= 0		# starting tilt angle [degrees] (should be divisible by step)
# minTilt		= -60		# minimum absolute tilt angle [degrees]
# maxTilt		= 60		# maximum absolute tilt angle [degrees]
# step		= 3		# tilt step [degrees]
# minDefocus	= -5		# minimum defocus [microns] of target range (low defocus)
# maxDefocus	= -5		# maximum defocus [microns] of target range (high defocus)
# stepDefocus	= 0.5		# step [microns] between target defoci (between TS)

# focusSlope	= 0.0		# empirical linear focus correction [microns per degree] (obtained by linear regression of CTF fitted defoci over tilt series; microscope stage dependent)
# delayIS		= 0.1		# delay [s] between applying image shift and Record
# delayTilt	= 0.1 		# delay [s] after stage tilt
# zeroExpTime	= 0 		# set to exposure time [s] used for start tilt image, if 0: use same exposure time for all tilt images
# trackExpTime	= 0		# set to exposure time [s] used for tracking tilt series, if 0: use same exposure time for all tilt series
# trackDefocus	= 0		# set to defocus [microns] used for tracking tilt series, if 0: use same defocus range for all tilt series

# # Geometry settings
# pretilt		= 0		# pretilt [degrees] of sample in deg e.g. after FIB milling (if milling direction is not perpendicular to the tilt axis, estimate and add rotation)
# rotation	= 0		# rotation [degrees] of lamella vs tilt axis in deg (should be 0 deg if lamella is oriented perpendicular to tilt axis)

# # Holey support settings
# tgtPattern 	= False		# use same tgt pattern on different stage positions (useful for collection on holey support film)
# alignToP	= False		# use generic image in buffer P to align to
# refineVec	= False		# refine tgt pattern for local stage position by aligning furthest targets along each axis to to buffer P
# measureGeo	= False		# estimates pretilt and rotation values of support film by measuring defocus on automatically determined points within tgt pattern

# # Session settings
# beamTiltComp	= True		# use beam tilt compensation (uses coma vs image shift calibrations)
# addAF		= False		# does autofocus at the start of every tilt group, increases exposure on tracking TS drastically
# previewAli	= True		# adds initial dose, but makes sure start tilt image is on target (uses view image and aligns to buffer P if alignToP == True)
# geoRefine	= False		# uses on-the-fly CtfFind results of first image to refine geometry before tilting (only use when CTF fits on your sample seem reliable)

# # Advanced settings
# doCtfFind	= True		# set to False to skip CTFfind estimation (only necessary if it causes crashes) 
# doCtfPlotter	= False		# runs ctfplotter instead of CTFfind, needs standalone version of 3Dmod on PATH
# fitLimit	= 30		# geoRefine: minimum resolution [Angstroms] needed for CTF fit to be considered for geoRefine
# parabolTh	= 9		# geoRefine: minimum number of passable CtfFind values to fit paraboloid instead of plane 
# imageShiftLimit	= 15		# maximum image shift [microns] SerialEM is allowed to apply (this is a SerialEM property entry, default is 15 microns)
# dataPoints	= 4		# number of recent specimen shift data points used for estimation of eucentric offset (default: 4)
# alignLimit	= 0.5		# maximum shift [microns] allowed for record tracking between tilts, should reduce loss of target in case of low contrast (not applied for tracking TS)
# minCounts	= 0 		# minimum mean counts per second of record image (if set > 0, tilt series branch will be aborted if mean counts are not sufficient)
# splitLog	= False		# splits log file every 4 tilts (in case of >50 targets, writing to a large log file can become slow)
# ignoreNegStart 	= True		# ignore first shift on 2nd branch, which is usually very large on bad stages
# slowTilt	= False		# do backlash step for all tilt angles, on bad stages large tilt steps are less accurate
# taOffsetPos	= 0 		# additional tilt axis offset values [microns] applied to calculations for postitive and...
# taOffsetNeg	= 0 		# ...negative branch of the tilt series (possibly useful for side-entry holder systems)
# extendedMdoc	= True		# saves additional info to .mdoc file
# checkDewar	= True		# check if dewars are refilling before every acquisition

# ########## END SETTINGS ########## 

import serialem as sem
import os
import copy
import time
import glob

import numpy as np
from scipy import optimize
from typing import List, Optional, Callable

from functions import calculations, files, serialemfuncs, loaders
from data.settings import PACEtomoSettings
from data.position import AcquisitionGroup
from scope.interface import Microscope

########### FUNCTIONS ###########

def do_position(position:PositionBranch, pos_idx, tilt_angle, settings:PACEtomoSettings):
		if pos_idx != 0 and position["skip"]: 
			sem.Echo("[" + str(pos_idx + 1) + "] was skipped on this branch.")
			continue
		if tilt_angle != settings.startTilt:
			sem.OpenOldFile(targets[pos_idx]["tsfile"])
			sem.ReadFile(position["sec"], "O")					# read last image of position for AlignTo
		else:
			sem.OpenNewFile(targets[pos_idx]["tsfile"])
			if not settings.tgtPattern and "tgtfile" in targets[pos_idx].keys():
				sem.ReadOtherFile(0, "O", targets[pos_idx]["tgtfile"])			# reads tgt file for first AlignTo instead

		### Calculate and apply predicted shifts
		SSchange = 0 										# only apply changes if not startTilt
		focuschange = 0
		if tilt_angle != settings.startTilt:
			SSchange = calculations.calcSSChange([tilt_angle, position["n0"]], position["z0"])
			focuschange = calculations.calcFocusChange([tilt_angle, position["n0"]], position["z0"])

		SSYprev = position["SSY"]
		SSYpred = position["SSY"] + SSchange

		focuscorrection = settings.focusSlope * (tilt_angle - settings.startTilt)
		position["focus"] += focuscorrection
		position["focus"] -= focuschange

		sem.SetDefocus(position["focus"])
		sem.SetImageShift(position["ISXset"], position["ISYset"])
		sem.ImageShiftByMicrons(0, SSchange)

		### Autofocus (optional) and tracking TS settings
		if pos_idx == 0:
			if settings.addAF and (tilt_angle - settings.startTilt) % (2 * settings.increment) != 0 and abs(tilt_angle - settings.startTilt) > settings.step:
				sem.G(-1)
				defocus, *_ = sem.ReportAutoFocus()
				focuserror = float(defocus) - targetDefocus
				for i in range(0, len(position)):
					position[i][pn]["focus"] -= focuserror
				sem.SetDefocus(position["focus"])
			if settings.trackDefocus < settings.maxDefocus:
				sem.SetDefocus(position["focus"] + settings.trackDefocus - targetDefocus)
			if settings.trackExpTime > 0:
				if tilt_angle == settings.startTilt:
					sem.SetExposure("R", max(settings.trackExpTime, settings.zeroExpTime))
				else:
					sem.SetExposure("R", settings.trackExpTime)

		### Record
		if settings.checkDewar: 
			checkFilling()
		if settings.beamTiltComp: 
			stig = sem.ReportObjectiveStigmator()
			sem.AdjustBeamTiltforIS()
		sem.Delay(settings.delayIS)
		sem.R()
		sem.S()
		if settings.beamTiltComp: 
			sem.RestoreBeamTilt()
			sem.SetObjectiveStigmator(stig[0], stig[1])

		if pos_idx != 0: 
			sem.LimitNextAutoAlign(settings.alignLimit)						# gives maximum distance for AlignTo to avoid runaway tracking
		if tilt_angle != settings.startTilt or not settings.tgtPattern: 
			sem.AlignTo("O")

		bufISX, bufISY = sem.ReportISforBufferShift()
		sem.ImageShiftByUnits(position["ISXali"], position["ISYali"])		# remove accumulated buffer shifts to calculate alignment to initial startTilt image

		position["focus"] += focuscorrection						# remove correction or it accumulates

		position["ISXset"], position["ISYset"], *_ = sem.ReportImageShift()

		if pos_idx == 0:										# apply measured shifts of first/tracking position to other positions
			for i in range(1, len(position)):
				position[i][pn]["ISXset"] += bufISX + position["ISXali"]	# apply accumulated (stage dependent) buffer shifts of tracking TS to all targets
				position[i][pn]["ISYset"] += bufISY + position["ISYali"]
				if tilt_angle == settings.startTilt:							# also save shifts from startTilt image for second branch since it will alignTo the startTilt image
					position[i][2]["ISXset"] += bufISX
					position[i][2]["ISYset"] += bufISY
					position[i][2]["ISXali"] += bufISX
					position[i][2]["ISYali"] += bufISY
			if tilt_angle == settings.startTilt:								# do not forget about 0 position
				position[0][2]["ISXset"] += bufISX
				position[0][2]["ISYset"] += bufISY
			if settings.trackExpTime > 0:
				sem.RestoreCameraSet("R")

		position["ISXali"] += bufISX
		position["ISYali"] += bufISY
		if tilt_angle == settings.startTilt:									# save alignment of first tilt to tgt file for the second branch
			position[pos_idx][2]["ISXali"] += bufISX
			position[pos_idx][2]["ISYali"] += bufISY

		position["SSX"], position["SSY"] = sem.ReportSpecimenShift()

		sem.Echo("[" + str(pos_idx + 1) + "] Prediction: y = " + str(round(SSYpred, 3)) + " | z = " + str(round(position["focus"], 3)) + " | z0 = " + str(round(position["z0"], 3)))
		sem.Echo("[" + str(pos_idx + 1) + "] Reality: y = " + str(round(position["SSY"], 3)))
		sem.Echo("[" + str(pos_idx + 1) + "] Focus change: " + str(round(focuschange, 3)) + " | Focus correction: " + str(round(focuscorrection, 3)))

		### Calculate new z0

		ddy = position["SSY"] - SSYprev
		if (tilt_angle == settings.startTilt or
				(settings.ignoreNegStart and pn == 2 and len(position["shifts"]) == 0) or
				recover or
				(resumePN == 1 and tilt_angle == resumePlus + settings.step and pos_idx < posResumed) or
				(resumePN == 1 and tilt_angle == resumeMinus - settings.step) or
				(resumePN == 2 and tilt_angle == resumeMinus - settings.step and pos_idx < posResumed) or
				(resumePN == 2 and tilt_angle == resumePlus + settings.step)):		
				# ignore shift if first image or first shift of second branch or first image after resuming run (all possible conditions)
			ddy = calculations.calcSSChange([tilt_angle, position["n0"]], position["z0"])

		position["shifts"].append(ddy)
		position["angles"].append(tilt_angle)

		if len(position["shifts"]) > settings.dataPoints:
			position["shifts"].pop(0)
			position["angles"].pop(0)

		position["z0"], cov = optimize.curve_fit(calculations.calcSSChange, np.vstack((position["angles"], [position["n0"] for i in range(0, len(position["angles"]))])), position["shifts"], p0=(position["z0"]))
		position["z0"] = position["z0"][0]

		if settings.doCtfFind:
			cfind = sem.CtfFind("A", (min(settings.maxDefocus, settings.trackDefocus) - 2), (settings.minDefocus + 2))
			sem.Echo("[" + str(pos_idx + 1) + "] CtfFind: " + str(round(cfind[0], 3)))

		if settings.doCtfPlotter:
			cplot = sem.Ctfplotter("A", (min(settings.maxDefocus, settings.trackDefocus) - 2), (settings.minDefocus + 2), 1, 0, pretilt)
			sem.Echo("[" + str(pos_idx + 1) + "] Ctfplotter: " + str(round(cplot[0], 3)))

		if settings.geoRefine and tilt_angle == settings.startTilt:
			if settings.doCtfPlotter:
				geo[0].append(position["SSX"])
				geo[1].append(position["SSY"])
				geo[2].append(cplot[0])
			elif settings.doCtfFind and len(cfind) > 5:
				if cfind[5] < settings.fitLimit:							# save vectors for geoRefine only if CTF fit has reasonable resolution
					geo[0].append(position["SSX"])
					geo[1].append(position["SSY"])
					geo[2].append(cfind[0])

		position["sec"] = int(sem.ReportFileZsize()) - 1				# save section number for next alignment

		progress = position["sec"] * len(position) + pos_idx + 1
		percent = round(100 * (progress / maxProgress), 1)
		bar = '#' * int(percent / 2) + '_' * (50 - int(percent / 2))
		if percent - resumePercent > 0:
			remTime = int((sem.ReportClock() - startTime) / (percent - resumePercent) * (100 - percent) / 60)
		else:
			remTime = "?"
		sem.Echo("Progress: |" + bar + "| " + str(percent) + " % (" + str(remTime) + " min remaining)")

		if settings.extendedMdoc:
			sem.AddToAutodoc("SpecimenShift", str(position["SSX"]) + " " + str(position["SSY"]))
			sem.AddToAutodoc("EucentricOffset", str(position["z0"]))
			if settings.doCtfFind:
				sem.AddToAutodoc("CtfFind", str(cfind[0]))
			if settings.doCtfPlotter:
				sem.AddToAutodoc("Ctfplotter", str(cplot[0]))
			sem.WriteAutodoc()

		sem.CloseFile()
		### Abort conditions
		if np.linalg.norm(np.array([position[pos][pn]["SSX"], position[pos][pn]["SSY"]], dtype=float)) > imageShiftLimit - alignLimit:
			position[pos][pn]["skip"] = True
			sem.Echo("WARNING: Target [" + str(pos + 1) + "] is approaching the image shift limit. This branch will be aborted.")

		if minCounts > 0:
			meanCounts = sem.ReportMeanCounts()
			expTime, *_ = sem.ReportExposure("R")
			if meanCounts / expTime < minCounts:
				position[pos][pn]["skip"] = True
				sem.Echo("WARNING: Target [" + str(pos + 1) + "] was too dark. This branch will be aborted.")

		if tilt_angle >= maxTilt or tilt_angle <= minTilt:
			position[pos][pn]["skip"] = True
			if maxTilt - startTilt != abs(minTilt - startTilt):
				sem.Echo("WARNING: Target [" + str(pos + 1) + "] has reached the final tilt angle. This branch will be aborted.")			

		updateTargets(runFileName, targets, position, position[pos][pn]["sec"], pos)	


def Tilt(microscope:Microscope, tilt_angle, targets, position):

	##THIS SHOULDN'T NEED TO BE GLOBAL
	# global recover

	microscope.set_tilt_angle(tilt_angle)

	microscope.tilt_to_angle()

	microscope.delay_tilt(delayTilt)

	microscope.set_exposure_time(zeroExpTime)

	###NEED TO MOVE THIS SOMEWHERE
	# if recover:
	# 	target = targets[0]
	# 	pos = position[0][pn]
	# 	# preview align to last tracking TS
	# 	sem.OpenOldFile(target["tsfile"])
	# 	sem.ReadFile(pos["sec"], "O")						# read last image of position for AlignTo
	# 	sem.SetDefocus(pos["focus"])
	# 	sem.SetImageShift(pos["ISXset"], pos["ISYset"])
	# 	if checkDewar: serialemfuncs.checkFilling()
	# 	sem.Preview()
	# 	sem.AlignTo("O")
	# 	bufISX, bufISY = sem.ReportISforBufferShift()
	# 	sem.ImageShiftByUnits(pos["ISXali"], pos["ISYali"])		# remove accumulated buffer shifts to calculate alignment to initial startTilt image
	# 	pos["ISXset"], pos["ISYset"], *_ = sem.ReportImageShift()
	# 	for pos in pos[1:]:
	# 		pos[pn]["ISXset"] += bufISX + pos["ISXali"]			# apply accumulated (stage dependent) buffer shifts of tracking TS to all targets
	# 		pos[pn]["ISYset"] += bufISY + pos["ISYali"]
	# 	sem.CloseFile()

	# 	posStart = posResumed
	# else:
	# 	posStart = 0

	for pos,  in range(posStart, len(position)):
		
		do_position(position[pos][pn])


	microscope.reset_exposure_time()

	###NEED TO MOVE THIS ELSEWHERE
	# if recover:
	# 	recover = False	

######## END FUNCTIONS ########

def get_microscope_interface(test=True):
	if test:
		from scope.interface_test import TestInterface
		return TestInterface
	from scope.serialem_interace import SerialemInterface
	return SerialemInterface

def main():

	##INITALIZE THE SETTINGS AND THE MICROSCOPE
	settings = PACEtomoSettings()
	scope = get_microscope_interface()
	microscope = scope()

	tilt_scheme = settings.get_tilt_scheme()

	tilt_scheme.check(printf=microscope.print)
	
	microscope.suppress_reports()

	if settings.tgtPattern:												# initialize in case tgts file contains values
		vecA0 = vecA1 = vecB0 = vecB1 = size = None

	### Find target file
	targets_loader:Callable = loaders.load_targets_from_files #HARDCODED FOR NOW BUT WILL LEAVE ROOM FOR ALTERNATIVE LOADERS LATER
	targets, savedRun, resume = targets_loader(microscope)

	###TO FIGURE OUT LATER. ### Recovery data
	# recoverInput = 0
	recover = False
	# realign = False
	# if savedRun != False and (resume["sec"] > 0 or resume["pos"] > 0):
	# 	recoverInput = sem.YesNoBox("The target file contains recovery data. Do you want to attempt to continue the acquisition? Tracking accuracy might be impacted.")
	# 	if recoverInput == 1:
	# 		recover = True
	# 		if sem.ReportFileNumber() > 0:								# make sure user closes all files to avoid file conflict crashes
	# 			sem.OKBox("Please close all open files in SerialEM and try again!")
	# 			sem.Exit()

	# 		stageX, stageY, stageZ = sem.ReportStageXYZ()
	# 		if abs(stageX - float(targets[0]["stageX"])) > 1.0 or abs(stageY - float(targets[0]["stageY"])) > 1.0:	# test if stage was moved (with 1 micron wiggle room)
	# 			userRealign = sem.YesNoBox("It seems that the stage was moved since stopping acquisition. Do you want to realign to the tracking target before resuming? This will also reset prediction parameters reducing tracking accuracy.")	
	# 			realign = True if userRealign == 1 else False
	# 	else:
	# 		sem.AllowFileOverwrite(1)

	### Start setup

	microscope.reset_clock()
	microscope.set_target_defocus(settings.maxDefocus) # use highest defocus for tracking TS

	if recover:
		microscope.print("##### Recovery attempt of PACEtomo with parameters: #####")
	else:
		microscope.print("##### Starting new PACEtomo with parameters: #####")
	microscope.print("Start: " + str(settings.startTilt) + " deg - Min/Max: " + str(settings.minTilt) + "/" + str(settings.maxTilt) + " deg (" + str(settings.step) + " deg increments)") ###NEED TO CHANGE THIS FOR CUSTOM SCHEME
	microscope.print("Data points used: " + str(settings.dataPoints))
	microscope.print("Target defocus range (min/max/step): " + str(settings.minDefocus) + "/" + str(settings.maxDefocus) + "/" + str(settings.stepDefocus))
	microscope.print("Sample pretilt (rotation): " + str(pretilt) + " (" + str(rotation) + ")")
	microscope.print("Focus correction slope: " + str(settings.focusSlope))

	# branchsteps = max(maxTilt - startTilt, abs(minTilt - startTilt)) / 2 / step
	microscope.set_property("ImageShiftLimit", settings.imageShiftLimit)

	### Create run file
	### THIS NEEDS TO GO ELSEWHERE
	# counter = 1
	# while os.path.exists(os.path.join(curDir, fileStem + "_run" + str(counter).zfill(2) + ".txt")):
	# 	counter += 1
	# runFileName = os.path.join(curDir, fileStem + "_run" + str(counter).zfill(2) + ".txt")

	### Initital actions
	if not recover:
		microscope.print("Realigning to target 1...")
		microscope.move_to_item()

		microscope.refine_eucentricity()

		###FOR LATER
		# if alignToP:
		# 	sem.V()
		# 	sem.AlignTo("P")
		# 	if refineVec and tgtPattern and size is not None:
		# 		if float(sem.ReportDefocus()) < -50:
		# 			sem.Echo("WARNING: Large defocus offsets for View can cause additional offsets in image shift upon mag change.")
		# 		size = int(size)
		# 		sem.Echo("Refining target pattern...")
		# 		sem.GoToLowDoseArea("R")
		# 		ISX0, ISY0, *_ = sem.ReportImageShift()
		# 		SSX0, SSY0 = sem.ReportSpecimenShift()
		# 		sem.Echo("Vector A: (" + str(vecA0) + ", " + str(vecA1) + ")")
		# 		shiftx = size * vecA0
		# 		shifty = size * vecA1
		# 		sem.ImageShiftByMicrons(shiftx, shifty)

		# 		sem.V()
		# 		sem.AlignTo("P")
		# 		sem.GoToLowDoseArea("R")

		# 		SSX, SSY = sem.ReportSpecimenShift()
		# 		SSX -= SSX0
		# 		SSY -= SSY0		
		# 		if np.linalg.norm([shiftx - SSX, shifty - SSY]) > 0.5:
		# 			sem.Echo("WARNING: Refined vector differs by more than 0.5 microns! Original vectors will be used.")
		# 		else:
		# 			vecA0, vecA1 = (round(SSX / size, 4), round(SSY / size, 4))
		# 			sem.Echo("Refined vector A: (" + str(vecA0) + ", " + str(vecA1) + ")")

		# 			sem.SetImageShift(ISX0, ISY0)						# reset IS to center position
		# 			sem.Echo("Vector B: (" + str(vecB0) + ", " + str(vecB1) + ")")
		# 			shiftx = size * vecB0
		# 			shifty = size * vecB1
		# 			sem.ImageShiftByMicrons(shiftx, shifty)

		# 			sem.V()
		# 			sem.AlignTo("P")
		# 			sem.GoToLowDoseArea("R")

		# 			SSX, SSY = sem.ReportSpecimenShift()
		# 			SSX -= SSX0
		# 			SSY -= SSY0
		# 			if np.linalg.norm([shiftx - SSX, shifty - SSY]) > 0.5:
		# 				sem.Echo("WARNING: Refined vector differs by more than 0.5 microns! Original vectors will be used.")
		# 			else:
		# 				vecB0, vecB1 = (round(SSX / size, 4), round(SSY / size, 4))
		# 				sem.Echo("Refined vector B: (" + str(vecB0) + ", " + str(vecB1) + ")")

		# 				targetNo = 0
		# 				for i in range(-size,size+1):
		# 					for j in range(-size,size+1):
		# 						if i == j == 0: continue
		# 						targetNo += 1
		# 						SSX = i * vecA0 + j * vecB0
		# 						SSY = i * vecA1 + j * vecB1
		# 						targets[targetNo]["SSX"] = str(SSX)
		# 						targets[targetNo]["SSY"] = str(SSY)
		# 				sem.Echo("Target pattern was overwritten using refined vectors.")
		# 		sem.SetImageShift(ISX0, ISY0)							# reset IS to center position
		# else:
		microscope.realign_to_item()
		####FOR LATER
		# if measureGeo and tgtPattern and size is not None:
		# 	sem.Echo("Measuring geometry...")
		# 	geoPoints = []
		# 	if size > 1:
		# 		geoPoints.append([0.5 * (vecA0 + vecB0), 0.5 * (vecA1 + vecB1)])
		# 	geoPoints.append([(size - 0.5) * (vecA0 + vecB0), (size - 0.5) * (vecA1 + vecB1)])
		# 	geoPoints.append([(size - 0.5) * (vecA0 - vecB0), (size - 0.5) * (vecA1 - vecB1)])
		# 	geoPoints.append([(size - 0.5) * (-vecA0 + vecB0), (size - 0.5) * (-vecA1 + vecB1)])
		# 	geoPoints.append([(size - 0.5) * (-vecA0 - vecB0), (size - 0.5) * (-vecA1 - vecB1)])
		# 	geoXYZ = [[], [], []]
		# 	sem.GoToLowDoseArea("R")
		# 	ISX0, ISY0, *_ = sem.ReportImageShift()
		# 	for i in range(len(geoPoints)):
		# 		sem.ImageShiftByMicrons(geoPoints[i][0], geoPoints[i][1])
		# 		sem.G(-1)
		# 		defocus, *_ = sem.ReportAutoFocus()
		# 		if defocus != 0:
		# 			geoXYZ[0].append(geoPoints[i][0])
		# 			geoXYZ[1].append(geoPoints[i][1])
		# 			geoXYZ[2].append(defocus)
		# 		sem.SetImageShift(ISX0, ISY0)							# reset IS to center position
		# 	##########
		# 	# Source: https://math.stackexchange.com/q/99317
		# 	# subtract out the centroid and take the SVD, extract the left singular vectors, the corresponding left singular vector is the normal vector of the best-fitting plane
		# 	svd = np.linalg.svd(geoXYZ - np.mean(geoXYZ, axis=1, keepdims=True))
		# 	left = svd[0]
		# 	norm = left[:, -1]
		# 	##########		
		# 	sem.Echo("Fitted plane into cloud of " + str(len(geoPoints)) + " points.")
		# 	sem.Echo("Normal vector: " + str(norm))
		# 	pretilt = round(-np.degrees(np.arctan(np.linalg.norm(norm[0:2]))), 1)
		# 	sem.Echo("Estimated pretilt: " + str(pretilt) + " degrees")
		# 	rotation = round(-np.degrees(np.arctan(norm[0]/norm[1])), 1)
		# 	sem.Echo("Estimated rotation: " + str(rotation) + " degrees")


		microscope.print("Tilting to start tilt angle...")
		# backlash correction
		microscope.set_starting_angle(tilt_scheme[0])
		microscope.correct_intial_backlash(step=3)

		if not settings.tgtPattern:
			microscope.realign_preview()

		microscope.get_starting_image_shift()
		microscope.get_starting_specimen_shift()
		microscope.get_initial_focus()
	
		### Target setup
		microscope.print("Setting up " + str(len(targets)) + " targets...")

		# posTemplate = {"SSX": 0, "SSY": 0, "focus": 0, "z0": 0, "n0": 0, "shifts": [], "angles": [], "ISXset": 0, "ISYset": 0, "ISXali": 0, "ISYali": 0, "sec": 0, "skip": False}
		position = AcquisitionGroup()
		for ind, tgt in enumerate(targets):
			if ind == 0:
				position.add_tracking_position(ind,tgt,settings,microscope)
			 
			# position.append([])
			# position[-1].append(copy.deepcopy(posTemplate))

			# skip = False
			# if "skip" in tgt.keys() and tgt["skip"] == "True":
			# 	sem.Echo("WARNING: Target [" + str(len(position)).zfill(3) + "] was set to be skipped.")
			# 	skip = True
			# if np.linalg.norm(np.array([tgt["SSX"], tgt["SSY"]], dtype=float)) > imageShiftLimit - alignLimit:
			# 	sem.Echo("WARNING: Target [" + str(len(position)).zfill(3) + "] is too close to the image shift limit. This target will we skipped.")
			# 	skip = True

			# if skip: 
			# 	position[-1][0]["skip"] = True
			# 	position[-1].append(copy.deepcopy(position[-1][0]))
			# 	position[-1].append(copy.deepcopy(position[-1][0]))
			# 	continue

			# tiltScaling = np.cos(np.radians(pretilt * np.cos(np.radians(rotation)) + startTilt)) / np.cos(np.radians(pretilt * np.cos(np.radians(rotation))))	# stretch shifts from 0 tilt to startTilt
			# sem.ImageShiftByMicrons(float(tgt["SSX"]), float(tgt["SSY"]) * tiltScaling)		# apply relative shifts to find out absolute IS after realign to item
			# if previewAli:										# adds initial dose, but makes sure start tilt image is on target
			# 	if alignToP:
			# 		sem.V()
			# 		sem.AlignTo("P")
			# 		sem.GoToLowDoseArea("R")
			# 	elif "tgtfile" in tgt.keys():
			# 		sem.ReadOtherFile(0, "O", tgt["tgtfile"])				# reads tgt file for first AlignTo instead
			# 		sem.L()
			# 		sem.AlignTo("O")	
			# ISXset, ISYset, *_ = sem.ReportImageShift()
			# SSX, SSY = sem.ReportSpecimenShift()
			# sem.SetImageShift(ISX0, ISY0)								# reset IS to center position	

			# z0_ini = np.tan(np.radians(pretilt)) * (np.cos(np.radians(rotation)) * float(tgt["SSY"]) - np.sin(np.radians(rotation)) * float(tgt["SSX"]))
			# correctedFocus = positionFocus - z0_ini * np.cos(np.radians(startTilt)) - float(tgt["SSY"]) * np.sin(np.radians(startTilt))

			# position[-1][0]["SSX"] = float(SSX)
			# position[-1][0]["SSY"] = float(SSY)
			# position[-1][0]["focus"] = correctedFocus
			# position[-1][0]["z0"] = z0_ini								# offset from eucentric height (will be refined during collection)
			# position[-1][0]["n0"] = float(tgt["SSY"])						# offset from tilt axis
			# position[-1][0]["ISXset"] = float(ISXset)
			# position[-1][0]["ISYset"] = float(ISYset)

			# position[-1].append(copy.deepcopy(position[-1][0]))					# plus and minus branch start with same values
			# position[-1].append(copy.deepcopy(position[-1][0]))

			# position[-1][1]["n0"] -= taOffsetPos
			# position[-1][2]["n0"] -= taOffsetNeg

			# positionFocus += stepDefocus								# adds defocus step between targets and resets to initial defocus if minDefocus is surpassed
			# if positionFocus > minFocus0: positionFocus = focus0

		### Start tilt
		sem.Echo("Start tilt series...")
		maxProgress = ((maxTilt - minTilt) / step + 1) * len(position)
		resumePercent = 0
		startTime = sem.ReportClock()

		geo = [[], [], []]

		plustilt = minustilt = startTilt
		Tilt(startTilt, targets=targets,position=position)

		if geoRefine:
			if len(geo[2]) >= 3:									# if number of points > 3: fit z = a * x + b * y
				sem.Echo("Refining geometry...")
				sem.Echo(str(len(geo[2])) + " usable CtfFind results found.")
				if len(geo[2]) >= parabolTh:							# if number of points > 6: fit z = a * x + b * y + c * (x**2) + d * (y**2) + e * x * y
					sem.Echo("Fitting paraboloid...")
					geoF = geoPara
				else:							
					sem.Echo("Fitting plane...")
					geoF = geoPlane

				p, cov = optimize.curve_fit(geoF, [geo[0], geo[1]], [z - geo[2][0] for z in geo[2]])

				ss = 0
				for i in range(0, len(geo[2])):
					ss += (geo[2][i] - geo[2][0] - geoF([geo[0][i], geo[1][i]], *p))**2
				rmse = np.sqrt(ss / len(geo[2]))

				sem.Echo("Fit parameters: " + " # ".join(p.astype(str)))
				sem.Echo("RMSE: " + str(round(rmse, 3)))

				for pos in range(0, len(position)):						# calculate and adjust refined z0
					zs = geoF([position[pos][1]["SSX"], position[pos][1]["SSY"]], *p)
					z0_ref = position[pos][1]["z0"] + zs * np.cos(np.radians(startTilt)) + position[pos][1]["SSY"] * np.sin(np.radians(startTilt))

					position[pos][1]["z0"] = z0_ref
					position[pos][2]["z0"] = z0_ref
			else: 
				sem.Echo("WARNING: Not enough reliable CtfFind results (" + str(len(geo[2])) + ") to refine geometry. Continuing with initial geometry model.")

		startstep = 0
		substep = [0, 0]
		posResumed = -1
		resumePN = 0

	#####FOR LATER
	# ### Recovery attempt
	# else:
	# 	if realign:
	# 		sem.MoveToNavItem()
	# 		if alignToP:
	# 			sem.V()
	# 			sem.AlignTo("P")
	# 		else:
	# 			sem.RealignToNavItem(1)
	# 	position = []
	# 	for pos in range(len(targets)):
	# 		position.append([{},{},{}])
	# 		for i in range(2):
	# 			position[-1][i+1]["SSX"] = float(savedRun[pos][i]["SSX"])
	# 			position[-1][i+1]["SSY"] = float(savedRun[pos][i]["SSY"])
	# 			position[-1][i+1]["focus"] = float(savedRun[pos][i]["focus"])
	# 			position[-1][i+1]["z0"] = float(savedRun[pos][i]["z0"])
	# 			position[-1][i+1]["n0"] = float(savedRun[pos][i]["n0"])
	# 			if savedRun[pos][i]["shifts"] != "" and not realign:
	# 				position[-1][i+1]["shifts"] = [float(shift) for shift in savedRun[pos][i]["shifts"].split(",")]
	# 			else:
	# 				position[-1][i+1]["shifts"] = []
	# 			if savedRun[pos][i]["angles"] != "" and not realign:
	# 				position[-1][i+1]["angles"] = [float(angle) for angle in savedRun[pos][i]["angles"].split(",")]
	# 			else:
	# 				position[-1][i+1]["angles"] = []
	# 			position[-1][i+1]["ISXset"] = float(savedRun[pos][i]["ISXset"])
	# 			position[-1][i+1]["ISYset"] = float(savedRun[pos][i]["ISYset"])
	# 			position[-1][i+1]["ISXali"] = float(savedRun[pos][i]["ISXali"])
	# 			position[-1][i+1]["ISYali"] = float(savedRun[pos][i]["ISYali"])
	# 			position[-1][i+1]["sec"] = int(savedRun[pos][i]["sec"])
	# 			position[-1][i+1]["skip"] = True if savedRun[pos][i]["skip"] == "True" or targets[pos]["skip"] == "True" else False

	# 	startstep = (resume["sec"] - 1) // 4 								# figure out start values for branch loops
	# 	substep = [min((resume["sec"] - 1) % 4, 2), (resume["sec"] - 1) % 4 // 3]

	# 	plustilt = resumePlus = float(savedRun[resume["pos"]][0]["angles"].split(",")[-1])		# obtain last angle from savedRun in case position["angles"] was reset
	# 	if substep[0] < 2:										# subtract step when stopped during positive branch
	# 		plustilt -= step
	# 		resumePN = 1 										# indicator which branch was interrupted
	# 		sem.TiltTo(plustilt)
	# 	if savedRun[pos][1]["angles"] != "":
	# 		minustilt = resumeMinus = float(savedRun[resume["pos"]][1]["angles"].split(",")[-1])
	# 		if substep[0] == 2:									# add step when stopped during negative branch
	# 			minustilt += step
	# 			resumePN = 2
	# 			sem.TiltTo(minustilt)
	# 	else:
	# 		minustilt = resumeMinus = startTilt

	# 	posResumed = resume["pos"] + 1

	# 	maxProgress = ((maxTilt - minTilt) / step + 1) * len(position)
	# 	progress = resume["sec"] * len(position) + resume["pos"]
	# 	resumePercent = round(100 * (progress / maxProgress), 1)
	# 	startTime = sem.ReportClock()


	### Tilt series
	for i in range(startstep, int(np.ceil(branchsteps))):
		for j in range(substep[0], 2):
			plustilt += step
			if all([pos[1]["skip"] for pos in position]): continue
			sem.Echo("Tilt step " + str(i * 4 + j + 1) + " out of " + str(int((maxTilt - minTilt) / step + 1)) + " (" + str(plustilt) + " deg)...")
			Tilt(plustilt, targets=targets,position=position)
		for j in range(substep[1], 2):
			minustilt -= step
			if all([pos[2]["skip"] for pos in position]): continue
			sem.Echo("Tilt step " + str(i * 4 + j + 3) + " out of " + str(int((maxTilt - minTilt) / step + 1)) + " (" + str(minustilt) + " deg)...")
			Tilt(minustilt, targets=targets,position=position)
		substep = [0, 0]										# reset substeps after recovery
		if splitLog: sem.SaveLogOpenNew(navNote.split("_tgts")[0])

	### Finish
	sem.TiltTo(0)
	sem.SetDefocus(0)
	sem.SetImageShift(0, 0)
	sem.CloseFile()
	files.updateTargets(runFileName, targets)

	totalTime = round(sem.ReportClock() / 60, 1)
	perTime = round(totalTime / len(position), 1)
	if recoverInput == 1:
		perTime = "since recovery: " + str(perTime)
	print("##### All tilt series completed in " + str(totalTime) + " min (" + str(perTime) + " min per tilt series) #####")
	sem.SaveLog()
	sem.Exit()

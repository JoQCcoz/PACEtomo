import os
import glob
from ..scope.interface import Microscope
from files import parseTargets


def load_targets_from_files(microscope:Microscope):
	navNote = microscope.get_current_item()

	file_stem, file_ext = os.path.splitext(navNote)
	curDir = microscope.report_directory()

	if file_stem == "" or file_ext != ".txt":
		microscope.exit_warning("The navigator item note does not contain a target file. Make sure to setup PACEtomo targets using the selectTargets script!")

	tf = sorted(glob.glob(os.path.join(curDir, file_stem + ".txt")))					# find  tgts file
	tfr = sorted(glob.glob(os.path.join(curDir, file_stem + "_run??.txt")))				# find run files but not copied tgts file
	tf.extend(tfr)											# only add run files to list of considered files

	while tf == []:
		searchInput = microscope.binary_choice("\n".join(["Target file not found! Please choose the directory containing the target file!", "WARNING: All future target files will be searched here!", "Do you want to choose a new directory?"]))
		if not searchInput:
			microscope.exit()
		microscope.user_set_directory("Please choose the directory containing the target file!")
		curDir = microscope.report_directory()
		tf = sorted(glob.glob(os.path.join(curDir, file_stem + "*.txt")))

	#NOT SURE THIS SHOULD GO HERE
	microscope.refresh_log_file(navNote.split("_tgts")[0])

	#THIS SEEMS PRONE TO ERROR WITH THE WAY ITS SORTED BUT I LEAVE FOR NOW
	with open(os.path.join(curDir, tf[-1])) as f:								# open last tgts or tgts_run file
		targetFileLines = f.readlines()

	return parseTargets(targetFileLines)
	

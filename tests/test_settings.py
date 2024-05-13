import pytest
from ..data.settings import PACEtomoSettings


startTilt	= 0		# starting tilt angle [degrees] (should be divisible by step)
minTilt		= -60		# minimum absolute tilt angle [degrees]
maxTilt		= 60		# maximum absolute tilt angle [degrees]
step		= 3		# tilt step [degrees]
minDefocus	= -5		# minimum defocus [microns] of target range (low defocus)
maxDefocus	= -5		# maximum defocus [microns] of target range (high defocus)
stepDefocus	= 0.5		# step [microns] between target defoci (between TS)

focusSlope	= 0.0		# empirical linear focus correction [microns per degree] (obtained by linear regression of CTF fitted defoci over tilt series; microscope stage dependent)
delayIS		= 0.1		# delay [s] between applying image shift and Record
delayTilt	= 0.1 		# delay [s] after stage tilt
zeroExpTime	= 0 		# set to exposure time [s] used for start tilt image, if 0: use same exposure time for all tilt images
trackExpTime	= 0		# set to exposure time [s] used for tracking tilt series, if 0: use same exposure time for all tilt series
trackDefocus	= 0		# set to defocus [microns] used for tracking tilt series, if 0: use same defocus range for all tilt series

pretilt:int		= 1	# pretilt [degrees] of sample in deg e.g. after FIB milling (if milling direction is not perpendicular to the tilt axis, estimate and add rotation)
rotation:int	= 0		# rotation [degrees] of lamella vs tilt axis in deg (should be 0 deg if lamella is oriented perpendicular to tilt axis)

# Holey support settings
tgtPattern:bool 	= False		# use same tgt pattern on different stage positions (useful for collection on holey support film)
alignToP:bool	= False		# use generic image in buffer P to align to
refineVec:bool	= False		# refine tgt pattern for local stage position by aligning furthest targets along each axis to to buffer P
measureGeo:bool	= False		# estimates pretilt and rotation values of support film by measuring defocus on automatically determined points within tgt pattern

# Session settings
beamTiltComp:bool	= True		# use beam tilt compensation (uses coma vs image shift calibrations)
addAF:bool		= False		# does autofocus at the start of every tilt group, increases exposure on tracking TS drastically
previewAli:bool	= True		# adds initial dose, but makes sure start tilt image is on target (uses view image and aligns to buffer P if alignToP == True)
geoRefine:bool	= False		# uses on-the-fly CtfFind results of first image to refine geometry before tilting (only use when CTF fits on your sample seem reliable)

# Advanced settings
doCtfFind:bool	= True		# set to False to skip CTFfind estimation (only necessary if it causes crashes) 
doCtfPlotter:bool	= False		# runs ctfplotter instead of CTFfind, needs standalone version of 3Dmod on PATH
fitLimit:int	= 30		# geoRefine: minimum resolution [Angstroms] needed for CTF fit to be considered for geoRefine
parabolTh:int	= 9		# geoRefine: minimum number of passable CtfFind values to fit paraboloid instead of plane 
imageShiftLimit:int	= 15		# maximum image shift [microns] SerialEM is allowed to apply (this is a SerialEM property entry, default is 15 microns)
dataPoints:int	= 4		# number of recent specimen shift data points used for estimation of eucentric offset (default: 4)
alignLimit:float	= 0.5		# maximum shift [microns] allowed for record tracking between tilts, should reduce loss of target in case of low contrast (not applied for tracking TS)
minCounts:float	= 1		# minimum mean counts per second of record image (if set > 0, tilt series branch will be aborted if mean counts are not sufficient)
splitLog:bool	= False		# splits log file every 4 tilts (in case of >50 targets, writing to a large log file can become slow)
ignoreNegStart:bool 	= True		# ignore first shift on 2nd branch, which is usually very large on bad stages
slowTilt:bool	= False		# do backlash step for all tilt angles, on bad stages large tilt steps are less accurate
taOffsetPos:int	= 0 		# additional tilt axis offset values [microns] applied to calculations for postitive and...
taOffsetNeg:int	= 0 		# ...negative branch of the tilt series (possibly useful for side-entry holder systems)
extendedMdoc:bool	= True		# saves additional info to .mdoc file
checkDewar:bool	= True		# check if dewars are refilling before every acquisition

def test_initialize():
    settings = PACEtomoSettings.initialize(**globals())
    assert all([settings.pretilt == 1,settings.minCounts==1])

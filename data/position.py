import copy
from dataclasses import dataclass, field,
from typing import get_type_hints, List
from .settings import PACEtomoSettings
from ..functions import calculations # scale_tilt, calc_z0, correct_focus, is_approaching_limit
from ..scope.interface import Microscope


def check_if_target_skipped(tgt, settings) -> bool:
	if "skip" in tgt.keys() and tgt["skip"] == "True":
		return True
	if calculations.is_approaching_limit(SSX=tgt["SSX"],SSY=tgt["SSY"], limit=settings.imageShiftLimit - settings.alignLimit):
		return True
	return False


@dataclass
class PositionBranch:
	_SSX: float = 0.0
	_SSY: float = 0.0
	_focus: float = 0.0
	_z0: float = 0.0
	_n0: float = 0.0
	_shifts: List = field(default_factory=list)
	_angles: List = field(default_factory=list)
	_ISXset: float = 0.0
	_ISYali: float = 0.0
	_sec: int = 0
	_skip: bool = False

	def set_params(self,**kwargs):
		for k,v in kwargs.items():
			k = "_" + k 
			if not hasattr(self,k):
				raise AttributeError(f"Attribute {k} does not exists. Choices are {', '.join(vars(self).keys())}")
			setattr(self,k,v)
			
	@property
	def SSX(self):
		return self._SSX
	
	@property
	def SSY(self):
		return self._SSY
	
	@property
	def focus(self):
		return self._focus
	
	@property
	def z0(self):
		return self._z0
	
	@property
	def n0(self):
		return self._n0
	
	@property
	def shifts(self):
		return self._shifts
	
	@property
	def angles(self):
		return self._angles
	
	@property
	def ISXset(self):
		return self._ISXset
	
	@property
	def ISYset(self):
		return self._ISYali
	
	@property
	def sec(self):
		return self._sec
	
	@property
	def skip(self):
		return self._skip
	
	@skip.setter
	def skip(self, v:bool) -> None:
		
		if not isinstance(v,get_type_hints(self)['_skip']):
			raise TypeError(f'Skip attribute should be a bool. Got {v} of type {type(v).__name__}.')
		self._skip = v 



@dataclass
class Position:
	index: int
	start: PositionBranch
	positive: PositionBranch = None
	negative: PositionBranch = None


	@classmethod
	def initialize(cls, index, tgt, settings:PACEtomoSettings, microscope:Microscope):
		start = PositionBranch()

		if check_if_target_skipped(tgt,settings):
			microscope.print("WARNING: Target [" + str(len(index)).zfill(3) + "] is set to be skipped.")
			return cls(index=index,start=start,positive=start,negative=start)

		tiltScaling = calculations.scale_tilt(pre_tilt=settings.pretilt,start_tilt=settings.startTilt,rotation=settings.rotation)	# stretch shifts from 0 tilt to startTilt

		ISXset, ISYset, SSX, SSY = microscope.intitial_realignment(tgt, tiltScaling)

		z0_ini = calculations.calc_z0(SSX,SSY,pre_tilt=settings.pretilt,rotation=settings.rotation)
		correctedFocus = calculations.correct_focus(position_focus=positionFocus,SSY=SSY,z0=z0_ini,start_tilt=settings.startTilt)

		start.set_params(SSX=float(SSX),
                        SSY=float(SSY),
                        focus=correctedFocus,
                        z0=z0_ini,			# offset from eucentric height (will be refined during collection)
                        n0= float(tgt["SSY"]),						# offset from tilt axis
                        ISXset = float(ISXset),
                        ISYset = float(ISYset),
            )

		positive = copy.deepcopy(start)				# plus and minus branch start with same values
		negative = copy.deepcopy(start)

		positive.set_params(n0= positive.n0 - settings.taOffsetPos)
		negative.set_params(n0= negative.n0 - settings.taOffsetNeg)

		return cls(index=index,start=start,positive=positive,negative=negative)

		positionFocus += settings.stepDefocus								# adds defocus step between targets and resets to initial defocus if minDefocus is surpassed
		if positionFocus > minFocus0: 
			positionFocus = focus0

@dataclass
class TrackingPosition(Position):
	pass

@dataclass
class GeoPosition(Position):
	pass

@dataclass
class AquisitionGroup:
	_tracking: TrackingPosition = None
	_positions: List[Position] = field(default_factory=list)
	_geopositions: List[GeoPosition] = field(default_factory=list)

	def add_tracking_position(self,index, target,settings,microscope):
		self.tracking = TrackingPosition.initialize(index,target,settings,microscope)

	def add_position(self,index,target,settings,microscope):
		self.positions.append(Position.initialize(index,target,settings,microscope))



import numpy as np

def geoPlane(x, a, b):
	return a * x[0] + b * x[1]

def geoPara(x, a, b, c, d, e):
	return a * x[0] + b * x[1] + c * (x[0]**2) + d * (x[1]**2) + e * x[0] * x[1]

def calcSSChange(x, z0, increment):									# x = array(tilt, n0) => needs to be one array for optimize.curve_fit()
    return x[1] * (np.cos(np.radians(x[0])) - np.cos(np.radians(x[0] - increment))) - z0 * (np.sin(np.radians(x[0])) - np.sin(np.radians(x[0] - increment)))

def calcFocusChange(x, z0,  increment):									# x = array(tilt, n0) => needs to be one array for optimize.curve_fit()
    return z0 * (np.cos(np.radians(x[0])) - np.cos(np.radians(x[0] - increment))) + x[1] * (np.sin(np.radians(x[0])) - np.sin(np.radians(x[0] - increment)))

def scale_tilt(pre_tilt:float=0, start_tilt:float=0, rotation:float=0) -> float:
    return np.cos(np.radians(pre_tilt * np.cos(np.radians(rotation)) + start_tilt)) / np.cos(np.radians(pre_tilt * np.cos(np.radians(rotation))))

def calc_z0(SSX,SSY,pre_tilt:float=0,rotation:float=0) -> float:
    return np.tan(np.radians(pre_tilt)) * (np.cos(np.radians(rotation)) * SSY - np.sin(np.radians(rotation)) * SSX)

def correct_focus(position_focus:float, SSY:float, z0:float=0, start_tilt:float=0)-> float:
     return position_focus - z0 * np.cos(np.radians(start_tilt)) - SSY * np.sin(np.radians(start_tilt))

def is_approaching_limit(SSX:float,SSY:float, limit:float) -> bool:
     return np.linalg.norm(np.array([SSX,SSY], dtype=float)) > limit
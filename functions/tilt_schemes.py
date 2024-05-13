from typing import List
from math import ceil
from pathlib import Path


def load_tilt_scheme_from_file(file:Path) -> List[float]:
    def to_float(val:str):
        val = val.strip()
        if not val.lstrip('+-').isnumeric():
            raise ValueError(f'Cannot convert {val} to float')
        return float(val)
    
    with open(file, 'r') as f:
        lines = f.readlines()
    return list(map(to_float,lines))
        

def create_dose_symmetric_scheme(start_tilt, min_tilt, max_tilt, step) -> List[float]:
    tilt_scheme = [start_tilt]
    branchsteps = max(max_tilt - start_tilt, abs(min_tilt - start_tilt)) / 2 / step
    plustilt = minustilt = start_tilt
    for _ in range(int(ceil(branchsteps))):
        for _ in range(2):
            plustilt += step
            if plustilt <= max_tilt:
                tilt_scheme.append(plustilt)
        for _ in range(2):
            minustilt -= step
            if minustilt >= min_tilt:
                tilt_scheme.append(minustilt)
    return tilt_scheme
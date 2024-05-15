from typing import List, Callable

def parseTargets(targetFileLines:List[str], printf:Callable=print):
    targets = []
    savedRun = []
    branch = None
    resume = {"sec": 0, "pos": 0}
    for line in targetFileLines:
        col = line.split(" ")
        if col[0] == "": 
            continue
        if line.startswith("_set") and len(col) == 4:
            if col[1] in globals():
                printf(f"WARNING: Read setting from tgts file and overwrite: {col[1]} = {col[3]}")
                globals()[col[1]] = float(col[3])
            else:
                printf(f"WARNING: Attempted to overwrite {col[1]} but variable does not exist!")
        elif line.startswith("_spos"):
            resume["sec"] = int(col[2].split(",")[0])
            resume["pos"] = int(col[2].split(",")[1])
        elif line.startswith("_tgt"):
            targets.append({})
            branch = None
        elif line.startswith("_pbr"):
            savedRun.append([{},{}])
            branch = 0
        elif line.startswith("_nbr"):
            branch = 1
        else:
            if branch is None:
                targets[-1][col[0]] = col[2]
            else:
                savedRun[-1][branch][col[0]] = col[2]

    if savedRun == []: 
        savedRun = False
    return targets, savedRun, resume

####ADD ALL THE OTHER PARAMS
def updateTargets(fileName, targets, position=[], sec=0, pos=0):
    output = ""
    if sec > 0 or pos > 0:
        output += f"_set startTilt = {str(startTilt)}\n"
        output += f"_set minTilt = {str(minTilt)}\n"
        output += f"_set maxTilt = {str(maxTilt)}\n"
        output += f"_set step = {str(step)}\n"
        output += f"_set pretilt = {str(pretilt)}\n"
        output += f"_set rotation = {str(rotation)}\n"
        output += f"_spos = {str(sec)},{str(pos)}\n" * 2
    for pos in range(len(targets)):
        output += f"_tgt = {str(pos + 1).zfill(3)}\n"
        for key in targets[pos].keys():
            output += f"""{key} = {targets[pos][key]}\n"""
        if position != []:
            output += "_pbr\n"
            for key in position[pos][1].keys():
                output += f"""{key} = {str(position[pos][1][key]).strip("[]").replace(" ","")}\n"""
            output += "_nbr\n"
            for key in position[pos][2].keys():
                output += f"""{key} = {str(position[pos][2][key]).strip("[]").replace(" ","")}\n"""		
        output += "\n"
    with open(fileName, "w") as f:
        f.write(output)
from typing import Callable

class TiltScheme(list):

    def check(self, printf:Callable) -> bool:
        checks = list(filter(lambda x: any([x > 70, x < -70]), self))
        if checks != []:
            printf("WARNING: Tilt angles go beyond +/- 70 degrees. Most stage limitations do not allow for symmetrical tilt series with these values!")
            return False
        return True

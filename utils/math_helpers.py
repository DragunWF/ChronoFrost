import math


def get_distance(x1: float, y1: float, x2: float, y2: float) -> float:
    """Calculate the Euclidean distance between two points."""
    return math.hypot(x2 - x1, y2 - y1)


def get_angle(x1: float, y1: float, x2: float, y2: float) -> float:
    """Calculate the angle (in radians) from point 1 to point 2."""
    return math.atan2(y2 - y1, x2 - x1)

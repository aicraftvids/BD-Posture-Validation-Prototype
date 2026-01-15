import pytest
from processor import angle_between_points, evaluate_posture

def test_angle_between_points_right_angle():
    # triangle with right angle at b: a=(1,0), b=(0,0), c=(0,1) -> 90 deg
    a = (1,0)
    b = (0,0)
    c = (0,1)
    ang = angle_between_points(a,b,c)
    assert ang is not None
    assert abs(ang - 90.0) < 1e-3

def test_evaluate_posture_empty():
    # empty landmarks sequence should return a summary with zero frames inspected
    rep = evaluate_posture([], 0)
    assert "frames_inspected" in rep
    assert rep["frames_inspected"] == 0

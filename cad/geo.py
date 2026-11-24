"""Shared geometry helpers (world positions of things), used by panels, parts, wires and checks."""
import math

import params as P

T = P.T


def tilt_cs(deg):
    a = math.radians(deg)
    return math.sin(a), math.cos(a)


def local_to_world(frame, lx, ly, lz):
    """Map a point in a tilted plate's local frame to the world.

    Local frame: x across the plate, y BEHIND the plate's front face (negative y is in front of it),
    z up the plate. frame = (x0, y0, z0, tilt_deg): world position of the front face's bottom-left
    corner and the tilt from vertical (leaning back)."""
    x0, y0, z0, deg = frame
    s, c = tilt_cs(deg)
    return (x0 + lx, y0 + c * ly + s * lz, z0 - s * ly + c * lz)


STRIP_FRAME = (P.STRIP_X0, P.STRIP_Y, P.STRIP_Z, P.STRIP_TILT)


def plate_frame():
    return (P.SCREEN_CX - P.PLATE_W / 2, P.SCREEN_Y, P.SCREEN_Z, P.SCREEN_TILT)


def strip_pt(u, ly, v):
    return local_to_world(STRIP_FRAME, u, ly, v)


def rear_face_pt(frame, v):
    """(y, z) of the rear face line of a tilted plate at distance v up the plate."""
    _, y, z = local_to_world(frame, 0, T, v)
    return (y, z)


# ---- Raspberry Pi (rotated 180 degrees: HDMI long edge to the back, GPIO to the front, USB end to the left)
def pi_y0():
    return P.PI_PORT_EDGE_Y - P.PI_W


def pi_world(bx, by):
    return (P.PI_X0 + P.PI_L - bx, pi_y0() + P.PI_W - by)


def pi_pcb_top_z():
    return T + P.PI_STANDOFF_H + P.PI_PCB_T


def perf_top_z():
    return T + P.PERF_STANDOFF_H + P.PERF_T


# ---- breakout pads and ULN2003 pins
def breakout_top_z():
    return T + P.BREAKOUT_SIZE[2]


def breakout_pad(k):
    """Pad k (0 based) on the breakout's front edge row, left to right."""
    n = 14
    x0 = P.BREAKOUT_CX - (n - 1) * P.BREAKOUT_PAD_PITCH / 2
    return (x0 + k * P.BREAKOUT_PAD_PITCH, P.BREAKOUT_CY - P.BREAKOUT_SIZE[1] / 2 + 3.0, breakout_top_z())


def uln_in(k):
    """Input pin k (1..7): back row of the DIP. Pin 1 at the left."""
    x = P.PERF_CX - 7 * 2.54 / 2 - 2.54 / 2 + 2.54 * (k - 1) - 0.0
    return (x, P.PERF_CY + 3.81, perf_top_z() + 0.6)


def uln_out(k):
    """Output pin k (1..7): front row, OUT1 opposite IN1."""
    x, y, z = uln_in(k)
    return (x, P.PERF_CY - 3.81, z)

"""--head-reflex: head (gaze) stabilisation, HAND reflex (HAND-MADE, VARSAYIM). SPEC_SENSORY_INPUTS §3.3d.

Acts every physics sub-step, like the haltere reflex; it does not pass through the brain.
Per axis (thorax frame) the head joint target integrates the counter-rotation of the body:
    d theta*/dt = -G * omega_b - theta* / TAU_RC,   |theta*| <= THETA_MAX
yaw additionally makes a reset saccade (theta*_yaw = 0) when |theta*_yaw| >= YAW_RESET.
Position actuators on the three neck joints track theta* (tracking time constant
1 / (KP + passive stiffness) = 5 ms with the FlyGym neck damping 1).

Constants (fixed before any run, never tuned):
  G_YAW 0.6     hand-set; motivated by the fly gaze-stabilisation literature; not traced to a
                specific source
  G_ROLL 0.5    hand-set (VARSAYIM; no value traced to a source); G_PITCH = G_ROLL (VARSAYIM, no
                Drosophila value found). Related literature on head-roll compensation in flies, not the
                source of the value (paper could not be opened): Hengstenberg 1988, J Comp Physiol A 163:151
  THETA_MAX 15  deg; hand-set; motivated by the fly gaze-stabilisation literature; not traced to
                a specific source. Roll and pitch the same (VARSAYIM)
  YAW_RESET 9   deg, yaw reset saccade threshold; hand-set; motivated by the fly
                gaze-stabilisation literature; not traced to a specific source
  Related literature (not the source of G_YAW, THETA_MAX, YAW_RESET): Davis & Mongeau 2023,
  PLoS Comput Biol 19:e1011746, doi:10.1371/journal.pcbi.1011746; Cellini, Salem & Mongeau 2022,
  PNAS 119:e2121660119, doi:10.1073/pnas.2121660119. (Earlier versions of this docstring and
  SPEC_SENSORY_INPUTS §3.3d attributed the three constants to "Cellini, Salem & Mongeau 2022,
  PLoS Comput Biol 18:e1011746"; that citation mixes the two papers.)
  TAU_RC 0.2 s  re-centring leak (VARSAYIM, no literature value found)
  KP 190        -> 1 / (190 + 10) = 5 ms; hand-set latency (VARSAYIM), not taken from a source

FlyGym joint names do not match the physical axes (measured, flight/body.py test):
  joint_Head_roll turns about thorax z (yaw), joint_Head about y (pitch, + = nose down),
  joint_Head_yaw about x (roll, + = right side down).
"""
import numpy as np

AXES = ("yaw", "pitch", "roll")
JOINTS = {"yaw": "joint_Head_roll", "pitch": "joint_Head", "roll": "joint_Head_yaw"}
THORAX_AXIS = {"yaw": 2, "pitch": 1, "roll": 0}          # component of omega_b (thorax x, y, z)

G = np.array([0.6, 0.5, 0.5])                            # yaw, pitch, roll
THETA_MAX = np.radians(15.0)
YAW_RESET = np.radians(9.0)
TAU_RC = 0.2
KP = 190.0
TURN_RATE = 1.0           # rad/s: a sub-step counts as "turning" above this body yaw rate (B-H3)


class HeadReflex:
    def __init__(self):
        self.target = np.zeros(3)            # yaw, pitch, roll (rad)
        self.n_resets = 0

    def update(self, omega_b, dt):
        """omega_b: body angular velocity in thorax axes (x, y, z). Returns the joint targets
        (yaw, pitch, roll) in rad."""
        w = np.array([omega_b[THORAX_AXIS[a]] for a in AXES])
        self.target += dt * (-G * w - self.target / TAU_RC)
        np.clip(self.target, -THETA_MAX, THETA_MAX, out=self.target)
        if abs(self.target[0]) >= YAW_RESET:
            self.target[0] = 0.0
            self.n_resets += 1
        return self.target

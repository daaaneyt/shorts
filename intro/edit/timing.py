"""The intro's event times, shared by render.py and foley.py.

Times are in "internal" seconds: one animation step is 0.1 internal seconds, and
10 steps is a beat's worth of 16ths, so event times are just step numbers / 10.

  v2 timing   the 150 bpm synthesised track: internal seconds are real seconds.
  music mode  a supplied track: step n happens at g0 + n * step (music_sync.json),
              so internal t maps to real time g0 + t * 10 * step.

Music mode retimes three events so the track's accents carry the picture: "In a suit."
lands on the roll's strongest hit (step 3), rip 1 cracks across on steps 5-6 and tears
open on the drop (step 8), and rip 2 cracks on the strong kick at step 30.
"""
import json


def constants(music, hold=None):
    """Event times (internal seconds) and the total hold for a profile."""
    hold = (1.2 if music else 1.6) if hold is None else hold
    c = dict(T_LINE2=0.3 if music else 0.4, T_RIP1=0.5 if music else 0.8, T_RIP2=3.0 if music else 3.2,
             T_EYEBROW=3.6, T_DIGITS=4.0, T_TOBEAT=4.8, T_CRACK=5.1, T_BURST=5.2,
             T_WORD=5.6, T_STRIP1=6.0, T_STRIP2=6.2, T_LABEL=6.4)
    c["HOLD"] = hold
    c["T_OUT"] = round(7.6 + hold, 1)
    c["DUR"] = round(8.0 + hold, 1)
    return c


class Grid:
    """Maps internal time <-> real time for a supplied track."""

    def __init__(self, path):
        d = json.load(open(path))
        self.step, self.g0 = d["step"], d["g0"]

    def real(self, t_internal):
        return self.g0 + t_internal * 10 * self.step

    def duration(self, dur_internal):
        return self.real(dur_internal)

    def internal_step(self, t_real, fps=30):
        """The animation step shown by the frame starting at t_real (nearest-frame rounding)."""
        import math
        return math.floor((t_real + 0.5 / fps - self.g0) / self.step + 1e-6)

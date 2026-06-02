"""PID heading controller with anti-windup and 360° wraparound."""

from dataclasses import dataclass


@dataclass
class PIDController:
    kp: float = 0.8
    ki: float = 0.1
    kd: float = 0.3
    integral: float = 0.0
    last_error: float = 0.0
    max_rudder: float = 15.0
    heading_tol: float = 2.0

    @staticmethod
    def _heading_error(current: float, target: float) -> float:
        return ((target - current + 540.0) % 360.0) - 180.0

    def update(self, current: float, target: float, dt: float) -> tuple[float, float, bool]:
        err = self._heading_error(current, target)

        p = self.kp * err

        self.integral += err * dt
        self.integral = max(-self.max_rudder, min(self.max_rudder, self.integral))
        i = self.ki * self.integral

        d = self.kd * (err - self.last_error) / dt if dt > 0 else 0.0
        self.last_error = err

        cmd = max(-self.max_rudder, min(self.max_rudder, p + i + d))
        on_course = abs(err) < self.heading_tol
        return cmd, err, on_course

    def reset(self):
        self.integral = 0.0
        self.last_error = 0.0


def simulate_heading_hold(
    pid: PIDController | None = None,
    initial: float = 0.0,
    target: float = 90.0,
    dt: float = 0.1,
    max_steps: int = 500,
) -> list[dict]:
    if pid is None:
        pid = PIDController()
    pid.reset()
    heading = initial
    history = []
    for _ in range(max_steps):
        cmd, err, on_course = pid.update(heading, target, dt)
        history.append({"heading": heading, "error": err, "rudder": cmd, "on_course": on_course})
        heading = (heading + cmd * dt) % 360.0
        if on_course:
            break
    return history

from gpiozero import AngularServo
from gpiozero.pins.pigpio import PiGPIOFactory
from time import sleep
import threading
import bisect
from typing import Sequence, List, Optional, Tuple

class Servo:
    def __init__(self, pin):
        self.SERVO_PIN = pin
        self.MIN_DEGREE = -90
        self.MAX_DEGREE = 90
        self.factory = PiGPIOFactory()
        self.servo = AngularServo(self.SERVO_PIN, min_angle=self.MIN_DEGREE, max_angle=self.MAX_DEGREE,
                                  min_pulse_width=500/1000000, max_pulse_width=2500/1000000, frame_width=1/50,
                                  pin_factory=self.factory)
        self.update_dt = 1.0/200
        self.speed = 120
        self._current = 0
        self.target_angle = 0

        self._profile_mode = False
        self._t = []
        self._profile_theta = []
        self._profile_count = 0

        self._lock = threading.Lock()
        self._event = threading.Event()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def close(self):
        self._event.set()
        self._thread.join(timeout=1.0)
        self.servo.close()

    def move(self, angle, speed=120):
        # 指定した角度で指定した時間でサーボを動かす
        with self._lock:
            self.target_angle = angle
            self.speed = speed

    # time(s), angle(0-1)
    def move_with_profile(self, t, angle):
        self._profile_mode = True
        self._profile_theta = self._resample_profile(t, angle, self.update_dt)
        self._profile_count = 0

    def _resample_profile(
        self,
        times: Sequence[float],
        angles: Sequence[float],
        dt: float,
        t_start: Optional[float] = None,
        t_end: Optional[float] = None,
        include_endpoint: bool = True,
        left: str = "hold",  # "hold" | "extrapolate" | "error"
        right: str = "hold",  # "hold" | "extrapolate" | "error"
        clamp: Optional[Tuple[float, float]] = None,  # (min_deg, max_deg)
    ) -> List[float]:
        """
        不等間隔 (times, angles) を線形補間し、dt ごとの角度列のみを返す。

        - times: 秒。厳密な単調増加（重複なし）を仮定
        - angles: 度。len(times) == len(angles) >= 2
        - dt: 出力サンプリング周期 [s]
        - t_start/t_end: 出力範囲（省略時は入力の先頭/末尾）
        - include_endpoint: True なら t_end も含めるよう試みる
        - left/right: 出力範囲が入力の外側にはみ出す場合の扱い
            * "hold": 端の角度で保持
            * "extrapolate": 端の2点で一次外挿
            * "error": はみ出しで ValueError
        - clamp: 角度を (min_deg, max_deg) にクリップ
        """
        if dt <= 0:
            raise ValueError("dt must be > 0")
        if len(times) != len(angles) or len(times) < 2:
            raise ValueError("times/angles must have same length >= 2")
        for i in range(1, len(times)):
            if not (times[i] > times[i - 1]):
                raise ValueError("times must be strictly increasing (no duplicates).")

        t0 = times[0] if t_start is None else t_start
        t1 = times[-1] if t_end is None else t_end
        if t1 < t0:
            raise ValueError("t_end must be >= t_start")

        # 進行方向に合わせて一回だけ idx を初期化（以後は単調に前進）
        j = bisect.bisect_right(times, t0)
        if j <= 0:
            j = 1
        if j >= len(times):
            j = len(times) - 1

        def interp(x: float) -> float:
            # 左側
            if x < times[0]:
                if left == "hold":
                    y = angles[0]
                elif left == "extrapolate":
                    x0, x1 = times[0], times[1]
                    y0, y1 = angles[0], angles[1]
                    m = (y1 - y0) / (x1 - x0)
                    y = y0 + m * (x - x0)
                else:
                    raise ValueError(f"x={x} is left of profile (left='error').")
                return y
            # 右側
            if x > times[-1]:
                if right == "hold":
                    y = angles[-1]
                elif right == "extrapolate":
                    x0, x1 = times[-2], times[-1]
                    y0, y1 = angles[-2], angles[-1]
                    m = (y1 - y0) / (x1 - x0)
                    y = y1 + m * (x - x1)
                else:
                    raise ValueError(f"x={x} is right of profile (right='error').")
                return y

            # 中間（j は単調に増やすだけで良い）
            nonlocal j
            while j < len(times) - 1 and x > times[j]:
                j += 1
            x0, x1 = times[j - 1], times[j]
            y0, y1 = angles[j - 1], angles[j]
            if x1 == x0:
                return y0
            r = (x - x0) / (x1 - x0)
            return y0 + (y1 - y0) * r

        # 角度列を生成（タイムスタンプは返さない）
        out: List[float] = []
        t = t0
        eps = dt * 1e-9

        def cont(u: float) -> bool:
            return (u <= t1 + eps) if include_endpoint else (u < t1 - eps)

        while cont(t):
            val = interp(t)
            if clamp is not None:
                mn, mx = clamp
                if val < mn:
                    val = mn
                if val > mx:
                    val = mx
            out.append(val)
            t += dt

        # 範囲が極短の場合でも1点は返す（t_startのみ）
        if not out:
            val = interp(t0)
            if clamp is not None:
                mn, mx = clamp
                if val < mn:
                    val = mn
                if val > mx:
                    val = mx
            out = [val]

        return out
        

    def _loop(self):
        while not self._event.is_set():
            with self._lock:
                if self._profile_mode:
                    if len(self._profile_theta)-1 <= self._profile_count:
                        self.profile_count = 0
                        self._profile_mode = False
                    self.target_angle = self._profile_theta[self._profile_count]
                    self._profile_count += 1
                diff = self.target_angle - self._current
                delta = self.speed * self.update_dt * (1 if 0<=diff else -1)
                previous = self.servo.angle
                if 1  <= abs(diff):
                    if abs(self._current + delta) <= 90.0:
                        self.servo.angle = self._current + delta
                    if previous != self.servo.angle:
                        self._current = self.servo.angle
                    else:
                        self._current += delta
            self._event.wait(self.update_dt)

def main():
    rotate = Servo(12)
    vertical = Servo(13)
    speed = 15
    try:
        vertical.move_with_profile([0, 2, 4, 6], [90, -75, 90, -75])
        sleep(7)
        rotate.move_with_profile([0, 2, 4, 6], [90, -90, 90, -90])
        sleep(7)
        vertical.move_with_profile([0, 2, 4, 6], [90, -75, 90, -75])
        rotate.move_with_profile([0, 2, 4, 6], [90, -90, 90, -90])
        sleep(7)
        #for _ in range(3):
        #    rotate.move_with_profile([1, 1.1, 1.2, 1.3, 2], [0, 90, 0, 90, -80])
        #    sleep(4)
    except KeyboardInterrupt:
        print("stop")
    finally:
        rotate.close()
        vertical.close()
    return


if __name__ == "__main__":
        main()

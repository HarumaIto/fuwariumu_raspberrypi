from gpiozero import AngularServo
from gpiozero.pins.pigpio import PiGPIOFactory
from time import sleep
import threading

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
        self._lock = threading.Lock()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._event = threading.Event()
        self._thread.start()

    def __del__(self):
        self._event.set()
        self._thread.join(timeout=1.0)

    def move(self, angle, speed=120):
        # 指定した角度で指定した時間でサーボを動かす
        with self._lock:
            self.target_angle = angle
            self.speed = speed

    def _loop(self):
        while not self._event.is_set():
            with self._lock:
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
    speed = 30
    try:
        rotate.move(-75, speed)
        vertical.move(-75, speed)
        sleep(2)

        for _ in range(5):
            print(90)
            rotate.move(90, speed)
            vertical.move(90, speed)
            sleep(2)
            print(0)
            rotate.move(0, speed)
            vertical.move(-75, speed)
            sleep(2)
    except KeyboardInterrupt:
        print("stop")
    return


if __name__ == "__main__":
        main()

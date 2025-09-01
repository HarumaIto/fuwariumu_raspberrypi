from gpiozero import AngularServo
from gpiozero.pins.pigpio import PiGPIOFactory
from time import sleep


class Servo:
    def __init__(self, pin):
        self.SERVO_PIN = pin
        self.MIN_DEGREE = -90
        self.MAX_DEGREE = 90
        self.factory = PiGPIOFactory()
        self.servo = AngularServo(self.SERVO_PIN, min_angle=self.MIN_DEGREE, max_angle=self.MAX_DEGREE,
                                  min_pulse_width=500/1000000, max_pulse_width=2500/1000000, frame_width=1/50,
                                  pin_factory=self.factory)

    def set_angle(self, angle):
        self.servo.angle = angle


def main():
    servo_12 = Servo(12)
    servo_13 = Servo(13)
    try:
        for _ in range(5):
            servo_12.set_angle(60)
            servo_13.set_angle(60)
            print("60")
            sleep(1)
            servo_12.set_angle(-60)
            servo_13.set_angle(-60)
            print("-60")
            sleep(1)
    except KeyboardInterrupt:
        print("stop")
    return


if __name__ == "__main__":
    main()
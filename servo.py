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

def move_servo_at_speed(servo, start_angle, end_angle, duration_sec, steps=100):
	"""
	指定した角度で指定した時間でサーボを動かす
	"""
	angle_diff = end_angle - start_angle
	angle_per_step = angle_diff / steps
	delay_per_step = duration_serc / steps

	for i in range(steps + 1):
		current_angle = start_angle + angle_per_step * i
		servo.angle = current_angle
		sleep(delay_per_step)

def main():
	servo_12 = Servo(12)
	servo_13 = Servo(13)
	try:
		servo_12.set_angle(-90)
		servo_13.set_angle(-90)

		for _ in range(5):
	    		move_servo_at_speed(servo_12, -90, 75, 2)
           		move_servo_at_speed(servo_13, -90, 75, 2) 
            		sleep(1)
			move_servo_at_speed(servo_12, 75, -90, 3)
			move_servo_at_speed(servo_13, 75, -90, 3)
            		sleep(1)
    	except KeyboardInterrupt:
       		 print("stop")
    	return


if __name__ == "__main__":
    	main()

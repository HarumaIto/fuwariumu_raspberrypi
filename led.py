from gpiozero import RGBLED
from gpiozero.pins.pigpio import PiGPIOFactory
from time import sleep

PIN_RED=5
PIN_GREEN=6
PIN_BLUE=13 

def hsv_to_rgb(h, s, v):
	if s == 0.0: return (v, v, v)
	i = int(h*6)
	f = (h*6) - i
	p, q, t = v*(1-s), v*(1-s*f), v*(1-s*(1-f))
	i %= 6
	if i == 0: return (v, t, p)
	if i == 1: return (q, v, p)
	if i == 2: return (p, v, t)
	if i == 3: return (p, q, v)
	if i == 4: return (t, p, v)
	if i == 5: return (v, p, q)

def main():
	factory=PiGPIOFactory()
	led = RGBLED(PIN_RED, PIN_GREEN, PIN_BLUE, pin_factory=factory) 

	print("Cycling through basic colors...")
    
	# 基本色を順番に点灯
	print("Red")
	led.color = (1, 0, 0) # (R, G, B)のタプルで色を設定 (0.0 - 1.0)

	print("Green")
	led.color = (0, 1, 0)
	sleep(1)

	print("Blue")
	led.color = (0, 0, 1)
	sleep(1)

	print("Yellow")
	led.color = (1, 1, 0)
	sleep(1)

	print("Cyan")
	led.color = (0, 1, 1)
	sleep(1)

	print("Magenta")
	led.color = (1, 0, 1)
	sleep(1)

	print("White")
	led.color = (1, 1, 1)
	sleep(1)

	print("Off")
	led.color = (0, 0, 0) # 全てオフで消灯
	sleep(1)

	# グラデーションを表現
	print("Fading through the rainbow...")
	steps = 100
	for i in range(steps + 1):
		hue = i / steps

		r, g, b = hsv_to_rgb(hue, 1.0, 1.0)

		led.color = (r, g, b)
		sleep(0.05)

	led.off()
	print("Program finished.")
if __name__=="__main__":
	main()	








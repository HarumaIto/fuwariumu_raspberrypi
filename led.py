from gpiozero import RGBLED
from gpiozero.pins.pigpio import PiGPIOFactory
from time import sleep
from colorsys import rgb_to_hsv
import logging

# loggingの設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

PIN_RED=17
PIN_GREEN=27
PIN_BLUE=22

def init_led():
    try:
        factory=PiGPIOFactory()
        led = RGBLED(PIN_RED, PIN_GREEN, PIN_BLUE, pin_factory=factory)
        led.color = (1, 1, 1)
        sleep(1)
        led.off()
        return led
    except Exception as e:
        logging.error(f"LEDの初期化に失敗しました: {e}")
        return None

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

def fade_out(led, duration, steps=100):
    step_size = 1.0 / steps
    delay_per_step = duration / steps

    for i in range(steps):
        brightness = 1.0 - (i * step_size)

        r, g, b = led.color
        h, s, _ = rgb_to_hsv(r, g, b)
        led.color = hsv_to_rgb(h, s, brightness)

        sleep(delay_per_step)
    
    led.off()

def main():
    led = init_led()
    if led is None:
        logging.error("LEDが初期化されていないため、プログラムを終了します。")
        return

    try:
        print("Cycling through basic colors...")
        
        # 基本色を順番に点灯
        print("Red")
        led.color = (1, 0, 0) # (R, G, B)のタプルで色を設定 (0.0 - 1.0)
        sleep(1)

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

    except Exception as e:
        logging.error(f"LEDの制御中にエラーが発生しました: {e}")
    finally:
        if led:
            led.off()
        print("Program finished.")

if __name__=="__main__":
    main()

from microbit import *
import music
import neopixel

uart.init(baudrate=115200)
rgb = neopixel.NeoPixel(pin13, 1)

last_a = False
last_b = False
last_p1 = 0
severity = 0
last_report = running_time()


def set_outputs(sev):
    sev = max(0, min(100, int(sev)))

    if sev < 40:
        rgb[0] = (0, 70, 0)
        pin14.write_digital(0)  # red traffic light
        pin15.write_digital(0)  # yellow traffic light
        pin16.write_digital(1)  # green traffic light
        display.show(Image.YES)
    elif sev < 70:
        rgb[0] = (80, 55, 0)
        pin14.write_digital(0)
        pin15.write_digital(1)
        pin16.write_digital(0)
        display.show(Image.SQUARE_SMALL)
    else:
        rgb[0] = (90, 0, 0)
        pin14.write_digital(1)
        pin15.write_digital(0)
        pin16.write_digital(0)
        display.show(Image.NO)

    rgb.show()


def play_sound(name):
    name = name.upper()

    if name in ("DANGER", "HIGH"):
        music.pitch(880, 120)
        sleep(70)
        music.pitch(988, 180)
    elif name in ("MODERATE", "MID"):
        music.pitch(659, 160)
    else:
        music.pitch(440, 90)


def handle_command(line):
    global severity
    line = line.strip().upper()

    if line.startswith("SEV:"):
        severity = int(line.split(":", 1)[1])
        set_outputs(severity)
    elif line.startswith("WARN:1"):
        play_sound("DANGER")
    elif line.startswith("SOUND:"):
        play_sound(line.split(":", 1)[1])


set_outputs(0)

while True:
    now = running_time()
    pot = pin0.read_analog()
    mic = pin2.read_analog()
    p1 = pin1.read_digital()
    ir8 = pin8.read_digital()
    ir12 = pin12.read_digital()

    if now - last_report > 120:
        print("POT:%d MIC:%d P1:%d IR8:%d IR12:%d" % (pot, mic, p1, ir8, ir12))
        last_report = now

    if button_a.is_pressed() and not last_a:
        print("A")

    if button_b.is_pressed() and not last_b:
        print("B")

    if p1 == 1 and last_p1 == 0:
        print("P1:1")

    last_a = button_a.is_pressed()
    last_b = button_b.is_pressed()
    last_p1 = p1

    if uart.any():
        incoming = uart.readline()
        if incoming:
            handle_command(incoming.decode().strip())

    sleep(30)

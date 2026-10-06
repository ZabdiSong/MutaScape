from microbit import *
import music

try:
    import neopixel
    rgb = neopixel.NeoPixel(pin13, 1)
except Exception:
    rgb = None

uart.init(baudrate=115200)

# Wiring used by this version:
# P0 = knob analog
# P1 = button bit, Button A: WT / Mutant
# P2 = sound bit analog, environmental stress
# P3 = optional extra button, also accepted as Button A fallback
# P8/P12 = IR bit, Button B: mutation hypothesis
# P13 = RGB bit / NeoPixel signal
# P14/P15/P16 = traffic light bit: red/yellow/green

last_send = running_time()
last_a = False
last_b = False
buffer = ""
severity = 0


def clamp(value, low, high):
    return max(low, min(high, value))


def set_rgb(r, g, b):
    if rgb:
        try:
            rgb[0] = (r, g, b)
            rgb.show()
        except Exception:
            pass


def set_traffic(value):
    value = clamp(int(value), 0, 100)
    pin14.write_digital(0)
    pin15.write_digital(0)
    pin16.write_digital(0)

    if value >= 70:
        pin14.write_digital(1)
        set_rgb(50, 0, 0)
    elif value >= 40:
        pin15.write_digital(1)
        set_rgb(40, 25, 0)
    else:
        pin16.write_digital(1)
        set_rgb(0, 40, 0)


def show_severity(value):
    value = clamp(int(value), 0, 100)
    lit = int(value / 100 * 25)
    display.clear()

    for i in range(lit):
        x = i % 5
        y = 4 - int(i / 5)
        display.set_pixel(x, y, 9)

    set_traffic(value)


def beep(kind):
    try:
        if kind in ["danger", "high"]:
            music.pitch(988, 120)
            sleep(40)
            music.pitch(988, 120)
        elif kind in ["moderate", "mid"]:
            music.pitch(659, 120)
        elif kind in ["stable", "low"]:
            music.pitch(440, 80)
    except Exception:
        pass


def handle_line(line):
    global severity
    line = line.strip()

    if not line:
        return

    if line.startswith("SEV:"):
        try:
            severity = int(line.split(":", 1)[1])
            show_severity(severity)
        except Exception:
            pass

    elif line.startswith("WARN:"):
        if line.endswith("1"):
            beep("danger")

    elif line.startswith("MODE:"):
        mode = line.split(":", 1)[1]
        if mode.startswith("Structure"):
            display.show("S")
        elif mode.startswith("DNA"):
            display.show("D")
        elif mode.startswith("Network"):
            display.show("N")

    elif line.startswith("MUT:"):
        display.scroll(line.split(":", 1)[1], wait=False)

    elif line.startswith("VIEW:"):
        view = line.split(":", 1)[1]
        display.show("W" if view.startswith("WT") else "M")

    elif line in ["danger", "high", "moderate", "mid", "stable", "low"]:
        beep(line)


def read_serial():
    global buffer

    if uart.any():
        data = uart.read()
        if data:
            buffer += data.decode("utf-8")

    while "\n" in buffer:
        line, buffer = buffer.split("\n", 1)
        handle_line(line)


def active_pin(digital_value, analog_value):
    # Accept both active-high and active-low button modules.
    return digital_value == 1 or analog_value < 150


set_traffic(0)
display.show(Image.YES)
sleep(300)
display.clear()

while True:
    read_serial()

    now = running_time()

    p0 = pin0.read_analog()
    p1a = pin1.read_analog()
    p1d = pin1.read_digital()
    p2 = pin2.read_analog()
    p3a = pin3.read_analog()
    p3d = pin3.read_digital()
    p8d = pin8.read_digital()
    p12d = pin12.read_digital()

    current_a = active_pin(p1d, p1a) or active_pin(p3d, p3a)
    current_b = p8d == 1 or p12d == 1

    if current_a and not last_a:
        uart.write("A\n")
        display.show("A")

    if current_b and not last_b:
        uart.write("B\n")
        display.show("B")

    last_a = current_a
    last_b = current_b

    if now - last_send > 250:
        # Main control message used by the website.
        uart.write("POT:{} MIC:{}\n".format(p0, p2))

        # Debug message: check this in the website's Last micro:bit message text.
        uart.write("DBG:P0={} P1A={} P1D={} P2={} P3A={} P3D={} P8={} P12={}\n".format(
            p0, p1a, p1d, p2, p3a, p3d, p8d, p12d
        ))
        last_send = now

    sleep(20)

# MutaScape micro:bit MakeCode Python version
# Wiring:
# P0 = knob
# P1 = ButtonBit input, but your readings show it may not distinguish A/B reliably
# P2 = sound bit, environmental stress
# P8/P12 = IR sensor pair
# P14/P15/P16 = traffic light red/yellow/green
# BTA/BTB = speaker connector; MakeCode can mainly control built-in speaker

last_send = 0
a_latch_until = 0
b_latch_until = 0
ir_latch_until = 0
last_builtin_a = False
last_builtin_b = False
last_ir = False
last_p1_pressed = False

# Your traffic light startup test worked with active-low.
TRAFFIC_ACTIVE_LOW = True


def clamp(value, low, high):
    if value < low:
        return low
    if value > high:
        return high
    return value


def traffic_write(pin, on):
    if TRAFFIC_ACTIVE_LOW:
        pins.digital_write_pin(pin, 0 if on else 1)
    else:
        pins.digital_write_pin(pin, 1 if on else 0)


def all_traffic_off():
    traffic_write(DigitalPin.P14, False)
    traffic_write(DigitalPin.P15, False)
    traffic_write(DigitalPin.P16, False)


def set_traffic(severity):
    severity = clamp(severity, 0, 100)
    all_traffic_off()
    basic.pause(5)

    if severity >= 70:
        traffic_write(DigitalPin.P14, True)   # red
    elif severity >= 40:
        traffic_write(DigitalPin.P15, True)   # yellow
    else:
        traffic_write(DigitalPin.P16, True)   # green


def show_severity(severity):
    severity = clamp(severity, 0, 100)
    lit = int(severity * 25 / 100)
    basic.clear_screen()

    for i in range(lit):
        x = i % 5
        y = 4 - int(i / 5)
        led.plot_brightness(x, y, 255)

    set_traffic(severity)


def beep(kind):
    music.set_built_in_speaker_enabled(True)

    if kind == "danger" or kind == "high":
        music.play_tone(988, music.beat(BeatFraction.EIGHTH))
        basic.pause(40)
        music.play_tone(988, music.beat(BeatFraction.EIGHTH))
    elif kind == "moderate" or kind == "mid":
        music.play_tone(659, music.beat(BeatFraction.EIGHTH))
    elif kind == "stable" or kind == "low":
        music.play_tone(440, music.beat(BeatFraction.SIXTEENTH))


def handle_line(line):
    if line.substr(0, 4) == "SEV:":
        sev_text = line.substr(4, line.length - 4)
        severity = parse_float(sev_text)
        show_severity(severity)

    elif line.substr(0, 5) == "WARN:":
        if line.substr(5, 1) == "1":
            beep("danger")

    elif line == "danger" or line == "high":
        beep("danger")
    elif line == "moderate" or line == "mid":
        beep("moderate")
    elif line == "stable" or line == "low":
        beep("stable")


def on_serial_received():
    line = serial.read_line()
    handle_line(line)


serial.on_data_received(serial.delimiters(Delimiters.NEW_LINE), on_serial_received)


def p1_pressed(p1a, p1d):
    # Your P1A sits near 126 all the time, so treat it as an optional single button only.
    # If it never changes, it will not drive controls.
    return p1d == 1 or p1a < 80


def ir_triggered(p8d, p12d):
    return p8d == 1 or p12d == 1


# Startup traffic test: green -> yellow -> red -> off -> green.
basic.show_icon(IconNames.YES)
set_traffic(20)
basic.pause(300)
set_traffic(55)
basic.pause(300)
set_traffic(90)
basic.pause(300)
all_traffic_off()
basic.pause(200)
set_traffic(20)
basic.pause(300)
basic.clear_screen()


def on_forever():
    global last_send, a_latch_until, b_latch_until, ir_latch_until
    global last_builtin_a, last_builtin_b, last_ir, last_p1_pressed

    now = input.running_time()

    p0 = pins.analog_read_pin(AnalogPin.P0)
    p1a = pins.analog_read_pin(AnalogPin.P1)
    p1d = pins.digital_read_pin(DigitalPin.P1)
    p2 = pins.analog_read_pin(AnalogPin.P2)
    p8d = pins.digital_read_pin(DigitalPin.P8)
    p12d = pins.digital_read_pin(DigitalPin.P12)

    builtin_a = input.button_is_pressed(Button.A)
    builtin_b = input.button_is_pressed(Button.B)
    p1_now = p1_pressed(p1a, p1d)
    ir_now = ir_triggered(p8d, p12d)

    # Built-in micro:bit A/B are the reliable controls.
    if builtin_a and not last_builtin_a:
        a_latch_until = now + 2000
        serial.write_line("A")
        basic.show_string("A")

    if builtin_b and not last_builtin_b:
        b_latch_until = now + 2000
        serial.write_line("B")
        basic.show_string("B")

    # P1 external ButtonBit fallback: single-button action only, mapped to A.
    if p1_now and not last_p1_pressed:
        a_latch_until = now + 2000
        serial.write_line("A")
        basic.show_string("A")

    # IR also maps to B.
    if ir_now and not last_ir:
        ir_latch_until = now + 2000
        b_latch_until = now + 2000
        serial.write_line("B")
        basic.show_string("I")

    last_builtin_a = builtin_a
    last_builtin_b = builtin_b
    last_p1_pressed = p1_now
    last_ir = ir_now

    if now - last_send > 250:
        serial.write_line("POT:" + str(p0) + " MIC:" + str(p2))

        # Latched messages survive until you click Read micro:bit data.
        if now < a_latch_until:
            serial.write_line("A")
        if now < b_latch_until:
            serial.write_line("B")

        serial.write_line("DBG:P0=" + str(p0) + " P1A=" + str(p1a) + " P1D=" + str(p1d) + " P2=" + str(p2) + " P8=" + str(p8d) + " P12=" + str(p12d) + " BA=" + str(1 if builtin_a else 0) + " BB=" + str(1 if builtin_b else 0) + " AL=" + str(1 if now < a_latch_until else 0) + " BL=" + str(1 if now < b_latch_until else 0))
        last_send = now

    basic.pause(20)


basic.forever(on_forever)

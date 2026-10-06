import streamlit as st
import pandas as pd
from streamlit_agraph import agraph, Node, Edge, Config

import py3Dmol
import streamlit.components.v1 as components
from stmol import showmol

import matplotlib.pyplot as plt
import numpy as np

import serial
import time
import re
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
ASSET_DIR = BASE_DIR / "assets"


# ---------------------------------
# PAGE CONFIG
# ---------------------------------
st.set_page_config(
    page_title="MutaScape",
    page_icon="M",
    layout="wide"
)

# ---------------------------------
# CUSTOM CSS (SCI-FI UI)
# ---------------------------------
st.markdown("""
<style>

.stApp {
    background: linear-gradient(135deg,#050816,#0b1020,#111827);
    color: white;
}

.glass {
    background: rgba(255,255,255,0.06);
    border: 1px solid rgba(255,255,255,0.12);
    border-radius: 22px;
    padding: 20px;
    backdrop-filter: blur(18px);
}

.title {
    text-align:center;
    font-size:52px;
    font-weight:700;
    color:#6ee7ff;
}

.subtitle {
    text-align:center;
    color:#b6c2d9;
    margin-bottom:30px;
}

.badge {
    position:fixed;
    bottom:20px;
    left:20px;
    background: rgba(0,0,0,0.6);
    border:1px solid #00f7ff;
    border-radius:15px;
    padding:14px;
    z-index:999;
}

.stepbar {
    text-align:center;
    font-size:20px;
    margin-bottom:20px;
}

.rmsd-low {
    color:#00ffb7;
    font-weight:bold;
}

.rmsd-mid {
    color:#ffd000;
    font-weight:bold;
}

.rmsd-high {
    color:#ff5f5f;
    font-weight:bold;
}

.console-panel {
    background: #020617;
    border: 1px solid rgba(103,232,249,0.45);
    border-left: 4px solid #67e8f9;
    border-radius: 8px;
    color: #dbeafe;
    font-family: Consolas, monospace;
    padding: 14px 16px;
    box-shadow: 0 0 24px rgba(34,211,238,0.12);
}

.console-panel b {
    color: #67e8f9;
}

</style>
""", unsafe_allow_html=True)

# ---------------------------------
# MICROBIT SERIAL
# ---------------------------------
if "ser" not in st.session_state:
    st.session_state.ser = None

with st.sidebar.expander("micro:bit", expanded=False):
    port = st.text_input("Port", value="COM5")

    if st.button("Connect micro:bit"):
        try:
            st.session_state.ser = serial.Serial(
                port,
                115200,
                timeout=0.1
            )
            st.success(f"Connected to {port}")
        except Exception as e:
            st.session_state.ser = None
            st.error(f"Could not connect: {e}")

    if st.session_state.ser:
        st.success("micro:bit is connected")
    else:
        st.caption("Leave this disconnected while testing the protein viewer.")

    st.checkbox("Live hardware sensing", value=False, key="live_microbit_enabled")

ser = st.session_state.ser

def send_microbit_command(command, pause=0.04):
    st.session_state.last_microbit_command = command
    active_ser = st.session_state.get("ser")
    if active_ser:
        try:
            active_ser.write((command + "\n").encode())
            active_ser.flush()
            if pause:
                time.sleep(pause)
            st.session_state.microbit_error = ""
        except Exception as e:
            st.session_state.microbit_error = str(e)
    else:
        st.session_state.microbit_error = "micro:bit is not connected"

def send_microbit_commands(commands, pause=0.08):
    for command in commands:
        send_microbit_command(command, pause=pause)

def send_sound(command, force=False):
    now = time.time()
    key = f"sound_{command}"

    if not force and now - st.session_state.get(key, 0.0) < 1.0:
        return

    st.session_state[key] = now
    st.session_state.raw_sound = command.upper()
    send_microbit_command(f"SOUND:{command.upper()}")


def send_motor_for_variant():
    angle = 180 if st.session_state.get("variant_view", "WT") == "Mutant" else 0
    st.session_state.raw_servo = angle
    send_microbit_commands([f"SERVO:{angle}", f"SERVO:{angle}"], pause=0.06)


def send_rgb_for_severity(severity):
    if severity >= 70:
        st.session_state.raw_rgb = "100,0,0"
        send_microbit_command("RGB:100,0,0", pause=0.06)
    elif severity >= 40:
        st.session_state.raw_rgb = "80,55,0"
        send_microbit_command("RGB:80,55,0", pause=0.06)
    else:
        st.session_state.raw_rgb = "0,80,0"
        send_microbit_command("RGB:0,80,0", pause=0.06)


def send_traffic_for_severity(severity):
    if severity >= 70:
        st.session_state.raw_traffic = "RED"
        commands = [f"SEV:{severity}", "TL:RED"]
    elif severity >= 40:
        st.session_state.raw_traffic = "YELLOW"
        commands = [f"SEV:{severity}", "TL:YELLOW"]
    else:
        st.session_state.raw_traffic = "GREEN"
        commands = [f"SEV:{severity}", "TL:GREEN"]

    send_microbit_commands(commands, pause=0.08)
    send_rgb_for_severity(severity)

# ---------------------------------
# SESSION STATE
# ---------------------------------
if "step" not in st.session_state:
    st.session_state.step = 0

if "mutation" not in st.session_state:
    st.session_state.mutation = "S169P"

PREDICTOR_MODES = ["Structure", "DNA", "Network"]
MUTATION_HYPOTHESES = ["S169A", "S169G", "S169P"]

if st.session_state.mutation not in MUTATION_HYPOTHESES:
    st.session_state.mutation = "S169P"

if "mutation_index" not in st.session_state:
    st.session_state.mutation_index = MUTATION_HYPOTHESES.index(st.session_state.mutation)

if "predictor_mode" not in st.session_state:
    st.session_state.predictor_mode = PREDICTOR_MODES[max(0, st.session_state.step - 1)] if st.session_state.step else "Structure"

if "variant_view" not in st.session_state:
    st.session_state.variant_view = "WT"

if "env_stress" not in st.session_state:
    st.session_state.env_stress = 0

if "pot" not in st.session_state:
    st.session_state.pot = 0

if "last_button_time" not in st.session_state:
    st.session_state.last_button_time = {"A": 0.0, "B": 0.0}

if "last_microbit_raw" not in st.session_state:
    st.session_state.last_microbit_raw = ""

if "microbit_error" not in st.session_state:
    st.session_state.microbit_error = ""

if "raw_p1" not in st.session_state:
    st.session_state.raw_p1 = 0

if "raw_p1a" not in st.session_state:
    st.session_state.raw_p1a = 0

if "raw_p1e" not in st.session_state:
    st.session_state.raw_p1e = "NONE"

if "last_event_seq" not in st.session_state:
    st.session_state.last_event_seq = -1

if "raw_seq" not in st.session_state:
    st.session_state.raw_seq = 0

if "raw_p2" not in st.session_state:
    st.session_state.raw_p2 = 0

if "last_microbit_command" not in st.session_state:
    st.session_state.last_microbit_command = ""

if "raw_ir8" not in st.session_state:
    st.session_state.raw_ir8 = 0

if "raw_ir12" not in st.session_state:
    st.session_state.raw_ir12 = 0

if "raw_music" not in st.session_state:
    st.session_state.raw_music = 0

if "raw_sound" not in st.session_state:
    st.session_state.raw_sound = "NONE"

if "raw_servo" not in st.session_state:
    st.session_state.raw_servo = 0

if "raw_rgb" not in st.session_state:
    st.session_state.raw_rgb = "0,80,0"

if "raw_traffic" not in st.session_state:
    st.session_state.raw_traffic = "GREEN"

if "p1_button_down" not in st.session_state:
    st.session_state.p1_button_down = False

if "prediction_run_count" not in st.session_state:
    st.session_state.prediction_run_count = 0

if "prediction_run_status" not in st.session_state:
    st.session_state.prediction_run_status = "Waiting for START"

# ---------------------------------
# AMINO ACID DATA
# ---------------------------------
aa_data = {

    "S": {
        "name":"Serine",
        "polarity":"Polar",
        "hydrogen":"Yes",
        "flexibility":"Medium",
        "phosphorylation":"Yes"
    },

    "P": {
        "name":"Proline",
        "polarity":"Nonpolar",
        "hydrogen":"No",
        "flexibility":"Low",
        "phosphorylation":"No"
    },

    "A": {
        "name":"Alanine",
        "polarity":"Nonpolar",
        "hydrogen":"No",
        "flexibility":"Medium",
        "phosphorylation":"No"
    },

    "F": {
        "name":"Phenylalanine",
        "polarity":"Nonpolar",
        "hydrogen":"No",
        "flexibility":"Low",
        "phosphorylation":"No"
    },

    "G": {
        "name":"Glycine",
        "polarity":"Nonpolar",
        "hydrogen":"No",
        "flexibility":"High",
        "phosphorylation":"No"
    },

    "Y": {
        "name":"Tyrosine",
        "polarity":"Polar",
        "hydrogen":"Yes",
        "flexibility":"Low",
        "phosphorylation":"Yes"
    },

    "W": {
        "name":"Tryptophan",
        "polarity":"Nonpolar",
        "hydrogen":"Yes",
        "flexibility":"Low",
        "phosphorylation":"No"
    },

    "R": {
        "name":"Arginine",
        "polarity":"Polar",
        "hydrogen":"Yes",
        "flexibility":"Medium",
        "phosphorylation":"No"
    }
}

def predict_functional_effect(mt):

    structure_score = 0
    dna_score = 0
    interaction_score = 0

    explanation = []

    # -------------------
    # rigidity
    # -------------------
    if mt == "P":

        structure_score += 30
        interaction_score += 15

        explanation.append(
            "Proline introduces structural rigidity."
        )

    # -------------------
    # polarity shift
    # -------------------
    if aa_data["S"]["polarity"] != aa_data[mt]["polarity"]:

        structure_score += 15
        dna_score += 10
        interaction_score += 15

        explanation.append(
            "Polarity changed."
        )

    # -------------------
    # hydrogen bond loss
    # -------------------
    if aa_data["S"]["hydrogen"] == "Yes" and \
       aa_data[mt]["hydrogen"] == "No":

        structure_score += 20
        dna_score += 15
        interaction_score += 20

        explanation.append(
            "Hydrogen bonding potential lost."
        )

    # -------------------
    # phosphorylation loss
    # -------------------
    if aa_data["S"]["phosphorylation"] == "Yes" and \
       aa_data[mt]["phosphorylation"] == "No":

        interaction_score += 20

        explanation.append(
            "Phosphorylation site removed."
        )

    # normalize to 100
    structure_score = min(structure_score,100)
    dna_score = min(dna_score,100)
    interaction_score = min(interaction_score,100)

    return (
        structure_score,
        dna_score,
        interaction_score,
        explanation
    )

def get_mutant_code():
    return st.session_state.mutation[-1]

def get_mutant_path():
    if st.session_state.mutation == "S169P":
        return ASSET_DIR / "foxa2_s169p.cif"
    return ASSET_DIR / "foxa2_wt.cif"

def debounce_button(button_name, interval=0.35):
    now = time.time()
    last = st.session_state.last_button_time.get(button_name, 0.0)

    if now - last < interval:
        return False

    st.session_state.last_button_time[button_name] = now
    return True

def set_predictor_from_pot(value):
    value = max(0, min(1023, int(value)))
    mode_index = min(2, int(value / 1024 * len(PREDICTOR_MODES)))

    st.session_state.pot = value
    st.session_state.predictor_mode = PREDICTOR_MODES[mode_index]

def cycle_mutation_hypothesis():
    st.session_state.mutation_index = (st.session_state.mutation_index + 1) % len(MUTATION_HYPOTHESES)
    st.session_state.mutation = MUTATION_HYPOTHESES[st.session_state.mutation_index]
    send_microbit_command(f"MUT:{st.session_state.mutation}")
    send_traffic_for_severity(current_disruption_severity())

def toggle_variant_view():
    st.session_state.variant_view = "Mutant" if st.session_state.variant_view == "WT" else "WT"
    send_motor_for_variant()
    send_microbit_command(f"VIEW:{st.session_state.variant_view}")
    send_traffic_for_severity(current_disruption_severity())

def normalize_microbit_value(value):
    value = max(0, min(1023, int(value)))
    return int(value / 1023 * 100)

def apply_microbit_line(raw):
    raw = raw.strip()

    if not raw:
        return

    st.session_state.last_microbit_raw = raw
    upper = raw.upper()

    if upper.isdigit():
        set_predictor_from_pot(int(upper))
        return

    if upper.startswith("DBG:"):
        upper = upper.replace("DBG:", "", 1)

    if upper in ["A", "BTN_A", "BUTTON_A"]:
        st.session_state.raw_p1e = "A"
        if debounce_button("A"):
            toggle_variant_view()
        return

    if upper in ["B", "BTN_B", "BUTTON_B"]:
        st.session_state.raw_p1e = "B"
        if debounce_button("B"):
            cycle_mutation_hypothesis()
        return

    pairs = re.findall(r"([A-Z][A-Z0-9_]*):(\d+|[A-Z]+)", upper)
    values = {key: value for key, value in pairs}
    event_seq = int(values["SEQ"]) if values.get("SEQ", "").isdigit() else None

    for key, value in pairs:
        if key == "SEQ" and value.isdigit():
            st.session_state.raw_seq = int(value)
        elif key in ["POT", "KNOB", "ROT", "ROTARY", "P0"] and value.isdigit():
            set_predictor_from_pot(int(value))
        elif key in ["MIC", "SOUND", "STRESS", "P2"] and value.isdigit():
            st.session_state.raw_p2 = int(value)
            st.session_state.env_stress = normalize_microbit_value(value)
        elif key in ["IR1", "P1"] and value.isdigit():
            st.session_state.raw_p1 = int(value)
        elif key == "CONTACT" and value.isdigit():
            st.session_state.raw_p1 = int(value)
        elif key in ["IR1A", "P1A"] and value.isdigit():
            st.session_state.raw_p1a = int(value)
        elif key in ["MUSIC8", "P8"] and value.isdigit():
            st.session_state.raw_ir8 = int(value)
        elif key in ["MUSIC12", "P12"] and value.isdigit():
            st.session_state.raw_ir12 = int(value)
        elif key == "MUSIC" and value.isdigit():
            st.session_state.raw_music = int(value)
        elif key == "SOUND":
            st.session_state.raw_sound = value
        elif key == "SERVO" and value.isdigit():
            st.session_state.raw_servo = int(value)
        elif key == "SERVOSET" and value.isdigit():
            st.session_state.raw_servo = int(value)
        elif key == "SERVOSCAN":
            st.session_state.raw_servo = f"scan {value}"
        elif key in ["TL", "TRAFFIC"]:
            st.session_state.raw_traffic = value
        elif key in ["RGBR", "RGBG", "RGBB"] and value.isdigit():
            rgb = st.session_state.raw_rgb.split(",")
            while len(rgb) < 3:
                rgb.append("0")
            index = {"RGBR": 0, "RGBG": 1, "RGBB": 2}[key]
            rgb[index] = value
            st.session_state.raw_rgb = ",".join(rgb[:3])
        elif key in ["EVT", "P1E", "BTN"]:
            st.session_state.raw_p1e = value
            is_new_event = event_seq is None or event_seq != st.session_state.last_event_seq
            if value in ["A", "B"] and is_new_event:
                st.session_state.last_event_seq = event_seq if event_seq is not None else st.session_state.last_event_seq
                if value == "A" and debounce_button("A"):
                    toggle_variant_view()
                elif value == "B" and debounce_button("B"):
                    cycle_mutation_hypothesis()
        elif key in ["A", "BTN_A", "BUTTON_A"] and value in ["1", "DOWN", "PRESS"]:
            st.session_state.raw_p1e = "A"
            if debounce_button("A"):
                toggle_variant_view()
        elif key in ["B", "BTN_B", "BUTTON_B"] and value in ["1", "DOWN", "PRESS"]:
            st.session_state.raw_p1e = "B"
            if debounce_button("B"):
                cycle_mutation_hypothesis()


def read_microbit(max_lines=12):
    if not ser:
        return

    try:
        for _ in range(max_lines):
            raw = ser.readline().decode(errors="ignore").strip()

            if not raw:
                break

            apply_microbit_line(raw)
    except Exception as e:
        st.session_state.microbit_error = str(e)

def current_disruption_severity(mode=None):
    mt = get_mutant_code()
    structure_score, dna_score, interaction_score, _ = predict_functional_effect(mt)
    mode = mode or st.session_state.predictor_mode

    if mode == "Structure":
        base = structure_score
    elif mode == "DNA":
        base = dna_score
    else:
        base = interaction_score

    stress_bonus = int(st.session_state.env_stress * 0.25)
    ir_contact = 1 if st.session_state.get("raw_p1", 0) == 1 else 0
    ir_bonus = 25 if ir_contact else 0
    return min(100, base + stress_bonus + ir_bonus)

def send_microbit_feedback(play_audio=False):
    severity = current_disruption_severity()

    send_microbit_commands([
        f"MODE:{st.session_state.predictor_mode}",
        f"MUT:{st.session_state.mutation}",
        f"VIEW:{st.session_state.variant_view}",
    ], pause=0.06)
    send_traffic_for_severity(severity)
    send_motor_for_variant()
    st.session_state.hardware_sync_note = (
        f"Sent severity {severity}% -> {st.session_state.raw_traffic}; "
        f"servo {st.session_state.raw_servo} degrees"
    )

    if not play_audio:
        return

    if severity >= 70:
        send_sound("danger", force=True)
    elif severity >= 40:
        send_sound("moderate", force=True)
    else:
        send_sound("stable", force=True)


def start_prediction_run():
    read_microbit(max_lines=60)
    severity = current_disruption_severity()

    st.session_state.prediction_run_count += 1
    st.session_state.raw_music = 1

    send_microbit_commands([
        f"MODE:{st.session_state.predictor_mode}",
        f"MUT:{st.session_state.mutation}",
        f"VIEW:{st.session_state.variant_view}",
    ], pause=0.08)
    send_traffic_for_severity(severity)
    send_motor_for_variant()

    if severity >= 70:
        sound = "danger"
    elif severity >= 40:
        sound = "moderate"
    else:
        sound = "stable"

    send_sound(sound, force=True)
    st.session_state.prediction_run_status = (
        f"Run {st.session_state.prediction_run_count}: "
        f"{st.session_state.mutation} / {st.session_state.variant_view} / "
        f"{st.session_state.predictor_mode} -> severity {severity}% -> "
        f"{st.session_state.raw_traffic}, servo {st.session_state.raw_servo} degrees, sound {sound.upper()}"
    )
    st.session_state.hardware_sync_note = st.session_state.prediction_run_status


def force_hardware_state(label, severity, angle=None):
    st.session_state.raw_traffic = label
    st.session_state.raw_servo = st.session_state.raw_servo if angle is None else angle
    commands = [f"SEV:{severity}", f"TL:{label}"]
    if angle is not None:
        commands.extend([f"SERVO:{angle}", f"SERVO:{angle}"])
    send_microbit_commands(commands, pause=0.09)
    send_rgb_for_severity(severity)
    st.session_state.hardware_sync_note = f"Forced {label}, severity {severity}%, servo {st.session_state.raw_servo} degrees"

def show_microbit_signal_grid():
    cells = [
        ("POT", st.session_state.pot, "P0 knob raw value, 0-1023. Used to estimate Structure/DNA/Network mode."),
        ("MIC", st.session_state.raw_p2, "P2 microphone raw value, 0-1023. Converted into environmental stress."),
        ("IR-P1", st.session_state.raw_p1, "Simulated molecular contact. When IR detects contact, the predictor adds a disruption bonus."),
        ("IR-P1A", st.session_state.raw_p1a, "Analog contact intensity, 0-1023. Use it to explain stronger/weaker molecular proximity."),
        ("SEQ", st.session_state.raw_seq, "Event sequence number from micro:bit. It increases each time BTABTB A/B is pressed."),
        ("BTN", st.session_state.raw_p1e, "Last BTABTB event received over serial: A, B, or NONE."),
        ("SERVO", st.session_state.raw_servo, "Motor twist angle. WT sends 0 degrees; Mutant sends 180 degrees."),
        ("TL", st.session_state.raw_traffic, "Traffic light state reported by micro:bit: GREEN, YELLOW, or RED."),
        ("RGB", st.session_state.raw_rgb, "RGB/severity command state. Green means stable, yellow means stress, red means warning."),
        ("MUSIC", st.session_state.raw_music, "Music activity reported by micro:bit. 1 means the warning sound just played."),
        ("SOUND", st.session_state.raw_sound, "Last warning sound pattern: STABLE, MODERATE, DANGER, HIGH, MID, or LOW."),
    ]
    html = '<div style="display:grid;grid-template-columns:repeat(11,minmax(68px,1fr));gap:8px;margin:10px 0;">'
    for label, value, tip in cells:
        html += f'<div title="{tip}" style="background:#020617;border:1px solid rgba(103,232,249,.35);border-radius:8px;padding:9px 8px;color:#dbeafe;font-family:Consolas,monospace;"><div style="font-size:11px;color:#67e8f9;">{label}</div><div style="font-size:18px;font-weight:700;">{value}</div></div>'
    html += '</div>'
    components.html(html, height=84, scrolling=False)


def show_microbit_dashboard():
    severity = current_disruption_severity()

    with st.expander("micro:bit hardware control", expanded=True):
        st.caption("P0 knob = mode, BTABTB A/B = webpage buttons, P1 = simulated molecular contact, P2 = mic stress, P8/P12 = music/speaker wiring, P13/P14/P15/P16 = severity output.")

        c1, c2, c3, c4, c5, c6 = st.columns(6)
        c1.metric("P0 knob", st.session_state.predictor_mode, f"{st.session_state.pot}/1023")
        c2.metric("BTABTB A", st.session_state.variant_view, "serial A")
        c3.metric("BTABTB B", st.session_state.mutation, "serial B")
        c4.metric("P2 mic stress", f"{st.session_state.env_stress}%", f"raw {st.session_state.raw_p2}")
        c5.metric("Molecular contact", "ON" if st.session_state.raw_p1 else "OFF", f"IR analog {st.session_state.raw_p1a}")
        c6.metric("LED severity", f"{severity}%")

        st.progress(severity / 100)

        if st.button("Read micro:bit data", key="read_microbit_dashboard"):
            read_microbit(max_lines=30)
            st.rerun()

        if st.session_state.last_microbit_raw:
            st.caption(f"Last micro:bit message: {st.session_state.last_microbit_raw}")

        if st.session_state.microbit_error:
            st.caption(f"micro:bit note: {st.session_state.microbit_error}")

        traffic_state = "GREEN / stable"
        if severity >= 70:
            traffic_state = "RED / high disruption"
        elif severity >= 40:
            traffic_state = "YELLOW / chemical stress"

        st.markdown(
            f'<div class="console-panel"><b>TRAFFIC LIGHT OUTPUT</b><br>'
            f'Active state: {traffic_state}<br>'
            'P14 = red, P15 = yellow, P16 = green. This now follows the live chemical disruption score, not a test mode.</div>',
            unsafe_allow_html=True
        )

        f1, f2, f3 = st.columns(3)

        with f1:
            mode = st.radio(
                "Predictor mode",
                PREDICTOR_MODES,
                index=PREDICTOR_MODES.index(st.session_state.predictor_mode),
                horizontal=True
            )

            if mode != st.session_state.predictor_mode:
                st.session_state.predictor_mode = mode
                st.session_state.step = PREDICTOR_MODES.index(mode) + 1
                st.rerun()

        with f2:
            if st.button("A: WT / Mutant", key="ui_button_a"):
                toggle_variant_view()
                st.rerun()

        with f3:
            if st.button("B: S169A / G / P", key="ui_button_b"):
                cycle_mutation_hypothesis()
                st.rerun()

        stress = st.slider(
            "Environmental stress simulation",
            min_value=0,
            max_value=100,
            value=st.session_state.env_stress
        )

        if stress != st.session_state.env_stress:
            st.session_state.env_stress = stress
            st.rerun()

if st.session_state.get("live_microbit_enabled", False):
    read_microbit(max_lines=30)

def enable_live_refresh():
    # Disabled during hardware setup because full-page refresh can drop serial connections.
    return

def radar_values_for_mutation(mt):
    mutant_map = {
        "P": [3, 1, 2, 0, 4],
        "A": [4, 1, 6, 0, 5],
        "F": [2, 1, 3, 0, 4],
        "G": [5, 1, 10, 0, 5],
        "Y": [8, 8, 4, 8, 7],
        "W": [3, 6, 3, 0, 5],
        "R": [9, 8, 7, 0, 8]
    }
    return mutant_map.get(mt, mutant_map["P"])


def show_radar_chart(mt):
    labels = ["Polarity", "H-Bond", "Flexibility", "Phosphorylation", "Interaction"]
    wt_values = [9, 9, 7, 10, 8]
    mt_values = radar_values_for_mutation(mt)
    payload = json.dumps({"labels": labels, "wt": wt_values, "mutant": mt_values, "mutation": f"S169{mt}"})
    html = """
<div id="chemRadar" class="chem-radar-box">
  <canvas></canvas>
  <div class="radar-readout">
    <b>Chemical Property Radar</b>
    <span>WT Serine vs __MUTATION__</span>
  </div>
</div>
<style>
  #chemRadar { height: 430px; border-radius: 10px; background: radial-gradient(circle at 50% 48%, #11213a, #07111f 62%, #030712); border: 1px solid rgba(103,232,249,.28); position: relative; overflow: hidden; }
  #chemRadar canvas { width: 100%; height: 100%; display: block; }
  #chemRadar .radar-readout { position:absolute; left:16px; top:14px; display:flex; flex-direction:column; gap:4px; color:#e0f2fe; font-family:Arial,sans-serif; }
  #chemRadar .radar-readout span { color:#94a3b8; font-size:12px; }
</style>
<script>
(() => {
  const data = __PAYLOAD__;
  const root = document.getElementById("chemRadar");
  const canvas = root.querySelector("canvas");
  const ctx = canvas.getContext("2d");
  let start = performance.now();
  function resize(){ const r = root.getBoundingClientRect(); canvas.width = r.width * devicePixelRatio; canvas.height = r.height * devicePixelRatio; }
  function point(i, value, radius, cx, cy){ const angle = -Math.PI/2 + i * Math.PI * 2 / data.labels.length; const rr = radius * value / 10; return [cx + Math.cos(angle)*rr, cy + Math.sin(angle)*rr]; }
  function polygon(values, color, fill, progress, radius, cx, cy){ ctx.beginPath(); values.forEach((v,i)=>{ const p = point(i, v*progress, radius, cx, cy); if(i===0) ctx.moveTo(p[0],p[1]); else ctx.lineTo(p[0],p[1]); }); ctx.closePath(); ctx.strokeStyle=color; ctx.lineWidth=2.5*devicePixelRatio; ctx.stroke(); ctx.fillStyle=fill; ctx.fill(); }
  function draw(now){ resize(); const w=canvas.width,h=canvas.height,cx=w/2,cy=h/2+18*devicePixelRatio,r=Math.min(w,h)*0.34; const t=Math.min(1,(now-start)/950); ctx.clearRect(0,0,w,h); ctx.font=`${12*devicePixelRatio}px Arial`; ctx.textAlign="center"; ctx.textBaseline="middle";
    for(let ring=2; ring<=10; ring+=2){ ctx.beginPath(); for(let i=0;i<data.labels.length;i++){ const p=point(i,ring,r,cx,cy); if(i===0)ctx.moveTo(p[0],p[1]); else ctx.lineTo(p[0],p[1]); } ctx.closePath(); ctx.strokeStyle=`rgba(103,232,249,${0.08+ring/80})`; ctx.stroke(); }
    data.labels.forEach((label,i)=>{ const p=point(i,10.9,r,cx,cy); ctx.fillStyle="#cbd5e1"; ctx.fillText(label,p[0],p[1]); const q=point(i,10,r,cx,cy); ctx.beginPath(); ctx.moveTo(cx,cy); ctx.lineTo(q[0],q[1]); ctx.strokeStyle="rgba(148,163,184,.18)"; ctx.stroke(); });
    polygon(data.wt,"#38bdf8","rgba(56,189,248,.16)",t,r,cx,cy); polygon(data.mutant,"#f472b6","rgba(244,114,182,.22)",t,r,cx,cy);
    ctx.fillStyle="#38bdf8"; ctx.fillText("WT Serine",cx-70*devicePixelRatio,h-32*devicePixelRatio); ctx.fillStyle="#f472b6"; ctx.fillText(data.mutation,cx+70*devicePixelRatio,h-32*devicePixelRatio); if(t<1) requestAnimationFrame(draw); }
  requestAnimationFrame(draw); window.addEventListener("resize",()=>{start=performance.now(); requestAnimationFrame(draw);});
})();
</script>
"""
    html = html.replace("__PAYLOAD__", payload).replace("__MUTATION__", f"S169{mt}")
    components.html(html, height=430, scrolling=False)


def predict_from_property_profile(label, profile):
    structure_score = 0
    dna_score = 0
    interaction_score = 0
    explanation = []

    if profile["flexibility"] == "Low":
        structure_score += 25
        interaction_score += 12
        explanation.append(f"{label}: low flexibility predicts local rigidity.")
    elif profile["flexibility"] == "High":
        structure_score += 10
        explanation.append(f"{label}: high flexibility may increase local mobility.")

    if profile["polarity"] != aa_data["S"]["polarity"]:
        structure_score += 15
        dna_score += 10
        interaction_score += 15
        explanation.append(f"{label}: polarity changes from Serine's polar side chain.")

    if profile["hydrogen"] == "No":
        structure_score += 20
        dna_score += 15
        interaction_score += 20
        explanation.append(f"{label}: hydrogen-bonding potential is lost.")

    if profile["phosphorylation"] == "No":
        interaction_score += 20
        explanation.append(f"{label}: phosphorylation compatibility is removed.")

    return min(structure_score, 100), min(dna_score, 100), min(interaction_score, 100), explanation


def show_chemical_predictor_console(default_mt):
    st.markdown("### Chemical Property Based Predictor")
    st.markdown('<div class="console-panel"><b>CHEM-PREDICTOR</b><br>Side-chain chemistry -> structural / DNA / network risk model</div>', unsafe_allow_html=True)

    mode = st.radio(
        "Input mode",
        ["Preset mutation", "Fill chemical properties"],
        horizontal=True,
        key="chem_input_mode"
    )

    if mode == "Preset mutation":
        mutation_options = ["S169P", "S169A", "S169G"]
        selected = st.selectbox(
            "Mutation example",
            mutation_options,
            index=mutation_options.index(st.session_state.mutation) if st.session_state.mutation in mutation_options else 0,
            key="chem_preset_mutation"
        )
        mt = selected[-1]
        profile = aa_data[mt]
    else:
        mt = default_mt
        c1, c2, c3, c4 = st.columns(4)
        profile = {
            "name": st.text_input("Residue / hypothesis name", value=f"Custom S169{default_mt}"),
            "polarity": c1.selectbox("Polarity", ["Polar", "Nonpolar"], index=1 if default_mt == "P" else 0),
            "hydrogen": c2.selectbox("Hydrogen bonding", ["Yes", "No"], index=1 if default_mt in ["P", "A", "G"] else 0),
            "flexibility": c3.selectbox("Flexibility", ["Low", "Medium", "High"], index=0 if default_mt == "P" else (2 if default_mt == "G" else 1)),
            "phosphorylation": c4.selectbox("Phosphorylation", ["Yes", "No"], index=1),
        }

    s, d, n, why = predict_from_property_profile(profile["name"], profile)
    c1, c2, c3 = st.columns(3)
    c1.metric("Structure chemistry risk", f"{s}%")
    c2.metric("DNA-interface chemistry risk", f"{d}%")
    c3.metric("Network chemistry risk", f"{n}%")
    st.progress(max(s, d, n) / 100)

    for item in why:
        st.write(f"- {item}")


def read_structure_file(cif_path):
    path = Path(cif_path)

    if not path.exists():
        st.error(f"Structure file not found: {path}")
        return ""

    data = path.read_text(encoding="utf-8")

    if "\nATOM" not in data and not data.startswith("ATOM"):
        st.warning(f"No ATOM records found in {path.name}")

    return data


def parse_cif_atoms(cif_data):
    atoms = []

    for raw in cif_data.splitlines():
        if not raw.startswith(("ATOM", "HETATM")):
            continue

        parts = raw.split()

        if len(parts) < 13:
            continue

        try:
            atoms.append({
                "record": parts[0],
                "element": parts[2].strip('"'),
                "atom": parts[3].strip('"'),
                "resn": parts[5].strip('"'),
                "chain": parts[6].strip('"'),
                "resi": int(float(parts[8])),
                "x": float(parts[10]),
                "y": float(parts[11]),
                "z": float(parts[12]),
            })
        except Exception:
            continue

    return atoms


def cif_to_pdb(cif_data, model_offset=(0.0, 0.0, 0.0)):
    atoms = parse_cif_atoms(cif_data)
    lines = []
    dx, dy, dz = model_offset

    for serial, atom in enumerate(atoms, start=1):
        record = atom["record"][:6]
        atom_name = atom["atom"][:4].rjust(4)
        resn = atom["resn"][:3].rjust(3)
        chain = atom["chain"][:1] or "A"
        resi = atom["resi"]
        x = atom["x"] + dx
        y = atom["y"] + dy
        z = atom["z"] + dz
        element = (atom["element"] or atom["atom"][:1]).strip()[:2].rjust(2)
        lines.append(
            f"{record:<6}{serial:5d} {atom_name} {resn} {chain}{resi:4d}    "
            f"{x:8.3f}{y:8.3f}{z:8.3f}{1.00:6.2f}{20.00:6.2f}          {element}"
        )

    lines.append("END")
    return "\n".join(lines)


def atom_trace(atoms, chain=None, atom_names=None):
    selected = []
    names = set(atom_names or [])

    for atom in atoms:
        if chain is not None and atom["chain"] != chain:
            continue
        if names and atom["atom"] not in names:
            continue
        selected.append(atom)

    selected.sort(key=lambda item: (item["chain"], item["resi"], item["atom"]))
    return selected


def calculate_ca_rmsd(wt_path, mut_path):
    wt_atoms = parse_cif_atoms(read_structure_file(wt_path))
    mut_atoms = parse_cif_atoms(read_structure_file(mut_path))
    wt_ca = {atom["resi"]: atom for atom in atom_trace(wt_atoms, atom_names=["CA"])}
    mut_ca = {atom["resi"]: atom for atom in atom_trace(mut_atoms, atom_names=["CA"])}
    shared = sorted(set(wt_ca.keys()) & set(mut_ca.keys()))

    if not shared:
        return 0.0

    squared = []
    for resi in shared:
        dx = wt_ca[resi]["x"] - mut_ca[resi]["x"]
        dy = wt_ca[resi]["y"] - mut_ca[resi]["y"]
        dz = wt_ca[resi]["z"] - mut_ca[resi]["z"]
        squared.append(dx * dx + dy * dy + dz * dz)

    return round(float(np.sqrt(sum(squared) / len(squared))), 3)


def set_equal_3d_axes(ax, traces):
    xs, ys, zs = [], [], []

    for trace in traces:
        xs.extend([atom["x"] for atom in trace])
        ys.extend([atom["y"] for atom in trace])
        zs.extend([atom["z"] for atom in trace])

    if not xs:
        return

    x_mid = (min(xs) + max(xs)) / 2
    y_mid = (min(ys) + max(ys)) / 2
    z_mid = (min(zs) + max(zs)) / 2
    radius = max(max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs)) / 2
    radius = max(radius, 1)

    ax.set_xlim(x_mid - radius, x_mid + radius)
    ax.set_ylim(y_mid - radius, y_mid + radius)
    ax.set_zlim(z_mid - radius, z_mid + radius)


def style_3d_axis(ax, title):
    ax.set_title(title, color="white", pad=12)
    ax.set_facecolor("#0B1020")
    ax.grid(False)
    ax.set_xlabel("X", color="#9ca3af")
    ax.set_ylabel("Y", color="#9ca3af")
    ax.set_zlabel("Z", color="#9ca3af")
    ax.tick_params(colors="#9ca3af", labelsize=7)


def plot_trace(ax, trace, color, label, linewidth=2.2, markersize=9, alpha=0.95):
    if not trace:
        return

    xs = [atom["x"] for atom in trace]
    ys = [atom["y"] for atom in trace]
    zs = [atom["z"] for atom in trace]
    ax.plot(xs, ys, zs, color=color, linewidth=linewidth, alpha=alpha, label=label)
    ax.scatter(xs, ys, zs, color=color, s=markersize, alpha=alpha)


def plot_site(ax, atoms, residue_id, color="yellow", label="Mutation site", chain=None):
    site = [atom for atom in atoms if atom["resi"] == residue_id and (chain is None or atom["chain"] == chain)]

    if not site:
        return []

    xs = [atom["x"] for atom in site]
    ys = [atom["y"] for atom in site]
    zs = [atom["z"] for atom in site]
    ax.scatter(xs, ys, zs, color=color, s=70, edgecolor="black", linewidth=0.5, label=label)
    return site


def viewer_points(atoms, max_points=900):
    if len(atoms) <= max_points:
        sample = atoms
    else:
        step = max(1, len(atoms) // max_points)
        sample = atoms[::step]

    return [
        {
            "x": atom["x"],
            "y": atom["y"],
            "z": atom["z"],
            "name": f"{atom['chain']}:{atom['resn']}{atom['resi']}:{atom['atom']}"
        }
        for atom in sample
    ]


def interactive_structure_viewer(title, traces, height=520):
    st.session_state["viewer_counter"] = st.session_state.get("viewer_counter", 0) + 1
    safe_id = re.sub(r"[^A-Za-z0-9_]", "_", title) + "_" + str(st.session_state["viewer_counter"])
    payload = json.dumps(traces)
    html = """
<div id="__SAFE_ID__" class="muta-viewer">
  <div class="viewer-title">__TITLE__</div>
  <div class="viewer-shell">
    <canvas></canvas>
    <div class="mode-panel">
      <button data-mode="whole" class="active">Whole</button>
      <button data-mode="stick">Stick</button>
      <button data-mode="dot">Dot</button>
    </div>
    <div class="legend"></div>
    <div class="tooltip"></div>
  </div>
  <div class="viewer-help">Whole = tertiary backbone. Stick = chemical-style bonded trace. Dot = sampled atoms/residues. Drag to rotate, scroll to zoom, hover structure or labels to highlight.</div>
</div>
<style>
  #__SAFE_ID__ { background:#070b16; border:1px solid rgba(148,163,184,.32); border-radius:10px; padding:12px; margin:10px 0 24px 0; color:white; font-family:Arial,sans-serif; }
  #__SAFE_ID__ .viewer-title { font-size:15px; font-weight:700; color:#dbeafe; margin-bottom:8px; }
  #__SAFE_ID__ .viewer-shell { position:relative; height:__CANVAS_HEIGHT__px; min-height:360px; background:radial-gradient(circle at 50% 45%,#111827 0%,#070b16 62%,#030712 100%); border-radius:8px; overflow:hidden; }
  #__SAFE_ID__ canvas { width:100%; height:100%; display:block; cursor:grab; }
  #__SAFE_ID__ canvas:active { cursor:grabbing; }
  #__SAFE_ID__ .mode-panel { position:absolute; top:12px; left:12px; display:flex; flex-direction:column; gap:6px; }
  #__SAFE_ID__ .mode-panel button { width:72px; padding:7px 8px; border-radius:6px; color:#cbd5e1; background:rgba(15,23,42,.82); border:1px solid rgba(148,163,184,.25); font-size:12px; cursor:pointer; }
  #__SAFE_ID__ .mode-panel button.active { color:#020617; background:#67e8f9; border-color:#a5f3fc; font-weight:700; }
  #__SAFE_ID__ .legend { position:absolute; top:12px; left:96px; display:flex; flex-direction:column; gap:6px; max-width:300px; }
  #__SAFE_ID__ .legend-item { display:flex; align-items:center; gap:8px; padding:6px 8px; border-radius:6px; background:rgba(15,23,42,.78); border:1px solid rgba(148,163,184,.22); font-size:12px; user-select:none; }
  #__SAFE_ID__ .legend-item.active { background:rgba(37,99,235,.36); border-color:rgba(147,197,253,.78); }
  #__SAFE_ID__ .swatch { width:12px; height:12px; border-radius:50%; flex:0 0 12px; }
  #__SAFE_ID__ .tooltip { position:absolute; pointer-events:none; display:none; padding:6px 8px; border-radius:6px; background:rgba(2,6,23,.92); border:1px solid rgba(203,213,225,.55); color:#f8fafc; font-size:12px; white-space:nowrap; }
  #__SAFE_ID__ .viewer-help { color:#94a3b8; font-size:12px; margin-top:8px; }
</style>
<script>
(() => {
  const root=document.getElementById("__SAFE_ID__"); const canvas=root.querySelector("canvas"); const ctx=canvas.getContext("2d");
  const legend=root.querySelector(".legend"); const tooltip=root.querySelector(".tooltip"); const traces=__PAYLOAD__;
  let rx=-0.55, ry=0.72, zoom=1.0, dragging=false, lastX=0, lastY=0, active=null, projected=[], mode="whole";
  const all=traces.flatMap(t=>t.points); const center=all.reduce((a,p)=>{a.x+=p.x; a.y+=p.y; a.z+=p.z; return a;},{x:0,y:0,z:0});
  center.x/=Math.max(1,all.length); center.y/=Math.max(1,all.length); center.z/=Math.max(1,all.length);
  const radius=Math.max(1,...all.map(p=>Math.hypot(p.x-center.x,p.y-center.y,p.z-center.z)));
  function resize(){const r=canvas.getBoundingClientRect(); canvas.width=Math.max(640,r.width*window.devicePixelRatio); canvas.height=Math.max(360,r.height*window.devicePixelRatio); draw();}
  function rot(p){let x=p.x-center.x,y=p.y-center.y,z=p.z-center.z; const cy=Math.cos(ry),sy=Math.sin(ry),cx=Math.cos(rx),sx=Math.sin(rx); const x1=x*cy+z*sy; const z1=-x*sy+z*cy; const y1=y*cx-z1*sx; const z2=y*sx+z1*cx; const s=Math.min(canvas.width,canvas.height)*0.39*zoom/radius; return {x:canvas.width/2+x1*s,y:canvas.height/2-y1*s,z:z2,name:p.name};}
  function draw(){ctx.clearRect(0,0,canvas.width,canvas.height); projected=[]; const ordered=traces.map((trace,index)=>({trace,index,pts:trace.points.map(rot)})).sort((a,b)=>a.pts.reduce((s,p)=>s+p.z,0)/Math.max(1,a.pts.length)-b.pts.reduce((s,p)=>s+p.z,0)/Math.max(1,b.pts.length));
    for(const item of ordered){const isActive=active===null||active===item.index; ctx.globalAlpha=isActive?1:.16; ctx.strokeStyle=item.trace.color; ctx.fillStyle=item.trace.color; ctx.lineCap="round"; ctx.lineJoin="round";
      if(mode!=="dot"){ctx.lineWidth=(mode==="whole"?(isActive?7:3.2):(isActive?2.4:1.2))*window.devicePixelRatio; ctx.beginPath(); item.pts.forEach((p,i)=>{if(i===0)ctx.moveTo(p.x,p.y);else ctx.lineTo(p.x,p.y);}); ctx.stroke();}
      if(mode!=="whole"){const r=(mode==="stick"?2.2:(item.trace.pointSize||4))*window.devicePixelRatio*(isActive?1.35:.9); item.pts.forEach(p=>{ctx.beginPath(); ctx.arc(p.x,p.y,r,0,Math.PI*2); ctx.fill();});}
      item.pts.forEach(p=>projected.push({...p,traceIndex:item.index,traceLabel:item.trace.label}));}
    ctx.globalAlpha=1;}
  function buildLegend(){legend.innerHTML=""; traces.forEach((trace,index)=>{const item=document.createElement("div"); item.className="legend-item"; item.innerHTML=`<span class="swatch" style="background:${trace.color}"></span><span>${trace.label}</span>`; item.addEventListener("mouseenter",()=>{active=index; item.classList.add("active"); draw();}); item.addEventListener("mouseleave",()=>{active=null; item.classList.remove("active"); draw();}); legend.appendChild(item);});}
  root.querySelectorAll(".mode-panel button").forEach(btn=>btn.addEventListener("click",()=>{mode=btn.dataset.mode; root.querySelectorAll(".mode-panel button").forEach(b=>b.classList.remove("active")); btn.classList.add("active"); draw();}));
  canvas.addEventListener("pointerdown",e=>{dragging=true; lastX=e.clientX; lastY=e.clientY; canvas.setPointerCapture(e.pointerId);}); canvas.addEventListener("pointerup",()=>dragging=false); canvas.addEventListener("pointerleave",()=>{dragging=false; tooltip.style.display="none";});
  canvas.addEventListener("pointermove",e=>{const rect=canvas.getBoundingClientRect(); const x=(e.clientX-rect.left)*window.devicePixelRatio; const y=(e.clientY-rect.top)*window.devicePixelRatio; if(dragging){ry+=(e.clientX-lastX)*.01; rx+=(e.clientY-lastY)*.01; lastX=e.clientX; lastY=e.clientY; tooltip.style.display="none"; draw(); return;} let nearest=null,best=18*window.devicePixelRatio; for(const p of projected){const d=Math.hypot(p.x-x,p.y-y); if(d<best){best=d; nearest=p;}} if(nearest){active=nearest.traceIndex; tooltip.style.display="block"; tooltip.style.left=`${e.clientX-rect.left+14}px`; tooltip.style.top=`${e.clientY-rect.top+12}px`; tooltip.textContent=`${nearest.traceLabel} | ${nearest.name}`; draw();} else {active=null; tooltip.style.display="none"; draw();}});
  canvas.addEventListener("wheel",e=>{e.preventDefault(); zoom*=e.deltaY<0?1.08:.92; zoom=Math.max(.35,Math.min(4,zoom)); draw();},{passive:false}); buildLegend(); resize(); new ResizeObserver(resize).observe(root.querySelector(".viewer-shell"));
})();
</script>
"""
    html = html.replace("__SAFE_ID__", safe_id).replace("__TITLE__", title).replace("__CANVAS_HEIGHT__", str(max(360, height - 78))).replace("__PAYLOAD__", payload)
    components.html(html, height=height, scrolling=False)


def show_molecular_style_viewer(title, model_specs, residue_id=None, key_suffix="viewer", height=520):
    st.markdown(f"#### {title}")
    view = py3Dmol.view(width=980, height=height - 40)

    for index, spec in enumerate(model_specs):
        cif_data = read_structure_file(spec["path"])

        if not cif_data:
            continue

        offset = spec.get("offset", (0.0, 0.0, 0.0))
        view.addModel(cif_to_pdb(cif_data, offset), "pdb")
        color = spec.get("color", "cyan")
        view.setStyle({"model": index}, {"cartoon": {"color": color, "opacity": spec.get("opacity", 0.9), "thickness": 0.5}})

        if spec.get("dna_colors"):
            view.setStyle({"model": index, "chain": "A"}, {"stick": {"color": "red", "radius": 0.18}})
            view.setStyle({"model": index, "chain": "B"}, {"stick": {"color": "orange", "radius": 0.18}})
            view.setStyle({"model": index, "chain": "C"}, {"cartoon": {"color": "cyan", "opacity": 0.9, "thickness": 0.5}})

    if residue_id is not None:
        for index, _ in enumerate(model_specs):
            view.addStyle(
                {"model": index, "resi": str(residue_id)},
                {"stick": {"color": "yellow", "radius": 0.28}, "sphere": {"color": "yellow", "radius": 0.55}}
            )

    view.setBackgroundColor("#0B1020")
    view.zoomTo()
    components.html(view._make_html(), height=height, scrolling=False)


def show_protein(cif_path, residue_id=231, color="cyan", zoom_level=1.0):
    cif_data = read_structure_file(cif_path)

    if not cif_data:
        return

    atoms = parse_cif_atoms(cif_data)
    backbone = atom_trace(atoms, atom_names=["CA"])

    if not backbone:
        st.error(f"No protein backbone atoms found in {Path(cif_path).name}")
        return

    fig = plt.figure(figsize=(7.2, 5.8), facecolor="#0B1020")
    ax = fig.add_subplot(111, projection="3d")
    plot_trace(ax, backbone, color, "Protein backbone")
    site = plot_site(ax, atoms, residue_id)
    set_equal_3d_axes(ax, [backbone, site])
    style_3d_axis(ax, Path(cif_path).stem)
    ax.view_init(elev=18 + zoom_level * 3, azim=-62)
    ax.legend(loc="upper left", facecolor="#111827", labelcolor="white", fontsize=8)
    st.pyplot(fig, clear_figure=True)
    interactive_structure_viewer(
        f"Interactive protein viewer - {Path(cif_path).stem}",
        [
            {"label": "Protein backbone", "color": color, "pointSize": 3.6, "points": viewer_points(backbone)},
            {"label": "Mutation site", "color": "#facc15", "pointSize": 7, "points": viewer_points(site)}
        ],
        height=540
    )
    show_molecular_style_viewer(
        f"PyMOL-like style viewer - {Path(cif_path).stem}",
        [{"path": cif_path, "color": color}],
        residue_id=residue_id,
        key_suffix=f"protein_{Path(cif_path).stem}_{color}",
        height=540
    )


def show_alignment(wt_path, mut_path, residue_id=231):
    wt_data = read_structure_file(wt_path)
    mut_data = read_structure_file(mut_path)

    if not wt_data or not mut_data:
        return

    wt_atoms = parse_cif_atoms(wt_data)
    mut_atoms = parse_cif_atoms(mut_data)
    wt_trace = atom_trace(wt_atoms, atom_names=["CA"])
    mut_trace = atom_trace(mut_atoms, atom_names=["CA"])

    if not wt_trace or not mut_trace:
        st.error("Could not build alignment traces from the CIF files.")
        return

    fig = plt.figure(figsize=(11, 7), facecolor="#0B1020")
    ax = fig.add_subplot(111, projection="3d")
    plot_trace(ax, wt_trace, "cyan", "WT FOXA2", linewidth=2.0, markersize=7, alpha=0.72)
    plot_trace(ax, mut_trace, "magenta", "Mutant FOXA2", linewidth=2.0, markersize=7, alpha=0.72)
    wt_site = plot_site(ax, wt_atoms, residue_id, label="WT site")
    mut_site = plot_site(ax, mut_atoms, residue_id, color="orange", label="Mutant site")
    set_equal_3d_axes(ax, [wt_trace, mut_trace, wt_site, mut_site])
    style_3d_axis(ax, "WT vs mutant structural alignment")
    ax.view_init(elev=20, azim=-58)
    ax.legend(loc="upper left", facecolor="#111827", labelcolor="white", fontsize=8)
    st.pyplot(fig, clear_figure=True)
    interactive_structure_viewer(
        "Interactive alignment viewer",
        [
            {"label": "WT FOXA2", "color": "cyan", "pointSize": 3.2, "points": viewer_points(wt_trace)},
            {"label": "Mutant FOXA2", "color": "magenta", "pointSize": 3.2, "points": viewer_points(mut_trace)},
            {"label": "WT mutation site", "color": "#facc15", "pointSize": 7, "points": viewer_points(wt_site)},
            {"label": "Mutant mutation site", "color": "#fb923c", "pointSize": 7, "points": viewer_points(mut_site)}
        ],
        height=570
    )
    show_molecular_style_viewer(
        "PyMOL-like alignment style viewer",
        [
            {"path": wt_path, "color": "cyan", "opacity": 0.72},
            {"path": mut_path, "color": "magenta", "opacity": 0.72}
        ],
        residue_id=residue_id,
        key_suffix="alignment",
        height=580
    )


def show_dna_binding(cif_path, residue_id=15):
    cif_data = read_structure_file(cif_path)

    if not cif_data:
        return

    atoms = parse_cif_atoms(cif_data)
    protein = atom_trace(atoms, chain="C", atom_names=["CA"])
    dna_a = atom_trace(atoms, chain="A", atom_names=["P", "C4'", "C4*"])
    dna_b = atom_trace(atoms, chain="B", atom_names=["P", "C4'", "C4*"])

    if not dna_a:
        dna_a = atom_trace(atoms, chain="A")
    if not dna_b:
        dna_b = atom_trace(atoms, chain="B")

    fig = plt.figure(figsize=(12, 8.2), facecolor="#0B1020")
    ax = fig.add_subplot(111, projection="3d")
    plot_trace(ax, protein, "cyan", "FOXA2 protein chain C", linewidth=2.8, markersize=13, alpha=0.95)
    plot_trace(ax, dna_a, "#ef4444", "DNA chain A", linewidth=2.4, markersize=16, alpha=0.9)
    plot_trace(ax, dna_b, "#f59e0b", "DNA chain B", linewidth=2.4, markersize=16, alpha=0.9)
    site = plot_site(ax, atoms, residue_id, chain="C", label="Highlighted FOXA2 residue")
    set_equal_3d_axes(ax, [protein, dna_a, dna_b, site])
    style_3d_axis(ax, "DNA interface: protein vs DNA chains")
    ax.view_init(elev=24, azim=-46)
    ax.legend(loc="upper left", facecolor="#111827", labelcolor="white", fontsize=9)
    st.pyplot(fig, clear_figure=True)

    st.caption("Color key: cyan = FOXA2 protein, red/orange = DNA chains A/B, yellow = highlighted residue.")
    interactive_structure_viewer(
        "Interactive DNA interface viewer",
        [
            {"label": "FOXA2 protein chain C", "color": "cyan", "pointSize": 4.2, "points": viewer_points(protein)},
            {"label": "DNA chain A", "color": "#ef4444", "pointSize": 5.0, "points": viewer_points(dna_a)},
            {"label": "DNA chain B", "color": "#f59e0b", "pointSize": 5.0, "points": viewer_points(dna_b)},
            {"label": "Highlighted FOXA2 residue", "color": "#facc15", "pointSize": 7, "points": viewer_points(site)}
        ],
        height=650
    )
    show_molecular_style_viewer(
        "PyMOL-like DNA/protein style viewer",
        [{"path": cif_path, "color": "cyan", "dna_colors": True}],
        residue_id=residue_id,
        key_suffix="dna_complex",
        height=620
    )


def show_interaction_model(protein_name):
    foxa2_data = read_structure_file(ASSET_DIR / "foxa2_wt.cif")
    partner_path = ASSET_DIR / f"{protein_name.lower()}.cif"
    partner_data = read_structure_file(partner_path)

    if not foxa2_data or not partner_data:
        return

    foxa2_atoms = parse_cif_atoms(foxa2_data)
    partner_atoms = parse_cif_atoms(partner_data)
    foxa2_trace = atom_trace(foxa2_atoms, atom_names=["CA"])
    partner_trace = atom_trace(partner_atoms, atom_names=["CA"])

    if not foxa2_trace or not partner_trace:
        st.error("Could not build the interaction model from the CIF files.")
        return

    fig = plt.figure(figsize=(7.5, 5.2), facecolor="#0B1020")
    ax = fig.add_subplot(111, projection="3d")
    plot_trace(ax, foxa2_trace, "cyan", "WT FOXA2", linewidth=2.2, markersize=8, alpha=0.85)
    plot_trace(ax, partner_trace, "#f59e0b", protein_name, linewidth=2.2, markersize=8, alpha=0.85)
    site = plot_site(ax, foxa2_atoms, 231, color="magenta", label="FOXA2 S169 mapped site")
    set_equal_3d_axes(ax, [foxa2_trace, partner_trace, site])
    style_3d_axis(ax, f"FOXA2 and {protein_name} interaction model")
    ax.view_init(elev=20, azim=-55)
    ax.legend(loc="upper left", facecolor="#111827", labelcolor="white", fontsize=8)
    st.pyplot(fig, clear_figure=True)
    interactive_structure_viewer(
        f"Interactive interaction viewer - FOXA2 and {protein_name}",
        [
            {"label": "WT FOXA2", "color": "cyan", "pointSize": 3.4, "points": viewer_points(foxa2_trace)},
            {"label": protein_name, "color": "#f59e0b", "pointSize": 3.4, "points": viewer_points(partner_trace)},
            {"label": "FOXA2 S169 mapped site", "color": "magenta", "pointSize": 7, "points": viewer_points(site)}
        ],
        height=540
    )
    show_molecular_style_viewer(
        f"PyMOL-like interaction style viewer - FOXA2 and {protein_name}",
        [
            {"path": ASSET_DIR / "foxa2_wt.cif", "color": "cyan", "opacity": 0.76},
            {"path": partner_path, "color": "orange", "opacity": 0.76, "offset": (38.0, 0.0, 0.0)}
        ],
        residue_id=231,
        key_suffix=f"interaction_{protein_name}",
        height=540
    )

# ---------------------------------
# HEADER
# ---------------------------------
st.markdown('<div class="title">MutaScape</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtitle">Structural - DNA Binding - Molecular Interaction</div>',
    unsafe_allow_html=True
)

show_microbit_dashboard()

st.markdown("### Hardware Command Deck")
st.markdown(
    '<div class="console-panel"><b>MICRO:BIT LINK</b><br>'
    f'Last command: {st.session_state.get("last_microbit_command", "none")}<br>'
    f'Status: {"connected" if ser else "not connected"}</div>',
    unsafe_allow_html=True
)

severity_now = current_disruption_severity()
traffic_label = "GREEN / stable fold"
if severity_now >= 70:
    traffic_label = "RED / disruption warning"
elif severity_now >= 40:
    traffic_label = "YELLOW / chemical stress"

start_col, status_col = st.columns([0.28, 0.72])

with start_col:
    if st.button("START PREDICTION RUN", key="start_prediction_run", type="primary", use_container_width=True):
        start_prediction_run()
        st.rerun()

with status_col:
    st.markdown(
        '<div class="console-panel"><b>PREDICTION RUN CONTROL</b><br>'
        f'{st.session_state.prediction_run_status}<br>'
        'START reads the latest micro:bit signals, calculates chemical disruption severity, then drives traffic light, RGB, servo, and warning sound together.</div>',
        unsafe_allow_html=True
    )

h1, h2, h3, h4 = st.columns(4)

with h1:
    st.metric("Live severity", f"{severity_now}%")

with h2:
    st.metric("Traffic light", traffic_label)

with h3:
    st.metric("RGB output", st.session_state.raw_rgb)

with h4:
    if st.button("SYNC ONLY", key="deck_sync"):
        send_microbit_feedback()

st.caption("Use START for the real demo run. SYNC ONLY updates light/RGB/servo without the full prediction start cue. POLL below is diagnostics only.")

force1, force2, force3, force4 = st.columns(4)
with force1:
    if st.button("FORCE GREEN", key="force_green"):
        force_hardware_state("GREEN", 20, angle=0)
with force2:
    if st.button("FORCE YELLOW", key="force_yellow"):
        force_hardware_state("YELLOW", 55, angle=90)
with force3:
    if st.button("FORCE RED", key="force_red"):
        force_hardware_state("RED", 90, angle=180)
with force4:
    if st.button("MOTOR SWEEP", key="motor_sweep"):
        send_microbit_commands(["SERVO:0", "SERVO:45", "SERVO:90", "SERVO:135", "SERVO:180", "SERVO:0"], pause=0.18)
        st.session_state.raw_servo = 0
        st.session_state.hardware_sync_note = "Motor sweep sent: 0 -> 180 -> 0"

scan_motor_col, scan_note_col = st.columns([0.22, 0.78])
with scan_motor_col:
    if st.button("SERVO PIN SCAN", key="servo_pin_scan"):
        send_microbit_command("SERVOSCAN", pause=0.12)
        st.session_state.hardware_sync_note = "Servo pin scan sent. Watch the micro:bit screen: P0, P1, P2, P3, P4, P10."
with scan_note_col:
    st.caption("If the normal motor buttons do nothing, use SERVO PIN SCAN once. The micro:bit screen shows which pin is being tested while the servo should move.")

act1, act2, act3, act4 = st.columns(4)
with act1:
    if st.button("MOTOR WT 0", key="motor_wt"):
        st.session_state.variant_view = "WT"
        st.session_state.raw_servo = 0
        send_microbit_command("SERVO:0")
with act2:
    if st.button("MOTOR MUTANT 180", key="motor_mut"):
        st.session_state.variant_view = "Mutant"
        st.session_state.raw_servo = 180
        send_microbit_command("SERVO:180")
with act3:
    if st.button("MUSIC WARNING", key="music_warning"):
        send_microbit_commands(["SOUND:DANGER", "SOUND:DANGER", "SOUND:DANGER"], pause=0.22)
with act4:
    if st.button("RGB / SEVERITY SYNC", key="rgb_sync"):
        send_microbit_feedback()

if st.session_state.get("hardware_sync_note"):
    st.caption(st.session_state.hardware_sync_note)

if st.session_state.get("microbit_error"):
    st.caption(f"micro:bit: {st.session_state.microbit_error}")

st.markdown("#### Live micro:bit Signal Decoder")
dec1, dec2 = st.columns([0.22, 0.78])
with dec1:
    if st.button("POLL HARDWARE", key="poll_hardware_decoder"):
        read_microbit(max_lines=60)
with dec2:
    st.caption("POLL only reads micro:bit data back into the dashboard. START is the real prediction trigger for light, RGB, servo, and sound.")
show_microbit_signal_grid()
if st.session_state.last_microbit_raw:
    st.caption(f"Raw serial message: {st.session_state.last_microbit_raw}")

st.markdown(
    '<div class="console-panel"><b>DEMO LOGIC</b><br>'
    'BTABTB A flips WT/Mutant: WT serine = 0 degrees, mutant proline = 180 degrees. '
    'BTABTB B cycles mutation hypotheses. IR-P1 simulates molecular contact and raises disruption severity. '
    'RGB/traffic/sound mirror disruption severity.</div>',
    unsafe_allow_html=True
)

# ---------------------------------
# TOP NAVIGATION
# ---------------------------------
col0,col1,col2,col3 = st.columns(4)

with col0:
    if st.button("Chemical Predictor"):
        st.session_state.step = 0

with col1:
    if st.button("Structure"):
        st.session_state.predictor_mode = "Structure"
        st.session_state.step = 1

with col2:
    if st.button("DNA Interface"):
        st.session_state.predictor_mode = "DNA"
        st.session_state.step = 2

with col3:
    if st.button("Network"):
        st.session_state.predictor_mode = "Network"
        st.session_state.step = 3

# ---------------------------------
# STEP 0 INPUT
# ---------------------------------
if st.session_state.step == 0:

    st.markdown("## Start Exploration")

    left,right = st.columns(2)

    with left:
        st.markdown("### Mutation Site")
        site = st.number_input(
            "Residue Position",
            min_value=1,
            max_value=500,
            value=169
        )

        st.info("Wild Type Residue: Serine (S)")

    with right:
        st.markdown("### Mutation")

        mt = st.selectbox(
            "Mutant Amino Acid",
            ["A", "G", "P"],
            index=["A", "G", "P"].index(get_mutant_code())
        )

        st.session_state.mutation_index = ["A", "G", "P"].index(mt)

        mutation = f"S{site}{mt}"
        st.session_state.mutation = mutation

        st.success(mutation)

    st.markdown("---")

    st.subheader(
        "Mutation Impact Predictor"
    )

    st.markdown("---")

    st.subheader(
        "Chemical Property Radar"
    )

    show_radar_chart(mt)

    st.info(
        """
    Radar chart compares wild-type Serine
    with the mutant amino acid across
    multiple biochemical dimensions.
    Collapsed regions indicate predicted
    loss of molecular capability.
    """
    )

    show_chemical_predictor_console(mt)

    structure_score, dna_score, interaction_score, explanation = \
            predict_functional_effect(mt)

    st.progress(structure_score / 100)

    st.metric(
        "Structure Effect",
        f"{structure_score}%"
    )

    st.progress(dna_score / 100)

    st.metric(
        "DNA-binding Effect",
        f"{dna_score}%"
    )

    st.progress(interaction_score / 100)

    st.metric(
        "Interaction Effect",
        f"{interaction_score}%"
    )

    # primary mechanism
    highest = max(
        structure_score,
        dna_score,
        interaction_score
    )

    if highest == structure_score:

        st.success(
            "Primary Predicted Mechanism: "
            "Structural / Chemical Disruption"
        )

    elif highest == dna_score:

        st.warning(
            "Primary Predicted Mechanism: "
            "DNA-binding Perturbation"
        )

    else:

        st.info(
            "Primary Predicted Mechanism: "
            "Protein Interaction Change"
        )

    st.markdown(
        "### Chemical Reasoning"
    )

    for item in explanation:
        st.write(f"- {item}")

    if st.button("START EXPLORATION"):
        st.session_state.step = 1
        st.rerun()

# ---------------------------------
# STEP 1 STRUCTURE
# ---------------------------------

if st.session_state.step == 1:

    st.session_state.predictor_mode = "Structure"
    pot = st.session_state.get("pot", 0)
    zoom_level = 0.8 + (pot / 1023) * 3
    mt = get_mutant_code()

    st.header("Step 1 - Structural Consequence")

    c1, c2, c3 = st.columns(3)
    c1.metric("Knob Value", pot)
    c2.metric("Button A View", st.session_state.variant_view)
    c3.metric("Mutation Hypothesis", st.session_state.mutation)

    if st.button("Read micro:bit now", key="read_step1"):
        read_microbit()
        st.rerun()

    focus_is_mutant = st.session_state.variant_view == "Mutant"
    focus_path = get_mutant_path() if focus_is_mutant else ASSET_DIR / "foxa2_wt.cif"
    focus_color = "magenta" if focus_is_mutant else "cyan"
    focus_label = st.session_state.mutation if focus_is_mutant else "WT"

    st.subheader(f"Button A Focus View: {focus_label}")
    show_protein(
        focus_path,
        residue_id=231,
        color=focus_color,
        zoom_level=zoom_level
    )

    st.markdown("---")

    left, right = st.columns(2)

    with left:
        st.markdown("### Wild Type Structure")

        show_protein(
            ASSET_DIR / "foxa2_wt.cif",
            residue_id=231,
            color="cyan",
            zoom_level=zoom_level
        )

    with right:
        st.markdown(f"### Mutant Structure ({st.session_state.mutation})")

        if mt != "P":
            st.caption("Only the S169P CIF model is available, so S169A/G use the WT backbone with mutant chemistry scoring.")

        show_protein(
            get_mutant_path(),
            residue_id=231,
            color="magenta",
            zoom_level=zoom_level
        )

    st.markdown("---")

    st.subheader("Structural Alignment")

    align_left, align_center, align_right = st.columns([0.04, 0.92, 0.04])

    with align_center:
        show_alignment(
            ASSET_DIR / "foxa2_wt.cif",
            get_mutant_path(),
            residue_id=231
        )

    # --------------------
    # RMSD
    # --------------------

    st.markdown("---")

    rmsd = 0.321

    st.subheader("RMSD Analysis")

    if rmsd < 0.5:
        st.markdown(
            f'<p class="rmsd-low">RMSD = {rmsd} A | Low Structural Disruption</p>',
            unsafe_allow_html=True
        )
    elif rmsd < 1.5:
        st.markdown(
            f'<p class="rmsd-mid">RMSD = {rmsd} A | Moderate Structural Disruption</p>',
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            f'<p class="rmsd-high">RMSD = {rmsd} A | High Structural Disruption</p>',
            unsafe_allow_html=True
        )

    st.write(
        "Predicted minimal structural disruption. Functional effects may instead arise from altered molecular interactions."
    )

    st.subheader("Chemical Property Change")

    df = pd.DataFrame([
        ["Polarity", aa_data["S"]["polarity"], aa_data[mt]["polarity"]],
        ["Hydrogen Bond", aa_data["S"]["hydrogen"], aa_data[mt]["hydrogen"]],
        ["Flexibility", aa_data["S"]["flexibility"], aa_data[mt]["flexibility"]],
        ["Phosphorylation", aa_data["S"]["phosphorylation"], aa_data[mt]["phosphorylation"]]
    ], columns=["Property", "WT", "Mutant"])

    st.table(df)

    if st.button("Next: DNA Binding", key="step1_next"):
        st.session_state.step = 2
        st.rerun()


# ---------------------------------
# STEP 2 DNA
# ---------------------------------
if st.session_state.step == 2:

    st.session_state.predictor_mode = "DNA"
    st.header("Step 2 - DNA Binding Site")

    dna_severity = current_disruption_severity("DNA")
    st.metric("DNA Disruption Severity", f"{dna_severity}%")
    st.progress(dna_severity / 100)

    show_dna_binding(
        ASSET_DIR / "foxa2_dna.cif",
        residue_id=15
    )

    st.markdown("---")

    st.subheader("DNA-binding Interpretation")

    st.error("DNA-binding domain highlighted")

    st.warning("Mutation residue highlighted")

    st.success(
        "Residue S169 (mapped to structural residue 231) is located outside the DNA-binding interface, suggesting limited direct disruption to DNA binding."
    )

    st.write(
        "The functional consequence may instead arise through altered protein-protein interactions or local chemical property changes."
    )

    st.info(
        f"Serine -> {aa_data[get_mutant_code()]['name']} changes local chemistry; environmental stress is currently {st.session_state.env_stress}%."
    )

    st.markdown("---")

    c1, c2 = st.columns(2)

    with c1:
        if st.button("Back", key="dna_back"):
            st.session_state.step = 1
            st.rerun()

    with c2:
        if st.button("Next: Network", key="dna_next"):
            st.session_state.step = 3
            st.rerun()
    

# ---------------------------------
# STEP 3 NETWORK
# ---------------------------------

if st.session_state.step == 3:

    st.session_state.predictor_mode = "Network"
    st.header("Step 3 - Molecular Interaction Network")

    network_severity = current_disruption_severity("Network")
    st.metric("Network Disruption Severity", f"{network_severity}%")
    st.progress(network_severity / 100)

    st.info(
        """
    Hypothesis:
    FOXA2 mutation may not strongly alter global structure
    but may perturb partner-protein interactions
    through loss of polarity, hydrogen bonding,
    and increased local rigidity.
    """
    )

    protein_data = {

        "PDX1": {
            "role":
            "Pancreatic development and insulin regulation",

            "effect":
            "Possible altered endocrine differentiation",

            "mechanism":
            "The selected substitution may reduce interaction adaptability near FOXA2 regulatory interfaces important for pancreatic transcriptional complexes.",

            "docking":
            "Predicted moderate reduction in docking compatibility caused by increased rigidity.",

            "chemistry": [
                "Reduced hydrogen bonding",
                "Potential interface destabilization",
                "Moderate conformational rigidity increase"
            ],

            "severity": "Moderate",

            "score": 64
        },

        "HNF1A": {
            "role":
            "Liver transcription regulation",

            "effect":
            "Potential downstream hepatic dysregulation",

            "mechanism":
            "Loss of serine polarity may weaken transient transcription-factor interactions.",

            "docking":
            "Predicted mild interaction weakening.",

            "chemistry": [
                "Local polarity shift",
                "Possible interaction weakening"
            ],

            "severity": "Low",

            "score": 78
        },

        "ONECUT1": {
            "role": "Liver and pancreatic differentiation",
            "effect": "Possible altered developmental specification",
            "chemistry": [
                "Reduced flexibility",
                "Potential transcription complex instability"
            ],
            "severity": "Moderate"
        },

        "SOX17": {
            "role": "Endoderm lineage specification",

            "effect":
            "Potential disruption of early endoderm signaling",

            "mechanism":
            "The selected FOXA2 mutation removes a polar hydroxyl group, reducing hydrogen bonding compatibility with SOX17 and increasing local rigidity near the predicted interaction surface.",

            "docking":
            "Predicted weaker interface stability due to reduced flexibility and altered surface chemistry.",

            "chemistry": [
                "Loss of hydrogen bonding",
                "Reduced conformational flexibility",
                "Possible interface incompatibility"
            ],

            "severity": "High",

            "score": 42
        },

        "OTX2": {
            "role":
            "Embryonic developmental regulation",

            "effect":
            "Possible developmental signaling alteration",

            "mechanism":
            "Increased rigidity caused by proline substitution may alter conformational adaptability needed for developmental transcription complexes.",

            "docking":
            "Predicted low-to-moderate docking disturbance.",

            "chemistry": [
                "Increased rigidity",
                "Altered conformational adaptability"
            ],

            "severity": "Low",

            "score": 71
        },

        "POU5F1": {
            "role": "Stem cell pluripotency maintenance",
            "effect": "Potential influence on pluripotency regulation",
            "chemistry": [
                "Potential interaction instability",
                "Loss of phosphorylation compatibility"
            ],
            "severity": "Moderate"
        },

        "HIF1A": {
            "role": "Hypoxia response regulation",
            "effect": "Possible stress-response alteration",
            "chemistry": [
                "Hydrophobicity change",
                "Potential interface weakening"
            ],
            "severity": "Low"
        },

        "RPS6KB1": {
            "role": "mTOR-mediated protein synthesis",
            "effect": "Potential translational signaling disruption",
            "chemistry": [
                "Altered interaction dynamics"
            ],
            "severity": "Low"
        },

        "RPS6KB2": {
            "role": "Cell growth signaling",
            "effect": "Possible altered growth signaling",
            "chemistry": [
                "Minor local interaction changes"
            ],
            "severity": "Low"
        }
    }

    nodes = [
        Node(id="FOXA2", label="FOXA2", size=40),
        Node(id="SOX17", label="SOX17"),
        Node(id="HNF1A", label="HNF1A"),
        Node(id="PDX1", label="PDX1"),
        Node(id="OTX2", label="OTX2")
    ]

    edges = [
        Edge(source="FOXA2", target="SOX17"),
        Edge(source="FOXA2", target="HNF1A"),
        Edge(source="FOXA2", target="PDX1"),
        Edge(source="FOXA2", target="OTX2")
    ]

    config = Config(
        width='100%',
        height=380,
        directed=False,
        physics=True,
        nodeHighlightBehavior=True,
        highlightColor="#00f7ff"
    )

    left, right = st.columns([1.2,1.8])

    # -------------------------
    # LEFT = network
    # -------------------------
    with left:

        st.markdown("### Interaction Network")

        selected = agraph(
            nodes=nodes,
            edges=edges,
            config=config
        )

        st.caption(
            "Click a node to explore predicted FOXA2 interaction changes."
        )

    # -------------------------
    # RIGHT = analysis panel
    # -------------------------
    with right:

        if selected and selected in protein_data:

            # 3D docking model
            show_interaction_model(selected)

            st.markdown(
            """
            **Color key**  
            - Cyan: WT FOXA2 backbone / cartoon  
            - Orange: selected partner protein  
            - Magenta: FOXA2 S169 mapped mutation site  
            - Yellow/Lime sticks: predicted interface residues when visible
            """
            )

            info = protein_data[selected]

            # protein name
            st.markdown(f"## {selected}")

            # role
            st.info(
                f"Role: {info['role']}"
            )

            # consequence
            st.success(
                f"Predicted Consequence: {info['effect']}"
            )

            st.markdown(
                "### Interaction Mechanism"
            )

            st.write(
                info["mechanism"]
            )

            st.markdown(
                "### Predicted Docking Outcome"
            )

            st.warning(
                info["docking"]
            )

            # chemistry
            st.markdown(
                "### Chemical Interpretation"
            )

            for item in info["chemistry"]:
                st.write(f"- {item}")

            # severity
            st.markdown(
                "### Predicted Interaction Severity"
            )

            st.markdown(
                "### Predicted Interaction Stability"
            )

            score = info["score"]

            st.progress(score / 100)

            st.metric(
                label="Interaction Score",
                value=f"{score}/100"
            )

            if score >= 80:

                st.success(
                    "Stable interaction predicted"
                )

            elif score >= 50:

                st.warning(
                    "Moderate interaction disruption predicted"
                )

            else:

                st.error(
                    "High interaction disruption predicted"
                )

        else:

            st.info(
                "Select a protein node to explore predicted interaction changes."
            )

        st.markdown("---")

        st.subheader(
            "Predicted Molecular Consequences"
        )

        st.write("- Reduced hydrogen bonding")
        st.write("- Increased rigidity")
        st.write("- Loss of phosphorylation potential")
        st.write("- Possible altered interaction specificity")
        
# ---------------------------------
# BADGE
# ---------------------------------
st.markdown(
    f'''<div class="badge">
    <b>ACTIVE MUTATION</b><br>
    {st.session_state.mutation}
    </div>''',
    unsafe_allow_html=True
)



import streamlit as st
from stmol import showmol
import py3Dmol

st.title("test")

xyz = """
3
water
O 0.000 0.000 0.000
H 0.757 0.586 0.000
H -0.757 0.586 0.000
"""

view = py3Dmol.view(width=700, height=500)
view.addModel(xyz, "xyz")
view.setStyle({}, {"stick": {}})
view.zoomTo()

showmol(view)
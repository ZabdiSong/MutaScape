
import streamlit as st
import pandas as pd
from streamlit_agraph import agraph, Node, Edge, Config

import py3Dmol
import streamlit.components.v1 as components

import matplotlib.pyplot as plt
import numpy as np

# ---------------------------------
# PAGE CONFIG
# ---------------------------------
st.set_page_config(
    page_title="MutaScape",
    page_icon="🧬",
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

</style>
""", unsafe_allow_html=True)


# ---------------------------------
# SESSION STATE
# ---------------------------------
if "step" not in st.session_state:
    st.session_state.step = 0

if "mutation" not in st.session_state:
    st.session_state.mutation = "S169P"

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

def show_radar_chart(mt):

    labels = [
        "Polarity",
        "H-Bond",
        "Flexibility",
        "Phosphorylation",
        "Interaction Potential"
    ]

    # WT = Serine
    wt_values = [9, 9, 7, 10, 8]

    # mutant mapping
    mutant_map = {

        "P": [3, 1, 2, 0, 4],
        "A": [4, 1, 6, 0, 5],
        "F": [2, 1, 3, 0, 4],
        "G": [5, 1, 10, 0, 5],
        "Y": [8, 8, 4, 8, 7],
        "W": [3, 6, 3, 0, 5],
        "R": [9, 8, 7, 0, 8]
    }

    mt_values = mutant_map[mt]

    # close polygon
    wt_values += wt_values[:1]
    mt_values += mt_values[:1]

    angles = np.linspace(
        0,
        2*np.pi,
        len(labels),
        endpoint=False
    ).tolist()

    angles += angles[:1]

    fig, ax = plt.subplots(
        figsize=(4,4),
        subplot_kw=dict(polar=True)
    )

    ax.plot(
        angles,
        wt_values,
        linewidth=2,
        label="WT Serine"
    )

    ax.fill(
        angles,
        wt_values,
        alpha=0.25
    )

    ax.plot(
        angles,
        mt_values,
        linewidth=2,
        label=f"Mutant {mt}"
    )

    ax.fill(
        angles,
        mt_values,
        alpha=0.25
    )

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels)

    ax.set_ylim(0,10)

    ax.set_title(
        "Chemical Property Comparison",
        pad=20
    )

    ax.legend(
        loc="upper right"
    )

    st.pyplot(fig)

def show_protein(cif_path, residue_id=169, color="cyan"):

    with open(cif_path, "r", encoding="utf-8") as f:
        cif_data = f.read()

    view = py3Dmol.view(
        width=500,
        height=500
    )

    # load cif
    view.addModel(
        cif_data,
        "cif"
    )

    # protein structure
    view.setStyle(
        {},
        {
            "cartoon": {
                "color": color
            }
        }
    )

    # mutation highlight
    view.setStyle(
        {"resi": str(residue_id)},
        {
            "stick": {
                "colorscheme": "yellowCarbon",
                "radius": 0.3
            }
        }
    )

    # zoom whole protein first
    view.zoomTo()

    view.setBackgroundColor("#0B1020")

    html = view._make_html()

    components.html(
        html,
        height=520,
        width=520
    )

def show_alignment(wt_path, mut_path, residue_id=231):

    with open(wt_path, "r", encoding="utf-8") as f:
        wt_data = f.read()

    with open(mut_path, "r", encoding="utf-8") as f:
        mut_data = f.read()

    view = py3Dmol.view(
        width=1400,
        height=850
    )

    # WT
    view.addModel(wt_data, "mmcif")

    view.setStyle(
        {"model": 0},
        {
            "cartoon": {
                "color": "cyan",
                "opacity": 0.7
            }
        }
    )

    # MUT
    view.addModel(mut_data, "mmcif")

    view.setStyle(
        {"model": 1},
        {
            "cartoon": {
                "color": "magenta",
                "opacity": 0.7
            }
        }
    )

    # highlight mutation
    for model_id in [0, 1]:

        view.addStyle(
            {
                "model": model_id,
                "resi": str(residue_id)
            },
            {
                "stick": {
                    "color": "yellow",
                    "radius": 0.35
                },
                "sphere": {
                    "radius": 0.7,
                    "color": "yellow"
                }
            }
        )

    # FIT TO BOTH PROTEINS
    view.zoomTo()

    # force enlarge
    view.zoomTo()
    view.zoom(1.2)

    view.setBackgroundColor("#0B1020")

    components.html(
        view._make_html(),
        height=860
    )

def show_dna_binding(cif_path, residue_id=231):

    with open(cif_path, "r", encoding="utf-8") as f:
        cif_data = f.read()

    view = py3Dmol.view(
        width=1000,
        height=550
    )

    view.addModel(cif_data, "cif")

    # ----------------
    # FOXA2 protein
    # ----------------
    view.setStyle(
        {"chain": "A"},
        {
            "cartoon": {
                "color": "cyan"
            }
        }
    )

    # ----------------
    # DNA chain C
    # ----------------
    view.setStyle(
        {"chain": "C"},
        {
            "cartoon": {
                "color": "red"
            }
        }
    )

    # ----------------
    # DNA chain D
    # ----------------
    view.setStyle(
        {"chain": "D"},
        {
            "cartoon": {
                "color": "red"
            }
        }
    )

    # ----------------
    # Mutation residue
    # ----------------
    view.setStyle(
        {"resi": str(residue_id)},
        {
            "stick": {
                "colorscheme": "yellowCarbon",
                "radius": 0.35
            },
            "sphere": {
                "radius": 0.55,
                "color": "yellow"
            }
        }
    )

    # zoom
    view.zoomTo()

    view.setBackgroundColor("#0B1020")

    html = view._make_html()

    components.html(
        html,
        height=580,
        width=1100
    )

def show_interaction_model(protein_name):

    view = py3Dmol.view(
        width=550,
        height=420
    )

    # ----------------
    # FOXA2
    # ----------------
    with open(
        r"C:\Users\Szq\Desktop\MutaScape\assets\foxa2_wt.cif",
        "r",
        encoding="utf-8"
    ) as f:
        foxa2_data = f.read()

    view.addModel(
        foxa2_data,
        "cif"
    )

    view.addStyle(
        {"model": 0},
        {
            "cartoon": {
                "color": "cyan",
                "opacity": 0.75
            }
        }
    )

    view.zoomTo()

    # mutation site
    view.setStyle(
        {
            "model": 0,
            "resi": "231"
        },
        {
            "sphere": {
                "color": "magenta",
                "radius": 0.8
            },
            "stick": {
                "color": "yellow"
            }
        }
    )

    # ----------------
    # partner protein
    # ----------------
    partner_path = rf"C:\Users\Szq\Desktop\MutaScape\assets\{protein_name.lower()}.cif"

    with open(
        partner_path,
        "r",
        encoding="utf-8"
    ) as f:
        partner_data = f.read()

    view.addModel(
        partner_data,
        "cif"
    )

    view.setStyle(
        {"model": 1},
        {
            "cartoon": {
                "color": "orange",
                "opacity": 0.75
            }
        }
    )

    # ----------------
    # predicted interface residues
    # ----------------
    interface_sites = {

        "SOX17": {
            "foxa2": [225,226,227,228,229],
            "partner": [45,46,47]
        },

        "PDX1": {
            "foxa2": [230,231,232,233],
            "partner": [110,111,112]
        },

        "HNF1A": {
            "foxa2": [180,181,182],
            "partner": [88,89]
        },

        "OTX2": {
            "foxa2": [250,251,252],
            "partner": [72,73]
        }
    }

    if protein_name in interface_sites:

        # FOXA2 interface
        for r in interface_sites[protein_name]["foxa2"]:

            view.addStyle(
                {
                    "model": 0,
                    "resi": str(r)
                },
                {
                    "stick": {
                        "color": "yellow"
                    }
                }
            )

        # partner interface
        for r in interface_sites[protein_name]["partner"]:

            view.addStyle(
                {
                    "model": 1,
                    "resi": str(r)
                },
                {
                    "stick": {
                        "color": "lime"
                    }
                }
            )

    view.zoomTo()

    view.setBackgroundColor(
        "#0B1020"
    )

    components.html(
        view._make_html(),
        height=430
    )

# ---------------------------------
# HEADER
# ---------------------------------
st.markdown('<div class="title">MutaScape</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtitle">Structural • DNA Binding • Molecular Interaction</div>',
    unsafe_allow_html=True
)

# ---------------------------------
# TOP NAVIGATION
# ---------------------------------
col1,col2,col3 = st.columns(3)

with col1:
    if st.button("① STRUCTURE"):
        st.session_state.step = 1

with col2:
    if st.button("② DNA INTERFACE"):
        st.session_state.step = 2

with col3:
    if st.button("③ NETWORK"):
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
            ["A","P","F","G","Y","W","R"]
        )

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
        st.write(f"• {item}")

    if st.button("🚀 START EXPLORATION"):
        st.session_state.step = 1
        st.rerun()

# ---------------------------------
# STEP 1 STRUCTURE
# ---------------------------------
if st.session_state.step == 1:

    st.header("Step 1 — Structural Consequence")

    left, right = st.columns(2)

    with left:
        st.markdown("### Wild Type Structure")

        show_protein(
            r"C:\Users\Szq\Desktop\MutaScape\assets\foxa2_wt.cif",
            residue_id=231,
            color="cyan"
        )

    with right:
        st.markdown("### Mutant Structure")

        show_protein(
            r"C:\Users\Szq\Desktop\MutaScape\assets\foxa2_s169p.cif",
            residue_id=231,
            color="magenta"
        )

    # --------------------
    # alignment viewer
    # --------------------
    st.markdown("---")

    st.subheader("Structural Alignment")

    show_alignment(
        r"C:\Users\Szq\Desktop\MutaScape\assets\foxa2_wt.cif",
        r"C:\Users\Szq\Desktop\MutaScape\assets\foxa2_s169p.cif",
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
            f'<p class="rmsd-low">RMSD = {rmsd} | Low Structural Disruption</p>',
            unsafe_allow_html=True
        )
    elif rmsd < 1.5:
        st.markdown(
            f'<p class="rmsd-mid">RMSD = {rmsd} | Moderate Structural Disruption</p>',
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            f'<p class="rmsd-high">RMSD = {rmsd} | High Structural Disruption</p>',
            unsafe_allow_html=True
        )

    st.write(
        "Predicted minimal structural disruption. Functional effects may instead arise from altered molecular interactions."
    )

    st.subheader("Chemical Property Change")

    df = pd.DataFrame([
        ["Polarity", aa_data["S"]["polarity"], aa_data["P"]["polarity"]],
        ["Hydrogen Bond", aa_data["S"]["hydrogen"], aa_data["P"]["hydrogen"]],
        ["Flexibility", aa_data["S"]["flexibility"], aa_data["P"]["flexibility"]],
        ["Phosphorylation", aa_data["S"]["phosphorylation"], aa_data["P"]["phosphorylation"]]
    ], columns=["Property", "WT", "Mutant"])

    st.table(df)

    if st.button("Next → DNA Binding", key="step1_next"):
        st.session_state.step = 2
        st.rerun()


# ---------------------------------
# STEP 2 DNA
# ---------------------------------
if st.session_state.step == 2:

    st.header("Step 2 — DNA Binding Site")

    show_dna_binding(
        r"C:\Users\Szq\Desktop\MutaScape\assets\foxa2_dna.cif",
        residue_id=231
    )

    st.markdown("---")

    st.subheader("DNA-binding Interpretation")

    st.error("🔴 DNA-binding domain highlighted")

    st.warning("🟡 Mutation residue highlighted")

    st.success(
        "Residue S169 (mapped to structural residue 231) is located outside the DNA-binding interface, suggesting limited direct disruption to DNA binding."
    )

    st.write(
        "The functional consequence may instead arise through altered protein-protein interactions or local chemical property changes."
    )

    st.info(
        "Serine → Proline substitution reduces hydrogen bonding potential and increases local rigidity."
    )

    st.markdown("---")

    c1, c2 = st.columns(2)

    with c1:
        if st.button("← Back", key="dna_back"):
            st.session_state.step = 1
            st.rerun()

    with c2:
        if st.button("Next → Network", key="dna_next"):
            st.session_state.step = 3
            st.rerun()
    

# ---------------------------------
# STEP 3 NETWORK
# ---------------------------------

if st.session_state.step == 3:

    st.header("Step 3 — Molecular Interaction Network")

    st.info(
        """
    Hypothesis:
    FOXA2 S169P may not strongly alter global structure
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
            "The S169P substitution may reduce interaction adaptability near FOXA2 regulatory interfaces important for pancreatic transcriptional complexes.",

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
            "FOXA2 S169P removes a polar hydroxyl group, reducing hydrogen bonding compatibility with SOX17 and increasing local rigidity near the predicted interaction surface.",

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
            🟦 **FOXA2**  
            🟧 **Partner Protein**  
            🟪 **Mutation Site (S169P)**  
            🟨 **Predicted FOXA2 Interface**  
            🟩 **Predicted Partner Interface**
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
                st.write(f"• {item}")

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

        st.write("• Reduced hydrogen bonding")
        st.write("• Increased rigidity")
        st.write("• Loss of phosphorylation potential")
        st.write("• Possible altered interaction specificity")
        
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



# MutaScape

**An interactive FOXA2 research explorer and environmental pressure teaching board.**

MutaScape grew from a student computational study into a molecular visualization prototype and a physical exhibition board. This browser edition brings the supplied research documents, seven structures, original Python programs and board simulation together.

## Explore

- **Structure:** rotate actual coordinates, compare WT and the supplied proline model, select an alignment window, inspect residue 231 and view Cα displacement.
- **DNA:** inspect the supplied 5X07-derived complex and near-atom distances.
- **Network:** explore four associations from the prototype and their separate partner structures.
- **Pressure board:** vary a teaching input, switch WT/mutant, cycle chemistry scenarios, inspect the score equation and export recorded snapshots.
- **Research & files:** read the paper, scientific poster and slide PDF, view exhibition photos and download the original sources.

## Evidence status

The original research is titled **FOXA2 S169P Variant**. The supplied 457-residue models differ at **SER231 → PRO231**; their residue 169 is THR. A reference transcript/protein version and sequence alignment are required before claiming that the two labels refer to the same variant. The structure panels therefore use **S231P (supplied model)**.

The paper's reported RMSD values are kept separate from the new reproducible Cα fits. Manual chemistry weights and environmental inputs generate **teaching indices**, not biological probabilities or validated mutation-effect predictions. Individual partner structures are not docked complexes. No project-specific wet-lab iPSC data were supplied.

Read [methods and evidence](docs/methods.md) or [材料核对（中文）](docs/研究核对_中文.md).

## Open locally

Extract the entire package, then open **index.html** in Chrome, Edge, Firefox or Safari with WebGL enabled. All required scripts, coordinates and rendering software are bundled. There is no npm install, server application, login or API key.

For a local HTTP preview, run this from the project folder:

```sh
python3 -m http.server 8000
```

Then open `http://localhost:8000`. Ordinary exploration also works from `file://`; optional physical Web Serial uses a supported secure context.

## Upload to GitHub Pages

1. Put the **contents of this folder** in a repository. `index.html` must be at the publishing root.
2. Commit and push with GitHub Desktop, or upload the files with GitHub's interface. Keep the folder structure.
3. In repository Settings → Pages, choose Deploy from a branch → main → /(root) → Save.
4. After deployment, copy the actual **Visit site** URL. Share that URL for the website; share the repository URL for the source.

See [GitHub 上传说明（中文）](docs/GitHub上传说明_中文.md). The package itself is not published by downloading or opening it.

## Optional physical board

The browser simulator needs no hardware. Web Serial is an optional user-initiated connection at 115200 baud. The two output profiles send commands understood by the corresponding uploaded firmware. There is no automatic physical servo control or pin scan.

Read [hardware compatibility](hardware/接线与兼容性_中文.md) before choosing a firmware profile. Firmware files in `original-code/` are preserved as supplied and are not newly flashed or physically tested here.

## Project files

| Path | Contents |
|---|---|
| `index.html`, `css/`, `js/` | Static browser app |
| `data/models.js` | Derived offline coordinates, PDB strings and fitted model positions |
| `data/structure-audit.json`, `data/rmsd-results.csv` | Current reproducible results |
| `assets/structures/` | Seven original CIF files |
| `assets/research/` | Three original PDFs and derived preview thumbnails |
| `assets/photos/` | Two original exhibition photographs |
| `original-code/` | Seven original Python files |
| `hardware/`, `docs/` | Usage, evidence checks and remaining research needs |
| `tools/rebuild_data.py` | Rebuild coordinate data and Kabsch results; requires NumPy |
| `tools/verify_engine.cjs` | Tests for scoring, serial events and data invariants; requires Node |
| `source-inventory.json` | Original-file mapping and SHA-256 hashes |
| `vendor/` | Bundled 3Dmol.js with its license |

## Reproduce the derived data

```sh
python3 -m pip install numpy
python3 tools/rebuild_data.py
node tools/verify_engine.cjs
```

These developer commands are unnecessary for viewing the website. The original Streamlit applications are research prototypes and do not run on GitHub Pages; they remain downloadable for source inspection.

## Sources and credits

- [UniProt human FOXA2 — Q9Y261](https://www.uniprot.org/uniprotkb/Q9Y261/entry)
- [RCSB PDB 5X07](https://www.rcsb.org/structure/5X07)
- [Giri et al., 2017](https://doi.org/10.1093/hmg/ddx318)
- [Li et al., 2017](https://doi.org/10.1021/acs.biochem.7b00211)
- [STRING](https://string-db.org/help/faq/) and [AlphaFold confidence guidance](https://alphafold.ebi.ac.uk/faq)
- [3Dmol.js](https://3dmol.org/) — bundled BSD-3-Clause renderer; full notices in `vendor/3Dmol-LICENSE.txt`

Original materials retain their authorship and existing terms. AlphaFold Server CIF files retain their output-terms notice. No new license is imposed on the user's research or code.

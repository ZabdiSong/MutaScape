# MutaScape: methods and evidence check

Audit date: 6 October 2026. Inputs: seven supplied Python files, seven CIF files, three PDFs and two exhibition photographs.

## 1. Sequence identity and numbering

The supplied WT and proline models have 457 matched Cα residues. Their only sequence difference is WT **SER231** versus mutant **PRO231**. Both have THR169. The WT model sequence matches the displayed 457-aa human FOXA2 sequence in UniProt Q9Y261.

The source paper identifies Q9Y262 as FOXA2. UniProt Q9Y262 instead identifies eukaryotic translation initiation factor 3 subunit L (EIF3L). The source claim that S169 maps to 231 through a 62-aa extension cannot be verified without its original reference sequence/version and alignment. The website retains S169P only as the original research title and labels the actual uploaded model S231P. It does not assert that the published S169P variant is equivalent or that the original variant nomenclature is wrong.

Giri et al. (2017) describe their S169P variant as within the DNA-binding domain and report functional experiments. Their experiments are background literature, not experiments conducted by this project. Exact variant comparisons require reference-specific mapping.

Primary records: [Q9Y261](https://rest.uniprot.org/uniprotkb/Q9Y261.txt), [Q9Y262](https://rest.uniprot.org/uniprotkb/Q9Y262.txt), [Giri et al.](https://doi.org/10.1093/hmg/ddx318).

## 2. CIF parsing and model rendering

`tools/rebuild_data.py` parses the `_atom_site` loop by header name, retaining author chain/residue IDs, atom coordinates, occupancy and B/pLDDT values. It uses the first model and primary conformer, and rejects incomplete atom rows. The parser is scoped to the supplied atom loops; it is not a general-purpose parser for every mmCIF category.

Offline PDB strings are derived for rendering. The original CIF bytes remain unchanged. Molecular geometry comes from uploaded coordinates; the environment slider never deforms it. 3Dmol infers intra-model covalent connectivity for ordinary visual rendering. No protein–DNA or protein–partner bond is introduced by the pressure simulator.

Only the proline mutant has a supplied coordinate file. Alanine and glycine selections are chemistry scenarios: the viewer clearly shows a WT reference, and no RMSD or displacement curve is generated for them.

## 3. Cα structural comparison

WT and mutant Cα positions are matched by author residue number. Each inclusive window is fitted separately using the Kabsch least-squares rotation and translation. The determinant correction prevents a reflection. Every matched Cα participates; no outlier rejection is applied.

RMSD = square root of the mean squared Euclidean distance between fitted mutant and WT Cα coordinates, in Å. The displacement plot shows each matched Cα distance after that fit. Overlay coordinates use the corresponding window's transform.

| Inclusive range | Matched Cα | Aligned RMSD / Å | Source paper report / Å |
|---|---:|---:|---:|
| 1–457 | 457 | 17.512283 | Not supplied |
| 132–330 | 199 | 4.340946 | 0.321 |
| 182–280 | 99 | 0.364130 | 0.097 |
| 159–252 | 94 | 0.211822 | Not supplied |

The source values cannot currently be reproduced under this method. PyMOL may use other atom selections, iterative rejection or model versions; this audit does not identify which factor caused the discrepancy. Need the original structures and exact commands/logs to reproduce the source calculation. Other 18 mutant structures were not supplied, so the claim that P has the smallest RMSD among 19 substitutions is not re-tested.

Whole-model comparisons include low-confidence regions. A large predicted-coordinate difference is not proof of instability; a small local RMSD is not proof of preserved function. Model mean Cα pLDDT is 50.234 for WT and 48.460 for the proline model. Residue 231 values are 95.75 and 95.59. The source's different mean (56.69) is not assigned to these uploaded structures.

## 4. DNA complex

The uploaded `foxa2_dna.cif` is a selected/edited export with entry name XXXX and a title/citation corresponding to 5X07. It contains author chains D and E (DNA) and F (protein); the 85 modeled Cα positions span author residues 155–239. It is not the full four-copy asymmetric unit in the public 5X07 entry.

Author F:231 is SER and label residue 77. It exists within the modeled protein fragment. The source prototype's chain assumptions (A/B/C) and its hardcoded residue 15 do not identify this site correctly.

All heavy-atom pairs between F:SER231 and DNA D/E were evaluated in the supplied positions. Six pairs are less than 4 Å. The shortest is F:SER231:N to D:DG5:OP1, **2.421288 Å**. This is coordinate geometry; it does not establish a hydrogen bond, energetic affinity or the effect of the mutation. The structure contains WT serine, not a modeled mutant–DNA complex.

The structural publication discusses DNA contacts involving Ser231/Trp233. The assertion that residue 231 is outside the DNA-binding region must not be retained. This does not resolve the original S169 reference-numbering question.

Sources: [5X07](https://www.rcsb.org/structure/5X07), [Li et al.](https://doi.org/10.1021/acs.biochem.7b00211).

## 5. Chemistry and teaching scores

Chemical descriptions distinguish side-chain OH loss from all hydrogen-bonding ability. Proteins retain other backbone/side-chain donor or acceptor groups. Proline changes backbone geometry and lacks the usual backbone amide hydrogen in an internal peptide residue. Loss of a serine OH removes its possible modification chemistry, but this does not establish that residue 231 is an experimentally phosphorylated site.

The main source function assigns manually chosen weights:

| Condition | Structure channel | DNA channel | Network channel |
|---|---:|---:|---:|
| Proline backbone constraint | 30 | 0 | 15 |
| Side-chain polarity change | 15 | 10 | 15 |
| Serine OH loss | 20 | 15 | 20 |
| Loss of serine OH modification potential | 0 | 0 | 20 |

Thus P = **65 / 25 / 70**; A and G = **35 / 25 / 55**. These are illustrative channel baselines from the prototype. The original alternative custom-profile function used different weights (P = 60 / 25 / 67); the browser uses only the main preset engine and does not retain that inconsistent second scoring route. The legacy arbitrary numerical radar is replaced with a qualitative side-chain diagram.

The board adds `floor(environment_input × 0.25)` and 25 when contact simulation is enabled, then caps at 100. WT view uses a zero chemistry baseline (an explicit browser teaching convention). Compare view uses the mutant baseline. Bands: <40 green; 40–69 yellow; ≥70 red. LED count uses floor(index ×25/100); servo image angle is WT 0° / mutant 180°.

No weights were fitted to biochemical data. These are **teaching indices**, never percentages of pathogenicity, calibrated fitness, predicted protein stability or measured DNA/network effects. The environmental input may represent sensor intensity, not measured cellular stress. Contact is a pedagogical toggle, not detected molecular binding.

## 6. Network and partner models

The source code supplies four FOXA2 links: SOX17, HNF1A, PDX1 and OTX2. The browser preserves those four as a selected functional-association schematic. A complete 31-edge export was not provided, so the reported 11-node / 31-edge network is not reconstructed from assumptions.

STRING associations can include indirect functional evidence; an edge does not automatically establish physical binding. Partner models are shown individually, with **no docking** and no invented interface residues. HNF1A is only a 119-residue fragment. Hardcoded partner scores (42/64/71/78) and claimed docking outcomes from the prototype are not used as scientific predictions.

Source: [STRING evidence guidance](https://string-db.org/help/faq/).

## 7. Hardware and storage

Browser controls fully support the teaching demo without hardware. Optional Web Serial is a user-initiated connection at 115200 baud; inputs are applied only when Use live inputs is on. Output requires an explicit Send action. No servo, RGB or pin-scan commands are sent.

Only explicit CONTACT packets control contact state. Raw P1 diagnostics have inconsistent polarity across supplied firmware and are not interpreted as molecular contact. Plain A/B bursts are deduplicated with a 500-ms quiet gap; sequence-numbered events are deduplicated by sequence. Plain bursts cannot distinguish all rapid repeated physical presses; sequence-numbered firmware is the better future protocol.

Recorded scenarios stay in browser local storage when available (up to 100), with JSON export. They are local teaching scenarios, not uploaded research measurements. No analytics, accounts, cloud database or background network calls are present.

Physical board operation is not verified here. See [hardware notes](../hardware/接线与兼容性_中文.md).

## 8. What remains to establish

- Reference-specific S169P mapping, including accession and version.
- Original model versions, all 19 mutant files and exact fit commands.
- Complete STRING edges and evidence export.
- Experimentally tested DNA/PPI/differentiation consequences.
- Confirmed servo wiring and a compatible firmware implementation.

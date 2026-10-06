#!/usr/bin/env python3
"""Rebuild offline viewer data from the seven supplied mmCIF files.
Requires numpy. Header-based parsing supports atom loops in supplied files;
it rejects incomplete records rather than guessing fixed column positions.
Rigid least-squares fitting uses all matched C-alpha atoms, no outlier pruning.
"""
from pathlib import Path
import shlex, json, hashlib, csv
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
AA=dict(zip('ALA ARG ASN ASP CYS GLN GLU GLY HIS ILE LEU LYS MET PHE PRO SER THR TRP TYR VAL'.split(),'ARNDCQEGHILKMFPSTWYV'))

def parse_atoms(path):
    lines=Path(path).read_text().splitlines(); out=[]
    for i,line in enumerate(lines):
        if line.strip()!='loop_' or i+1>=len(lines) or not lines[i+1].strip().startswith('_atom_site.'): continue
        j=i+1; cols=[]
        while j<len(lines) and lines[j].strip().startswith('_atom_site.'):
            cols.append(lines[j].strip());j+=1
        for row in lines[j:]:
            row=row.strip()
            if row.startswith(('#','_','loop_','data_')):break
            if not row:continue
            vals=shlex.split(row)
            if len(vals)!=len(cols): raise ValueError(f'Incomplete atom record: {path.name}: {row[:60]}')
            a=dict(zip(cols,vals));g=lambda k,default='':a.get('_atom_site.'+k,default)
            if g('pdbx_PDB_model_num','1')!='1' or g('label_alt_id','.') not in ['.','?','A']:continue
            seq=g('auth_seq_id',g('label_seq_id'))
            if seq in ['.','?']:continue
            out.append({'record':g('group_PDB'),'name':g('label_atom_id'),'element':g('type_symbol'),'resn':g('label_comp_id'),'chain':g('auth_asym_id',g('label_asym_id')),'labelChain':g('label_asym_id'),'resi':int(seq),'labelResi':g('label_seq_id'),'xyz':[float(g('Cartn_'+k)) for k in 'xyz'],'b':float(g('B_iso_or_equiv','0')),'occupancy':float(g('occupancy','1'))})
    if not out: raise ValueError('No atoms in '+str(path))
    return out

def ca(atoms):return {a['resi']:a for a in atoms if a['name']=='CA' and a['resn'] in AA}
def fit(wt,mt,lo,hi):
    w,m=ca(wt),ca(mt);rs=sorted(i for i in w.keys()&m.keys() if lo<=i<=hi)
    if len(rs)<3:raise ValueError('At least three matched C-alpha atoms are required')
    P=np.array([m[i]['xyz'] for i in rs]);Q=np.array([w[i]['xyz'] for i in rs]);pc=P.mean(0);qc=Q.mean(0)
    U,_,V=np.linalg.svd((P-pc).T@(Q-qc));D=np.eye(3);D[2,2]=np.linalg.det(U@V);R=U@D@V
    fitted=(P-pc)@R+qc;dev=np.linalg.norm(fitted-Q,axis=1)
    metric={'range':[lo,hi],'n':len(rs),'rmsd':float(np.sqrt(np.mean(dev**2))),'rawRmsd':float(np.sqrt(np.mean(np.sum((P-Q)**2,axis=1)))),'residueDeviations':[[i,round(float(d),4)] for i,d in zip(rs,dev)]}
    aligned=[dict(a,xyz=[round(float(v),5) for v in ((np.array(a['xyz'])-pc)@R+qc)]) for a in mt]
    return metric,aligned

def pdb(atoms):
    rows=[]
    for i,a in enumerate(atoms,1):
        atom=a['name'][:4]; atom=atom.rjust(4) if len(a['element'])==1 else atom.ljust(4)
        x,y,z=a['xyz'];rows.append(f"{a['record']:<6}{i:5d} {atom} {a['resn']:>3} {a['chain'][:1]}{a['resi']:4d}    {x:8.3f}{y:8.3f}{z:8.3f}{a['occupancy']:6.2f}{a['b']:6.2f}          {a['element']:>2}")
    return '\n'.join(rows)+'\nEND\n'

def main():
    models={}
    for path in sorted((ROOT/'assets/structures').glob('*.cif')):
        atoms=parse_atoms(path);back=ca(atoms);is_dna=path.stem=='foxa2_dna'
        models[path.stem]={'file':'assets/structures/'+path.name,'atoms':atoms,'pdb':pdb(atoms),'caCount':len(back),'atomCount':len(atoms),'sequence':''.join(AA[a['resn']] for a in back.values()),'meanConfidence':None if is_dna else float(np.mean([a['b'] for a in back.values()])),'confidenceKind':'B factor (Å²)' if is_dna else 'pLDDT','sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
    w=models['foxa2_wt']['atoms'];m=models['foxa2_s169p']['atoms'];wc,mc=ca(w),ca(m)
    changes=[{'resi':i,'wt':wc[i]['resn'],'mutant':mc[i]['resn']} for i in wc if wc[i]['resn']!=mc[i]['resn']]
    metrics={};aligned={}
    for key,lo,hi in [('full',1,457),('wide',132,330),('local',182,280),('dnaDomain',159,252)]:
        metric,a=fit(w,m,lo,hi);metrics[key]=metric;aligned[key]=pdb(a)
    d=models['foxa2_dna']['atoms'];site=[a for a in d if a['chain']=='F' and a['resi']==231];dna=[a for a in d if a['chain'] in ['D','E'] and a['resn'] in ['DA','DC','DG','DT']]
    pairs=[]
    for a in site:
        for b in dna:
            dist=float(np.linalg.norm(np.array(a['xyz'])-b['xyz']))
            if dist<4:pairs.append({'proteinAtom':a['name'],'dnaChain':b['chain'],'dnaResi':b['resi'],'dnaResn':b['resn'],'dnaAtom':b['name'],'distance':dist,'proteinXYZ':a['xyz'],'dnaXYZ':b['xyz']})
    pairs.sort(key=lambda p:p['distance'])
    audit={'date':'2026-10-06','changes':changes,'reportedRmsd':{'wide':.321,'local':.097},'metrics':metrics,'dnaContactsUnder4A':pairs,'canonicalAccession':'Q9Y261','unverifiedProjectLabel':'S169P','actualSuppliedSubstitution':'S231P','siteConfidence':{'wt':wc[231]['b'],'mutant':mc[231]['b']},'method':'All matched C-alpha atoms; Kabsch least-squares rigid alignment within each inclusive residue window; no outlier rejection; coordinates in Å.'}
    data={'models':models,'aligned':aligned,'audit':audit}
    (ROOT/'data/models.js').write_text('window.MUTA_DATA='+json.dumps(data,separators=(',',':'))+';\n')
    (ROOT/'data/structure-audit.json').write_text(json.dumps(audit,indent=2))
    with (ROOT/'data/rmsd-results.csv').open('w',newline='') as f:
        writer=csv.writer(f);writer.writerow(['window','start','end','matched_CA','aligned_RMSD_A','raw_RMSD_A','method'])
        for k,v in metrics.items():writer.writerow([k,*v['range'],v['n'],v['rmsd'],v['rawRmsd'],audit['method']])
    print(json.dumps({k:round(v['rmsd'],6) for k,v in metrics.items()}));print('Changes',changes);print('DNA close contacts',len(pairs), 'closest',pairs[0] if pairs else None)

if __name__=='__main__':main()

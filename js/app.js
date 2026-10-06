(function(){
'use strict';
const D=window.MUTA_DATA,E=window.MutaEngine,$=s=>document.querySelector(s),$$=s=>Array.from(document.querySelectorAll(s));
const C={wt:'#70e6d4',mut:'#f297b8',site:'#f4ce77',D:'#edaa70',E:'#b9a4fa',F:'#70e6d4'};
const state={mutation:'P',view:'Mutant',pressure:0,contact:false,mode:'Structure',pot:0,fit:'local',crop:true,style:'cartoon',confidence:false,partner:'SOX17',route:'explore',distance:false};
let snapshots=[];try{const raw=JSON.parse(localStorage.getItem('mutascape-snapshots-v1')||'[]');if(Array.isArray(raw))snapshots=raw.filter(r=>r.type==='MutaScape teaching scenario'&&Number.isFinite(r.value)).slice(-100);}catch(_){}
let toastTimer,serialPort=null,serialReader=null,serialWriter=null,serialRunning=false,serialBusy=false;
const decoder=new E.SerialDecoder();let serialLog=[];const viewers={};
function toast(s){$('#toast').textContent=s;$('#toast').classList.add('show');clearTimeout(toastTimer);toastTimer=setTimeout(()=>$('#toast').classList.remove('show'),3600);}
function download(name,content,type='application/json'){const url=URL.createObjectURL(new Blob([content],{type}));const a=document.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),2000);}
function escape(s){return String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
function table(headers,rows){return '<table><thead><tr>'+headers.map(h=>'<th scope="col">'+escape(h)+'</th>').join('')+'</tr></thead><tbody>'+rows.map(r=>'<tr>'+r.map(c=>'<td>'+c+'</td>').join('')+'</tr>').join('')+'</tbody></table>';}
function route(){const candidate=location.hash.replace('#','')||'explore';state.route=['explore','structure','dna','network','board','research'].includes(candidate)?candidate:'explore';$$('.page').forEach(p=>p.hidden=p.id!=='page-'+state.route);$$('[data-route]').forEach(a=>{const active=a.dataset.route===state.route;a.classList.toggle('active',active);if(active)a.setAttribute('aria-current','page');else a.removeAttribute('aria-current');});
 if(['structure','dna','network'].includes(state.route)){state.mode={structure:'Structure',dna:'DNA',network:'Network'}[state.route];state.pot=E.MODES.indexOf(state.mode)*342;}
 updateControls();requestAnimationFrame(()=>{if(state.route==='structure')renderStructure();if(state.route==='dna')renderDNA();if(state.route==='network')renderPartner();});}
function updateControls(){
 $('#mutation-title').textContent='S231'+state.mutation;$('#mutation-name').textContent='Serine → '+E.AA[state.mutation].name;$('#mutation').value=state.mutation;$('#pressure').value=state.pressure;$('#pressure-value').textContent=state.pressure+' / 100';$('#contact').checked=state.contact;
 $$('[data-view]').forEach(b=>{const a=b.dataset.view===state.view;b.classList.toggle('active',a);b.setAttribute('aria-pressed',String(a));});
 const scores=E.MODES.map(mode=>E.teaching(state.mutation,state.view,state.pressure,state.contact,mode).value);
 $('#score-bars').innerHTML=E.MODES.map((mode,i)=>'<div class="score-bar"><div class="label-row"><span>'+mode+'</span><output>'+scores[i]+' / 100</output></div><div class="track"><i style="width:'+scores[i]+'%"></i></div></div>').join('');
 updateChemistry();updateBoard();
 if(state.route==='structure')updateStructureMetrics();
}
function updateAll(render=true){updateControls();if(render&&state.route==='structure')renderStructure();if(render&&state.route==='dna')renderDNA();}
function setMutation(v){state.mutation=v;updateAll();}
function cycle(){const order=['A','G','P'];state.mutation=order[(order.indexOf(state.mutation)+1)%3];updateAll();}
function toggleView(){state.view=state.view==='WT'?'Mutant':'WT';updateAll();}
function updateChemistry(){
 const trait=E.AA[state.mutation];const p=state.mutation==='P';
 const wt='<g transform="translate(48 62)"><text x="5" y="-25" fill="#70e6d4" font-size="10">WT / SERINE</text><text x="0" y="23" fill="#bdd7d7" font-size="15">Cα</text><path d="M26 17H64M93 17H128" stroke="#7babb0" stroke-width="2"/><text x="64" y="23" fill="#e6f3f2" font-size="15">CH₂</text><text x="130" y="23" fill="#70e6d4" font-size="15">OH</text><text x="3" y="62" fill="#8dabba" font-size="9">polar side-chain hydroxyl</text></g>';
 let mt;
 if(p)mt='<g transform="translate(286 48)"><text x="0" y="-11" fill="#f297b8" font-size="10">PROLINE</text><path d="M44 20L80 18L98 54L62 78L28 52Z" fill="#f297b811" stroke="#af7a97" stroke-width="2"/><circle cx="44" cy="20" r="13" fill="#122330"/><circle cx="80" cy="18" r="13" fill="#122330"/><circle cx="98" cy="54" r="13" fill="#122330"/><circle cx="62" cy="78" r="13" fill="#122330"/><circle cx="28" cy="52" r="13" fill="#122330"/><text x="36" y="25" fill="#f297b8" font-size="12">N</text><text x="70" y="22" fill="#d8c7d4" font-size="12">Cα</text><text x="88" y="58" fill="#d8c7d4" font-size="12">Cβ</text><text x="52" y="82" fill="#d8c7d4" font-size="12">Cγ</text><text x="18" y="56" fill="#d8c7d4" font-size="12">Cδ</text><text x="0" y="111" fill="#8dabba" font-size="9">ring constrains the backbone</text></g>';
 else mt='<g transform="translate(295 62)"><text x="0" y="-25" fill="#f297b8" font-size="10">'+trait.name.toUpperCase()+'</text><text x="0" y="23" fill="#bdd7d7" font-size="15">Cα</text><path d="M26 17H67" stroke="#aa849b" stroke-width="2"/><text x="70" y="23" fill="#f297b8" font-size="15">'+(state.mutation==='A'?'CH₃':'H')+'</text><text x="0" y="62" fill="#8dabba" font-size="9">serine OH group removed</text></g>';
 $('#chemistry-diagram').innerHTML='<svg viewBox="0 0 480 180" role="img" aria-label="Qualitative side-chain comparison between serine and '+trait.name+'">'+wt+'<path d="M238 79h26m-5-4 5 4-5 4" stroke="#789aab" fill="none"/>'+mt+'</svg>';
 $('#chemistry-traits').innerHTML='<div>'+trait.polarity+'<span>SIDE-CHAIN CLASS</span></div><div>No serine OH<span>HYDROXYL CHANGE</span></div><div>'+(p?'Ring constraint':state.mutation==='G'?'Greater freedom':'Methyl side chain')+'<span>GEOMETRIC DIFFERENCE</span></div>';
}
function makeViewer(id){
 if(viewers[id]){viewers[id].resize?.();return viewers[id];}
 const target=$('#'+id);target.innerHTML='';
 try{if(!window.$3Dmol)throw new Error('The local molecular renderer is missing.');const v=$3Dmol.createViewer(target,{backgroundColor:'#091522',antialias:true});v.setBackgroundColor('#091522');viewers[id]=v;return v;}
 catch(err){target.innerHTML='<div class="viewer-error"><b>Molecular rendering needs WebGL.</b><span>Enable hardware acceleration or use a browser with WebGL. The original CIF downloads and numerical results remain available.</span></div>';console.warn('MutaScape viewer:',err.message);return null;}
}
function atomRead(atom){$('#atom-readout').textContent=`${atom.chain}:${atom.resn}${atom.resi} · ${atom.atom} · (${atom.x.toFixed(2)}, ${atom.y.toFixed(2)}, ${atom.z.toFixed(2)}) Å · pLDDT ${atom.b}`;}
function confidenceColor(atom){return atom.b>=90?'#1a79c1':atom.b>=70?'#6dc6e1':atom.b>=50?'#f3da6b':'#ee9166';}
function styleModel(v,model,selection,color,style,confidence=false){const config=confidence?{colorfunc:confidenceColor}:{color};const sel={model,...selection};if(style==='cartoon')v.setStyle(sel,{cartoon:{...config,opacity:1}});else if(style==='stick')v.setStyle(sel,{stick:{...config,radius:.13}});else v.setStyle(sel,{sphere:{...config,scale:.26}});}
function region(){return D.audit.metrics[state.fit].range;}
function renderStructure(){
 if(state.route!=='structure')return;const v=makeViewer('structure-viewer');if(!v)return;
 v.spin(false);$('#structure-spin').setAttribute('aria-pressed','false');$('#structure-spin').textContent='Rotate';v.removeAllModels();v.removeAllLabels();v.removeAllShapes();
 const r=region(),sel={};
 // GL selection accepts a residue array; avoid nesting the range result.
 if(state.crop)sel.resi=Array.from({length:r[1]-r[0]+1},(_,i)=>i+r[0]);
 const available=state.mutation==='P';const overlay=state.view==='Overlay'&&available;const mutant=state.view==='Mutant'&&available;
 if(!mutant||overlay){v.addModel(D.models.foxa2_wt.pdb,'pdb');v.setStyle({model:0},{});styleModel(v,0,sel,C.wt,state.style,state.confidence);}
 if(mutant||overlay){const ix=overlay?1:0;v.addModel(D.aligned[state.fit],'pdb');v.setStyle({model:ix},{});styleModel(v,ix,sel,C.mut,state.style,state.confidence);}
 const count=overlay?2:1;
 for(let i=0;i<count;i++){v.addStyle({model:i,resi:231},{stick:{color:C.site,radius:.22},sphere:{color:C.site,scale:.35}});v.setClickable({model:i,...sel},true,atomRead);}
 v.zoomTo(sel);v.render();v.resize();const ready=target=>target.dataset.ready='true';ready($('#structure-viewer'));$('#structure-title').textContent=available?('FOXA2 · '+(overlay?'WT / S231P alignment':mutant?'supplied S231P':'WT reference')):'FOXA2 · WT reference / '+state.mutation+' model not supplied';
 updateStructureMetrics();
}
function updateStructureMetrics(){
 const m=D.audit.metrics[state.fit],available=state.mutation==='P';$('#rmsd-value').textContent=available?m.rmsd.toFixed(3):'—';$('#rmsd-detail').textContent=available?`${m.n} matched Cα atoms · residues ${m.range.join('–')} · no outlier removal.`:'No A/G mutant coordinates supplied; a WT reference is shown. No mutant RMSD is available.';
 $('#model-availability').textContent=available?'Actual file substitution: SER231 → PRO231. Project S169P mapping awaits sequence verification.':'Chemistry scenario only. This is the original WT geometry, not a predicted alanine/glycine mutant structure.';
 const deviations=available?m.residueDeviations:[];drawLineChart($('#displacement-chart'),deviations,'Residue number','Displacement / Å',231);$('#chart-status').textContent=available?'Every point is a matched Cα coordinate displacement after the selected rigid fit.':'No displacement curve is generated for an unsupplied mutant.';
}
function drawLineChart(el,points,xlabel,ylabel,marker=null){
 if(!points.length){el.innerHTML='<div class="empty-state">No data for this selection.</div>';return;}
 const W=900,H=175,left=52,right=22,top=18,bottom=35,xmin=points[0][0],xmax=points.at(-1)[0],max=Math.max(...points.map(p=>p[1]),.1)*1.1;
 const X=x=>left+(x-xmin)/Math.max(1,xmax-xmin)*(W-left-right),Y=y=>H-bottom-y/max*(H-top-bottom);
 let grid='';for(let i=0;i<=3;i++){const val=max*i/3,y=Y(val);grid+=`<line class="chart-grid" x1="${left}" x2="${W-right}" y1="${y}" y2="${y}"/><text class="chart-text" x="${left-8}" y="${y+3}" text-anchor="end">${val.toFixed(max>5?0:2)}</text>`;}
 const path=points.map((p,i)=>(i?'L':'M')+X(p[0]).toFixed(2)+','+Y(p[1]).toFixed(2)).join(' ');
 const m=marker!==null&&marker>=xmin&&marker<=xmax?`<line x1="${X(marker)}" x2="${X(marker)}" y1="${top}" y2="${H-bottom}" stroke="#f4ce77" stroke-dasharray="3 4"/><text class="chart-text" x="${X(marker)+6}" y="${top+6}" style="fill:#f4ce77">${marker}</text>`:'';
 el.innerHTML=`<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="${escape(ylabel)} by ${escape(xlabel)}">${grid}${m}<path d="${path}" fill="none" stroke="#70e6d4" stroke-width="1.5"/><text class="chart-text" x="${left}" y="${H-17}">${xmin}</text><text class="chart-text" x="${W-right}" y="${H-17}" text-anchor="end">${xmax}</text><text class="chart-text" x="${W/2}" y="${H-3}" text-anchor="middle">${escape(xlabel)}</text><text class="chart-text" x="${left}" y="10">${escape(ylabel)}</text></svg>`;
}
function renderDNA(){
 if(state.route!=='dna')return;const v=makeViewer('dna-viewer');if(!v)return;v.removeAllModels();v.removeAllLabels();v.removeAllShapes();v.addModel(D.models.foxa2_dna.pdb,'pdb');v.setStyle({},{});const style=$('#dna-style').value;
 if(style==='cartoon'){v.setStyle({chain:'F'},{cartoon:{color:C.F}});v.setStyle({chain:'D'},{stick:{color:C.D,radius:.13}});v.setStyle({chain:'E'},{stick:{color:C.E,radius:.13}});}else for(const chain of ['F','D','E'])styleModel(v,0,{chain},C[chain],style);
 v.addStyle({chain:'F',resi:231},{stick:{color:C.site,radius:.23},sphere:{color:C.site,scale:.33}});
 if(state.distance){const p=D.audit.dnaContactsUnder4A[0];const start={x:p.proteinXYZ[0],y:p.proteinXYZ[1],z:p.proteinXYZ[2]},end={x:p.dnaXYZ[0],y:p.dnaXYZ[1],z:p.dnaXYZ[2]};v.addLine({start,end,color:'#f4ce77',dashed:true});v.addLabel(p.distance.toFixed(3)+' Å',{position:{x:(start.x+end.x)/2,y:(start.y+end.y)/2,z:(start.z+end.z)/2},fontSize:11,backgroundColor:'#17313e',fontColor:'#f4ce77',backgroundOpacity:.8});}
 v.zoomTo({});v.render();v.resize();$('#dna-viewer').dataset.ready='true';$('#dna-distance-toggle').setAttribute('aria-pressed',String(state.distance));
}
const partners={SOX17:{role:'Endoderm lineage specification — a biological context for studying FOXA2-associated regulation.',file:'sox17',note:'414-residue supplied predicted model.'},HNF1A:{role:'A transcription factor associated with liver and pancreatic gene regulation.',file:'hnf1a',note:'119-residue supplied fragment; this is not full-length HNF1A.'},PDX1:{role:'Pancreatic development and insulin-related transcriptional regulation.',file:'pdx1',note:'283-residue supplied predicted model.'},OTX2:{role:'Embryonic developmental patterning — a broader developmental association in the prototype.',file:'otx2',note:'297-residue supplied predicted model.'}};
function buildNetwork(){const coords={SOX17:[133,90],HNF1A:[410,90],PDX1:[410,351],OTX2:[133,351]},cx=270,cy=225;let html='';for(const [name,[x,y]] of Object.entries(coords))html+=`<line class="network-edge" x1="${cx}" y1="${cy}" x2="${x}" y2="${y}"/>`;html+=`<g class="network-center"><circle cx="${cx}" cy="${cy}" r="51"/><circle cx="${cx}" cy="${cy}" r="64" fill="none" stroke="#22424c" stroke-dasharray="2 6"/><text x="${cx}" y="${cy+4}">FOXA2</text></g>`;
 for(const [name,[x,y]] of Object.entries(coords))html+=`<g class="network-node" data-partner="${name}" role="button" tabindex="0" aria-label="Inspect ${name}"><circle cx="${x}" cy="${y}" r="37"/><text x="${x}" y="${y+4}">${name}</text></g>`;
 $('#network-map').innerHTML=html;$$('[data-partner]').forEach(g=>{const choose=()=>{state.partner=g.dataset.partner;renderPartner();};g.addEventListener('click',choose);g.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();choose();}});});}
function renderPartner(){
 const p=partners[state.partner];$('#partner-name').textContent=state.partner;$('#partner-role').textContent=p.role;$('#partner-model-note').textContent=p.note;$('#partner-download').href='assets/structures/'+p.file+'.cif';$$('[data-partner]').forEach(g=>{const a=g.dataset.partner===state.partner;g.classList.toggle('active',a);g.setAttribute('aria-pressed',String(a));});
 if(state.route!=='network')return;const v=makeViewer('partner-viewer');if(!v)return;v.removeAllModels();v.addModel(D.models[p.file].pdb,'pdb');v.setStyle({},{cartoon:{color:C.D}});v.zoomTo();v.render();v.resize();$('#partner-viewer').dataset.ready='true';
}
function updateBoard(){
 const t=E.teaching(state.mutation,state.view,state.pressure,state.contact,state.mode);$('#board-knob').value=state.pot;$('#knob-readout').textContent=state.pot+' · '+state.mode;$('#knob-visual').style.transform='rotate('+(-135+state.pot/1023*270)+'deg)';
 $('#board-index').innerHTML=t.value+'<span>/ 100</span>';$('#board-mode').textContent=state.mode;$('#traffic-label').textContent=t.band;$('#traffic-label').style.color=t.band==='RED'?'#f97881':t.band==='YELLOW'?'#f4ce77':'#70e6a9';$('#traffic-band').textContent=t.band==='RED'?'High demo band':t.band==='YELLOW'?'Middle demo band':'Low demo band';
 $$('[data-light]').forEach(l=>l.classList.toggle('on',l.dataset.light===t.band.toLowerCase()));$('#servo-arm').style.transform='rotate('+t.angle+'deg)';$('#servo-angle').textContent=t.angle+'°';const lit=Math.floor(t.value/100*25);$$('#led-grid i').forEach((led,i)=>led.classList.toggle('on',(4-Math.floor(i/5))*5+(i%5)<lit));$('#led-grid').setAttribute('aria-label',lit+' of 25 simulated LEDs lit');
 $('#board-equation').textContent=`${t.base} + ${t.stress} + ${t.contact} = ${t.value}`;$('#board-equation-detail').innerHTML=`<div><span>${state.mode} baseline (${state.view==='WT'?'WT':'S→'+state.mutation})</span><b>${t.base}</b></div><div><span>floor(${state.pressure} × 0.25)</span><b>+${t.stress}</b></div><div><span>Simulated contact</span><b>+${t.contact}</b></div><div><span>Clamped teaching index</span><b>${t.value} / 100</b></div>`;
}
function saveRuns(){try{localStorage.setItem('mutascape-snapshots-v1',JSON.stringify(snapshots));}catch(_){toast('Snapshots remain in this session; browser storage is unavailable.');}}
function renderRuns(){
 $('#run-count').textContent=snapshots.length+' SNAPSHOTS';if(!snapshots.length){$('#run-chart').innerHTML='';$('#run-table').innerHTML='<div class="empty-state">Record a snapshot to compare teaching scenarios. No experimental data are generated.</div>';return;}
 drawLineChart($('#run-chart'),snapshots.map((r,i)=>[i+1,r.value]),'Snapshot number','Teaching index / 100');
 $('#run-table').innerHTML=table(['#','Scenario','Channel','Input','Contact','Index'],snapshots.slice(-12).map((r,i)=>[String(snapshots.length-Math.min(12,snapshots.length)+i+1),escape(r.substitution+' / '+r.view),escape(r.channel),String(r.environmentInput),r.contactSimulation?'On':'Off',r.value+' / 100']));
}
function initTables(){
 $('#led-grid').innerHTML='<i></i>'.repeat(25);
 $('#rmsd-table').innerHTML=table(['Residues','Cα count','Current fit / Å','Original report / Å'],Object.entries(D.audit.metrics).map(([k,m])=>[m.range.join('–'),String(m.n),m.rmsd.toFixed(6),k==='wide'?'0.321':k==='local'?'0.097':'—']));
 $('#dna-contact-table').innerHTML=table(['Protein atom','DNA atom','Distance / Å'],D.audit.dnaContactsUnder4A.map(p=>[escape('F:SER231 '+p.proteinAtom),escape(p.dnaChain+':'+p.dnaResn+p.dnaResi+' '+p.dnaAtom),p.distance.toFixed(3)]));$('#dna-nearest').textContent=D.audit.dnaContactsUnder4A[0].distance.toFixed(3);
 $('#weights-table').innerHTML=table(['Rule','S','D','N'],E.RULES.map(r=>[escape(r.name),...r.scores.map(String)]));
 const rows=Object.entries(D.models).map(([key,m])=>[escape(key+'.cif'),key==='foxa2_dna'?'Exported DNA complex':key==='foxa2_s169p'?'Supplied S231P model':key==='hnf1a'?'Predicted fragment':'Predicted protein model',m.caCount+' Cα / '+m.atomCount+' atoms',`<a href="${m.file}" download>Download ↓</a>`]);
 for(const file of ['Untitled-1.py','test.py','microbit_makecode.py','microbit_muta_controller.py','microbit_mutascape.py','microbit_test.py','moltest.py'])rows.push([escape(file),file.startsWith('microbit')?'Original hardware / serial source':'Original Python prototype','As supplied',`<a href="original-code/${file}" download>Download ↓</a>`]);
 rows.push(['structure-audit.json','Current reproducible coordinate audit','Derived results','<a href="data/structure-audit.json" download>Download ↓</a>']);$('#file-inventory').innerHTML=table(['File','Purpose','Contents','Access'],rows);
}
function serialRecord(line){serialLog.push(line);serialLog=serialLog.slice(-18);$('#serial-log').textContent=serialLog.join('\n');}
function applyDecoded(events,force=false){if(!force&&!$('#follow-board').checked)return;let rerender=false;for(const e of events){serialRecord(e.raw);if(e.pot!==undefined){state.pot=e.pot;state.mode=E.modeFromPot(e.pot);}if(e.pressure!==undefined)state.pressure=e.pressure;if(e.contact!==undefined)state.contact=e.contact;if(e.event==='A'){state.view=state.view==='WT'?'Mutant':'WT';rerender=true;}if(e.event==='B'){const order=['A','G','P'];state.mutation=order[(order.indexOf(state.mutation)+1)%3];rerender=true;}}
 updateAll(rerender);}
async function disconnect(){serialRunning=false;try{if(serialReader)await serialReader.cancel();}catch(_){}try{serialReader?.releaseLock();}catch(_){}serialReader=null;try{serialWriter?.releaseLock();}catch(_){}serialWriter=null;try{await serialPort?.close();}catch(_){}serialPort=null;$('#serial-connect').hidden=false;$('#serial-disconnect').hidden=true;$('#board-link-badge').textContent='BROWSER DEMO';$('#serial-status').textContent='No board connected.';}
async function connect(){
 if(serialBusy)return;serialBusy=true;$('#serial-connect').disabled=true;
 try{if(!navigator.serial)throw new Error('Web Serial is unavailable. Use Chrome/Edge on HTTPS or localhost.');serialPort=await navigator.serial.requestPort();await serialPort.open({baudRate:115200});serialWriter=serialPort.writable.getWriter();serialReader=serialPort.readable.getReader();serialRunning=true;decoder.buffer='';decoder.lastSequence=null;decoder.lastPlain={A:-Infinity,B:-Infinity};$('#serial-connect').hidden=true;$('#serial-disconnect').hidden=false;$('#follow-board').checked=true;$('#board-link-badge').textContent='SERIAL CONNECTED';$('#serial-status').textContent='Connected at 115200 baud. Inputs enabled; outputs require Send.';
 const textDecoder=new TextDecoder();while(serialRunning){const {value,done}=await serialReader.read();if(done)break;if(value){const events=decoder.feed(textDecoder.decode(value,{stream:true}));applyDecoded(events);}}
 if(serialRunning){await disconnect();$('#serial-status').textContent='The board connection ended.';}
 }catch(err){await disconnect();$('#serial-status').textContent=err.name==='NotFoundError'?'No device selected.':err.message;}finally{serialBusy=false;$('#serial-connect').disabled=false;}
}
async function syncBoard(){
 if(!serialWriter){toast('Connect a board first. The browser demo is already running.');return;}
 const profile=$('#firmware-profile').value;if(profile==='browser'){toast('Read-only profile selected; no commands sent.');return;}
 const t=E.teaching(state.mutation,state.view,state.pressure,state.contact,state.mode);let commands=['SEV:'+t.value];if($('#board-audio').checked){const cue=t.band==='RED'?'DANGER':t.band==='YELLOW'?'MODERATE':'STABLE';commands.push(profile==='controller'?'SOUND:'+cue:cue.toLowerCase());}
 try{await serialWriter.write(new TextEncoder().encode(commands.join('\n')+'\n'));serialRecord('OUT '+commands.join(' · '));$('#serial-status').textContent='Sent '+commands.join(' / ')+'. Outputs have not been physically verified here.';}catch(err){$('#serial-status').textContent='Write failed: '+err.message;}
}
function saveViewer(id,name){const v=viewers[id];if(!v){toast('Open a supported molecular view first.');return;}try{const a=document.createElement('a');a.download=name;a.href=v.pngURI();a.click();}catch(_){toast('This browser could not export the view.');}}
function bind(){
 window.addEventListener('hashchange',route);$('#mutation').addEventListener('change',e=>setMutation(e.target.value));$$('[data-view]').forEach(b=>b.addEventListener('click',()=>{state.view=b.dataset.view;updateAll();}));$('#pressure').addEventListener('input',e=>{state.pressure=Number(e.target.value);updateAll(false);});$('#contact').addEventListener('change',e=>{state.contact=e.target.checked;updateAll(false);});
 $('#reset-state').addEventListener('click',()=>{Object.assign(state,{mutation:'P',view:'Mutant',pressure:0,contact:false,pot:0,mode:'Structure'});$('#follow-board').checked=false;updateAll();toast('Exploration reset. Recorded snapshots kept.');});
 $('#fit-window').addEventListener('change',e=>{state.fit=e.target.value;renderStructure();});$('#crop-region').addEventListener('change',e=>{state.crop=e.target.checked;renderStructure();});$('#structure-style').addEventListener('change',e=>{state.style=e.target.value;renderStructure();});$('#confidence-color').addEventListener('change',e=>{state.confidence=e.target.checked;renderStructure();});
 $('#structure-focus').addEventListener('click',()=>{const v=viewers['structure-viewer'];if(v){v.zoomTo({resi:231});v.zoom(.85);v.render();}});$('#structure-fit').addEventListener('click',()=>{const v=viewers['structure-viewer'];if(v){const r=region();v.zoomTo({resi:Array.from({length:r[1]-r[0]+1},(_,i)=>i+r[0])});v.render();}});$('#structure-reset').addEventListener('click',renderStructure);$('#structure-spin').addEventListener('click',e=>{const v=viewers['structure-viewer'];if(!v)return;const on=e.target.getAttribute('aria-pressed')!=='true';v.spin(on?'y':false,.4);e.target.setAttribute('aria-pressed',String(on));e.target.textContent=on?'Stop rotation':'Rotate';});$('#structure-png').addEventListener('click',()=>saveViewer('structure-viewer','MutaScape-structure.png'));
 $('#dna-style').addEventListener('change',renderDNA);$('#dna-focus').addEventListener('click',()=>{const v=viewers['dna-viewer'];if(v){v.zoomTo({chain:'F',resi:231});v.zoom(.8);v.render();}});$('#dna-reset').addEventListener('click',renderDNA);$('#dna-distance-toggle').addEventListener('click',()=>{state.distance=!state.distance;renderDNA();if(state.distance){viewers['dna-viewer']?.zoomTo({chain:'F',resi:231});viewers['dna-viewer']?.render();}});$('#dna-png').addEventListener('click',()=>saveViewer('dna-viewer','MutaScape-DNA.png'));$('#partner-reset').addEventListener('click',renderPartner);
 $('#board-a').addEventListener('click',toggleView);$('#board-b').addEventListener('click',cycle);$('#board-knob').addEventListener('input',e=>{state.pot=Number(e.target.value);state.mode=E.modeFromPot(state.pot);updateAll(false);});$('#record-run').addEventListener('click',()=>{snapshots.push(E.snapshot(state));snapshots=snapshots.slice(-100);saveRuns();renderRuns();toast('Teaching scenario recorded.');});$('#export-runs').addEventListener('click',()=>{if(!snapshots.length){toast('Record a snapshot first.');return;}download('MutaScape-teaching-scenarios.json',JSON.stringify({notice:'Illustrative teaching indices; not biological measurements or probabilities.',snapshots},null,2));});$('#clear-runs').addEventListener('click',()=>{snapshots=[];saveRuns();renderRuns();toast('Snapshots cleared.');});
 $('#serial-connect').addEventListener('click',connect);$('#serial-disconnect').addEventListener('click',disconnect);$('#serial-sync').addEventListener('click',syncBoard);$('#serial-test-apply').addEventListener('click',()=>{const sample=new E.SerialDecoder();applyDecoded(sample.feed($('#serial-test').value+'\n'),true);toast('Sample serial inputs applied locally.');});
 $('#help-btn').addEventListener('click',()=>$('#help-dialog').showModal());$('#close-help').addEventListener('click',()=>$('#help-dialog').close());$('#help-dialog').addEventListener('click',e=>{if(e.target.id==='help-dialog'){const r=e.target.getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)e.target.close();}});
 window.addEventListener('resize',()=>{for(const v of Object.values(viewers))v.resize?.();});
 window.addEventListener('hashchange',()=>{if(state.route!=='structure'){viewers['structure-viewer']?.spin(false);}});
}
initTables();buildNetwork();renderRuns();bind();route();
window.MutaApp={state,viewers,decoder,applyDecoded,getSnapshots:()=>snapshots,renderStructure,renderDNA,renderPartner};
})();

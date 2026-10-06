/* Shared transparent demo rules. No clinical or experimentally calibrated model. */
(function(global){
'use strict';
const MODES=['Structure','DNA','Network'];
const AA={S:{name:'Serine',polarity:'Polar',hydroxyl:true,flexibility:'Context dependent',ring:false},P:{name:'Proline',polarity:'Nonpolar',hydroxyl:false,flexibility:'Ring-constrained backbone',ring:true},A:{name:'Alanine',polarity:'Nonpolar',hydroxyl:false,flexibility:'Unconstrained side-chain geometry',ring:false},G:{name:'Glycine',polarity:'Nonpolar',hydroxyl:false,flexibility:'Greater backbone freedom',ring:false}};
const RULES=[{name:'Proline backbone constraint',scores:[30,0,15],applies:m=>m==='P'},{name:'Side-chain polarity change',scores:[15,10,15],applies:m=>['P','A','G'].includes(m)},{name:'Loss of serine side-chain OH',scores:[20,15,20],applies:m=>['P','A','G'].includes(m)},{name:'Loss of serine OH modification potential',scores:[0,0,20],applies:m=>['P','A','G'].includes(m)}];
function clamp(v,lo,hi){const n=Number(v);return Math.min(hi,Math.max(lo,Number.isFinite(n)?n:lo));}
function chemistry(mutant){if(!AA[mutant])throw new Error('Unknown preset');const contributions=RULES.filter(r=>r.applies(mutant));return {scores:MODES.map((_,i)=>Math.min(100,contributions.reduce((a,r)=>a+r.scores[i],0))),contributions};}
function teaching(mutant,view,pressure,contact,mode){if(!MODES.includes(mode))throw new Error('Unknown channel');const raw=chemistry(mutant);const base=view==='WT'?0:raw.scores[MODES.indexOf(mode)];const stress=Math.floor(clamp(pressure,0,100)*.25);const contactTerm=contact?25:0;const value=Math.min(100,base+stress+contactTerm);return {base,stress,contact:contactTerm,value,band:value>=70?'RED':value>=40?'YELLOW':'GREEN',angle:view==='WT'?0:180};}
function modeFromPot(value){return MODES[Math.min(2,Math.floor(clamp(value,0,1023)/1024*3))];}
class SerialDecoder{
 constructor(){this.buffer='';this.lastSequence=null;this.lastPlain={A:-Infinity,B:-Infinity};}
 event(button,seq,now){if(!['A','B'].includes(button))return null;if(seq!==undefined){if(seq===this.lastSequence)return null;this.lastSequence=seq;return button;}
 // The MakeCode upload repeats a latched event every 250 ms for two seconds.
 // Treat a uninterrupted burst as one event; distinct bursts need >500 ms quiet.
 const last=this.lastPlain[button];this.lastPlain[button]=now;return now-last>500?button:null;}
 parse(line,now=Date.now()){
  if(line.length>1024)return null;let s=String(line).trim().toUpperCase();if(!s)return null;const out={raw:line};
  if(/^(A|B|BTN_A|BTN_B|BUTTON_A|BUTTON_B)$/.test(s)){out.event=this.event(s.slice(-1),undefined,now);return out;}
  if(/^\d+$/.test(s)){out.pot=clamp(s,0,1023);return out;}
  const fields={};for(const m of s.matchAll(/([A-Z][A-Z0-9_]*)\s*[:=]\s*([A-Z]+|[-+]?\d+(?:\.\d+)?)/g))fields[m[1]]=m[2];
  const num=(names)=>{for(const n of names)if(fields[n]!==undefined&&Number.isFinite(Number(fields[n])))return Number(fields[n]);};
  const p=num(['POT','KNOB','P0','ROT','ROTARY']),mic=num(['MIC','P2','SOUND']),stress=num(['STRESS']),contact=num(['CONTACT']);
  if(p!==undefined)out.pot=clamp(p,0,1023);if(mic!==undefined)out.pressure=Math.floor(clamp(mic,0,1023)/1023*100);if(stress!==undefined)out.pressure=clamp(stress,0,100);
  // Raw P1 polarity differs between firmware variants. Only explicit CONTACT sets
  // the simulation, avoiding false contact caused by electrical pin diagnostics.
  if(contact!==undefined)out.contact=contact===1;
  let evt=fields.EVT||fields.BTN||fields.P1E;if(evt==='BTN_A'||evt==='BUTTON_A')evt='A';if(evt==='BTN_B'||evt==='BUTTON_B')evt='B';
  if(evt){const seq=num(['SEQ']);out.event=this.event(evt,seq,now);}
  return Object.keys(out).length>1?out:null;
 }
 feed(chunk,now=Date.now()){
  this.buffer+=chunk;if(this.buffer.length>8192&&!this.buffer.includes('\n')){this.buffer='';return [];}
  const rows=this.buffer.split(/\r?\n/);this.buffer=rows.pop();return rows.map(r=>this.parse(r,now)).filter(Boolean);
 }
}
function snapshot(state){return {type:'MutaScape teaching scenario',recordedAt:new Date().toISOString(),suppliedModelSite:231,projectS169Mapping:'unverified',substitution:'S231'+state.mutation,view:state.view,channel:state.mode,environmentInput:clamp(state.pressure,0,100),contactSimulation:!!state.contact,...teaching(state.mutation,state.view,state.pressure,state.contact,state.mode)};}
const API={MODES,AA,RULES,clamp,chemistry,teaching,modeFromPot,SerialDecoder,snapshot};global.MutaEngine=API;if(typeof module!=='undefined')module.exports=API;
})(typeof window!=='undefined'?window:globalThis);

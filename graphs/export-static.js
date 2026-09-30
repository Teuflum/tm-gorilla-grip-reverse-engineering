// Export the same default SVG charts shown by interactive.html.
// This tiny DOM adapter keeps the renderer dependency-free in Node.
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const model = require('./model.js');
const plasticFlick = require('./plastic-flick-data.js');

class Element {
  constructor(tag) { this.tag = tag; this.attributes = {}; this.children = []; this.textContent = ''; this.style = {}; this.value = ''; }
  setAttribute(key, value) { this.attributes[key] = String(value); }
  append(child) { this.children.push(child); }
  replaceChildren(...children) { this.children = children; }
  addEventListener() {}
}

const names = ['mix-chart','icing-time-chart','steering-chart','force-chart','speed-chart','recovery-chart','neutral-chart','flick-angle-chart','flick-force-chart'];
const values = { 'icing-range':80, 'initial-range':100, 'wetness-range':0, 'time-range':1650, 'contact-range':6, 'steer-size-range':20, 'speed-range':100, 'angle-range':30, 'lead-range':1300, 'neutral-range':100, 'flick-range':8300 };
const elements = new Map();
for (const name of names) elements.set(name,new Element('svg'));
for (const [name,value] of Object.entries(values)) { const input=new Element('input'); input.value=value; elements.set(name,input); }

const document = {
  createElementNS(_namespace, tag) { return new Element(tag); },
  getElementById(id) { if (!elements.has(id)) elements.set(id,new Element('span')); return elements.get(id); },
  querySelectorAll() { return []; },
};
vm.runInNewContext(fs.readFileSync(path.join(__dirname,'app.js'),'utf8'), {document, globalThis:{GorillaGripModel:model,PlasticFlickData:plasticFlick}});

function escapeXml(value) { return String(value).replaceAll('&','&amp;').replaceAll('"','&quot;').replaceAll('<','&lt;').replaceAll('>','&gt;'); }
function serialize(node) {
  const attrs=Object.entries(node.attributes).map(([key,value])=>` ${key}="${escapeXml(value)}"`).join('');
  return `<${node.tag}${attrs}>${escapeXml(node.textContent)}${node.children.map(serialize).join('')}</${node.tag}>`;
}

const charts = [
  ['mix-chart','icing-force-mix.svg','Average tire icing versus icy-force weight on ice-family and other materials'],
  ['icing-time-chart','icing-over-time.svg','Tire icing rising on ice and falling on plastic or in air'],
  ['steering-chart','steering-before-takeoff.svg','Internal steering threshold versus the final wheel-contact update'],
  ['force-chart','steering-force-target.svg','Recovered tire-force multiplier versus internal steering magnitude'],
  ['speed-chart','speed-force-target.svg','Recovered tire-force multiplier at full steering versus car speed and front-wheel angle to the travel direction'],
  ['recovery-chart','force-recovery.svg','Force multiplier recovery after landing with or without an early stored direction'],
  ['neutral-chart','neutral-steering-timeout.svg','Stored slide direction clears after 300 milliseconds of neutral internal steering'],
  ['flick-angle-chart','plastic-flick-angles.svg','Travel direction and steered-wheel angle from the car nose over a measured plastic flick'],
  ['flick-force-chart','plastic-flick-force.svg','Logged tire-force multiplier and predicted target over a measured plastic flick'],
];
const folder=path.join(__dirname,'static');
fs.mkdirSync(folder,{recursive:true});
for (const [id,filename,title] of charts) {
  const svg=elements.get(id);
  svg.setAttribute('xmlns','http://www.w3.org/2000/svg');
  svg.setAttribute('font-family','system-ui, sans-serif');
  svg.setAttribute('role','img');
  svg.setAttribute('aria-label',title);
  const markup=serialize(svg).replace('>',`><title>${escapeXml(title)}</title>`);
  fs.writeFileSync(path.join(folder,filename),`<?xml version="1.0" encoding="UTF-8"?>\n${markup}\n`);
  console.log(`wrote ${filename}`);
}

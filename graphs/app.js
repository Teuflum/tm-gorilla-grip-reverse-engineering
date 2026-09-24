(() => {
  'use strict';
  const m = globalThis.GorillaGripModel;
  const NS = 'http://www.w3.org/2000/svg';
  const C = { blue:'#1469aa', orange:'#b05b17', green:'#08775d', purple:'#7454a8', gray:'#5a6c7b' };
  const P = { left:72, right:775, top:46, bottom:326 };

  function svgNode(tag, attrs = {}, content) {
    const node = document.createElementNS(NS, tag);
    for (const [key, value] of Object.entries(attrs)) node.setAttribute(key, String(value));
    if (content !== undefined) node.textContent = content;
    return node;
  }
  function add(parent, tag, attrs, content) {
    const node = svgNode(tag, attrs, content);
    parent.append(node);
    return node;
  }
  function percent(value, digits = 3) {
    return `${Number((value * 100).toFixed(digits))}%`;
  }
  function milliseconds(value) { return `${Math.round(value).toLocaleString('en-US')} ms`; }
  function setText(id, value) { document.getElementById(id).textContent = value; }

  function drawChart(id, config) {
    const svg = document.getElementById(id);
    svg.setAttribute('viewBox', '0 0 800 400');
    svg.replaceChildren();
    const plotWidth = P.right - P.left;
    const plotHeight = P.bottom - P.top;
    const x = v => P.left + (v - config.xMin) / (config.xMax - config.xMin) * plotWidth;
    const y = v => P.bottom - (v - config.yMin) / (config.yMax - config.yMin) * plotHeight;

    add(svg, 'rect', { x:P.left, y:P.top, width:plotWidth, height:plotHeight, fill:'#fbfdff' });
    if (config.shadeBefore !== undefined) {
      add(svg, 'rect', { x:P.left, y:P.top, width:Math.max(0,x(config.shadeBefore)-P.left), height:plotHeight, fill:'#eaf5f2' });
    }
    for (const tick of config.yTicks) {
      const yy = y(tick);
      add(svg, 'line', { x1:P.left, y1:yy, x2:P.right, y2:yy, stroke:'#dbe4ed', 'stroke-width':1 });
      add(svg, 'text', { x:P.left-12, y:yy+4, 'text-anchor':'end', fill:'#506578', 'font-size':12 }, config.yFormat(tick));
    }
    for (const tick of config.xTicks) {
      const xx = x(tick);
      add(svg, 'line', { x1:xx, y1:P.top, x2:xx, y2:P.bottom, stroke:'#e4ebf0', 'stroke-width':1 });
      add(svg, 'text', { x:xx, y:P.bottom+22, 'text-anchor':'middle', fill:'#506578', 'font-size':12 }, config.xFormat(tick));
    }
    for (const line of config.referenceLines || []) {
      const attrs = { stroke:line.color || C.gray, 'stroke-width':1.5, 'stroke-dasharray':'5 4' };
      if (line.axis === 'x') add(svg, 'line', { x1:x(line.value), y1:P.top, x2:x(line.value), y2:P.bottom, ...attrs });
      else add(svg, 'line', { x1:P.left, y1:y(line.value), x2:P.right, y2:y(line.value), ...attrs });
    }
    for (const series of config.series) {
      const path = series.points.map(([px,py],index) => `${index?'L':'M'}${x(px).toFixed(2)},${y(py).toFixed(2)}`).join(' ');
      add(svg, 'path', { d:path, fill:'none', stroke:series.color, 'stroke-width':3.5, 'stroke-linecap':'round', 'stroke-linejoin':'round', 'stroke-dasharray':series.dash || 'none' });
    }
    for (const dot of config.dots || []) {
      add(svg, 'circle', { cx:x(dot.x), cy:y(dot.y), r:6.5, fill:dot.color, stroke:'#fff', 'stroke-width':2.5 });
    }
    let legendX = P.left;
    for (const series of config.series) {
      add(svg, 'line', { x1:legendX, y1:22, x2:legendX+25, y2:22, stroke:series.color, 'stroke-width':4, 'stroke-dasharray':series.dash || 'none' });
      add(svg, 'text', { x:legendX+33, y:26, fill:'#22394d', 'font-size':13, 'font-weight':650 }, series.name);
      legendX += series.legendWidth || 230;
    }
    add(svg, 'line', { x1:P.left, y1:P.bottom, x2:P.right, y2:P.bottom, stroke:'#506578', 'stroke-width':1.3 });
    add(svg, 'line', { x1:P.left, y1:P.top, x2:P.left, y2:P.bottom, stroke:'#506578', 'stroke-width':1.3 });
    add(svg, 'text', { x:(P.left+P.right)/2, y:383, 'text-anchor':'middle', fill:'#344d62', 'font-size':13, 'font-weight':650 }, config.xLabel);
    add(svg, 'text', { x:19, y:(P.top+P.bottom)/2, transform:`rotate(-90 19 ${(P.top+P.bottom)/2})`, 'text-anchor':'middle', fill:'#344d62', 'font-size':13, 'font-weight':650 }, config.yLabel);
  }

  function samples(xMin,xMax,step,fn) {
    const data=[];
    for (let v=xMin;v<=xMax+step/10;v+=step) data.push([Math.min(v,xMax),fn(Math.min(v,xMax))]);
    return data;
  }

  function updateMix() {
    const icing = Number(document.getElementById('icing-range').value)/100;
    const ice = m.iceWeight(icing), other=m.otherWeight(icing);
    setText('icing-value',percent(icing,0));
    setText('ice-weight',percent(ice)); setText('other-weight',percent(other));
    setText('ice-ordinary',percent(1-ice)); setText('other-ordinary',percent(1-other));
    document.getElementById('ice-stack').style.width=percent(ice,4);
    document.getElementById('other-stack').style.width=percent(other,4);
    setText('mix-summary',`${percent(icing,0)} average tire icing → icy-force weight ${percent(ice)} on ice-family material, ${percent(other)} on plastic/asphalt. These are force-calculation weights, not grip percentages.`);
    drawChart('mix-chart', { xMin:0,xMax:100,yMin:0,yMax:100,xTicks:[0,20,40,60,80,100],yTicks:[0,20,40,60,80,100],xFormat:v=>`${v}%`,yFormat:v=>`${v}%`,xLabel:'Average tire icing (input)',yLabel:'Weight for icy-force term (output)',
      series:[{name:'Ice / Snow / RoadIce',color:C.blue,points:samples(0,100,1,v=>m.iceWeight(v/100)*100),legendWidth:260},{name:'Plastic / Asphalt / other',color:C.orange,points:samples(0,100,1,v=>m.otherWeight(v/100)*100)}],
      referenceLines:[{axis:'x',value:icing*100,color:C.gray}],dots:[{x:icing*100,y:ice*100,color:C.blue},{x:icing*100,y:other*100,color:C.orange}] });
  }

  function updateIcingTime() {
    const initial=Number(document.getElementById('initial-range').value)/100;
    const wetness=Number(document.getElementById('wetness-range').value)/100;
    const time=Number(document.getElementById('time-range').value);
    setText('initial-value',percent(initial,0)); setText('wetness-value',percent(wetness,0)); setText('time-value',milliseconds(time));
    const at=state=>m.icingAt(state,initial,time,wetness);
    setText('icing-time-summary',`After ${milliseconds(time)} from ${percent(initial,0)} icing: on ice ${percent(at('ice'))}; on plastic ${percent(at('plastic'))}; in air ${percent(at('air'))}. Wetness holds decay above ${percent(Math.min(initial,wetness))} while it stays fixed.`);
    const types=[['ice','Ice / RoadIce',C.blue],['plastic','Plastic / other ground',C.orange],['air','Air',C.green]];
    drawChart('icing-time-chart',{xMin:0,xMax:6000,yMin:0,yMax:100,xTicks:[0,1000,2000,3000,4000,5000,6000],yTicks:[0,20,40,60,80,100],xFormat:v=>`${v/1000}s`,yFormat:v=>`${v}%`,xLabel:'Time held in that condition',yLabel:'Icing on one tire',
      series:types.map(([key,name,color])=>({name,color,points:samples(0,6000,50,t=>m.icingAt(key,initial,t,wetness)*100),legendWidth:key==='plastic'?255:180})),
      referenceLines:[{axis:'x',value:time,color:C.gray}],dots:types.map(([key,,color])=>({x:time,y:at(key)*100,color})) });
  }

  function updateSteering() {
    const last=Number(document.getElementById('contact-range').value);
    const steering=m.steeringAfterUpdates(last);
    const mode=m.modeAtTakeoff(last);
    setText('contact-value',String(last));
    setText('steering-summary',mode==='right'
      ? `Contact through update ${last}: internal steering is ${percent(steering)}. It passed +10% while a wheel touched, so right mode is stored before flight.`
      : `Contact only through update ${last}: internal steering reaches ${percent(steering)} before flight. It has not passed +10% with contact, so the previous left mode remains.`);
    drawChart('steering-chart',{xMin:0,xMax:10,yMin:-100,yMax:100,xTicks:[0,2,4,6,8,10],yTicks:[-100,-50,0,50,100],xFormat:v=>String(v),yFormat:v=>`${v}%`,xLabel:'Affected physics updates since raw input changed',yLabel:'Internal smoothed steering',shadeBefore:last,
      series:[{name:'Full-left → full-right example',color:C.blue,points:samples(0,10,1,n=>m.steeringAfterUpdates(n)*100),legendWidth:280}],
      referenceLines:[{axis:'y',value:10,color:C.green},{axis:'y',value:-10,color:C.orange},{axis:'x',value:last,color:C.purple}],
      dots:[{x:last,y:steering*100,color:C.purple}] });
  }

  function updateForce() {
    const magnitude=Number(document.getElementById('steer-size-range').value)/100;
    const target=m.targetMultiplier(magnitude);
    setText('steer-size-value',percent(magnitude,0));
    setText('force-summary',`${percent(magnitude,0)} internal steering → recovered target about ${target.toFixed(3)}× in the measured high-speed ice case. The 10% line decides the stored direction; it does not give the full 2.0× target.`);
    drawChart('force-chart',{xMin:0,xMax:100,yMin:1,yMax:2,xTicks:[0,10,20,40,60,80,100],yTicks:[1,1.25,1.5,1.75,2],xFormat:v=>`${v}%`,yFormat:v=>`${v.toFixed(2)}×`,xLabel:'Magnitude of internal smoothed steering',yLabel:'Recovered tire-force multiplier',
      series:[{name:'Measured high-speed ice relation',color:C.blue,points:samples(0,100,1,v=>m.targetMultiplier(v/100)),legendWidth:330}],
      referenceLines:[{axis:'x',value:10,color:C.orange}],dots:[{x:magnitude*100,y:target,color:C.blue}] });
  }

  function updateRecovery() {
    const lead=Number(document.getElementById('lead-range').value);
    const landing=m.recoverySketch(lead);
    setText('lead-value',milliseconds(lead));
    setText('recovery-summary',`If right mode was stored ${milliseconds(lead)} before landing, this illustrative full-steering trace is about ${landing.toFixed(2)}× at touchdown. If mode switches only on landing, it starts at 1.0× and recovers later.`);
    drawChart('recovery-chart',{xMin:0,xMax:700,yMin:1,yMax:2,xTicks:[0,100,200,300,400,500,600,700],yTicks:[1,1.25,1.5,1.75,2],xFormat:v=>`${v}`,yFormat:v=>`${v.toFixed(2)}×`,xLabel:'Milliseconds after landing',yLabel:'Tire-force multiplier (sketch)',
      series:[{name:'Mode changed on landing',color:C.blue,points:samples(0,700,10,t=>m.recoverySketch(t)),legendWidth:245},{name:'Mode stored before landing',color:C.green,points:samples(0,700,10,t=>m.recoverySketch(t+lead)),legendWidth:285}],
      referenceLines:[{axis:'x',value:400,color:C.orange}],dots:[{x:0,y:landing,color:C.green}] });
  }

  function updateNeutral() {
    const duration=Number(document.getElementById('neutral-range').value);
    const retained=m.neutralModeAt(duration)==='left';
    setText('neutral-value',milliseconds(duration));
    setText('neutral-summary',retained
      ? `${milliseconds(duration)} neutral: left mode is still stored. Returning past −10% left preserves that mode and avoids a new 400 ms recovery wait, although force may have fallen while steering was centered.`
      : `${milliseconds(duration)} neutral: the old left mode has cleared. Returning past −10% left stores left again and restarts the force-recovery wait.`);
    drawChart('neutral-chart',{xMin:0,xMax:500,yMin:-0.1,yMax:1.1,xTicks:[0,100,200,300,400,500],yTicks:[0,1],xFormat:v=>`${v}`,yFormat:v=>v===1?'Left stored':'Neutral',xLabel:'Milliseconds held at neutral internal steering',yLabel:'Stored slide direction',
      series:[{name:'Mode while steering stays neutral',color:C.purple,points:[[0,1],[299.99,1],[300,0],[500,0]],legendWidth:320}],
      referenceLines:[{axis:'x',value:300,color:C.orange},{axis:'x',value:duration,color:C.gray}],dots:[{x:duration,y:retained?1:0,color:C.purple}] });
  }

  document.getElementById('icing-range').addEventListener('input',updateMix);
  document.querySelectorAll('[data-icing]').forEach(button=>button.addEventListener('click',()=>{document.getElementById('icing-range').value=button.dataset.icing;updateMix();}));
  for (const id of ['initial-range','wetness-range','time-range']) document.getElementById(id).addEventListener('input',updateIcingTime);
  document.getElementById('contact-range').addEventListener('input',updateSteering);
  document.getElementById('steer-size-range').addEventListener('input',updateForce);
  document.getElementById('lead-range').addEventListener('input',updateRecovery);
  document.getElementById('neutral-range').addEventListener('input',updateNeutral);
  updateMix();updateIcingTime();updateSteering();updateForce();updateRecovery();updateNeutral();
})();

const state={context:{},history:[]};
const api=()=>localStorage.getItem('COPILOT_API')||'http://localhost:8000';
const el=id=>document.getElementById(id);
function addMessage(role,text,meta=''){
 const item=document.createElement('div'); item.className=`message ${role}`;
 item.innerHTML=`<div class="role">${role==='user'?'You':'Copilot'}</div><div class="text"></div><div class="small">${meta}</div>`;
 item.querySelector('.text').textContent=text; el('messages').appendChild(item); el('messages').scrollTop=el('messages').scrollHeight;
}
async function run(){
 const input=el('prompt').value.trim(); if(!input)return;
 addMessage('user',input); el('prompt').value=''; el('run').disabled=true; el('status').textContent='Orchestrating…';
 try{
  const r=await fetch(api()+'/api/v1/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:input,context:state.context})});
  const d=await r.json(); if(!r.ok)throw new Error(d.detail||'Request failed');
  state.history.push({input,output:d}); state.context.lastResponse=d;
  addMessage('assistant',d.answer,`Agent ${d.agent} · ${Math.round(d.confidence*100)}% · ${d.validation} · ${d.attempts} attempt(s)`);
  el('status').textContent=d.verified?'Verified result':'Generated result';
 }catch(e){addMessage('assistant',e.message,'Request failed');el('status').textContent='Error'}finally{el('run').disabled=false}
}
el('run').onclick=run;
el('prompt').addEventListener('keydown',e=>{if((e.ctrlKey||e.metaKey)&&e.key==='Enter')run()});
el('clear').onclick=()=>{el('messages').innerHTML='';state.history=[];state.context={};el('status').textContent='Ready'};
el('api').value=api();
el('api').onchange=()=>localStorage.setItem('COPILOT_API',el('api').value.replace(/\/$/,''));

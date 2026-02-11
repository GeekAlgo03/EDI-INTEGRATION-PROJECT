function el(id){return document.getElementById(id)}

async function postJson(path, body){
  const res = await fetch(path, {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify(body)
  });
  if (!res.ok) throw await res.json();
  return res.json();
}

function mk(text){
  const d = document.createElement('div'); d.innerHTML = text; return d.firstElementChild;
}

function showResult(obj){
  const area = el('resultsArea');
  area.innerHTML = '';
  const card = mk(`<div class="result-card"></div>`);
  const header = mk(`<div class="result-header"><div class="status">${obj.message||'Result'}</div></div>`);
  card.appendChild(header);

  if (obj.run_id){
    const runLine = mk(`<div class="row"><strong>Run ID:</strong> <span class="runid">${obj.run_id}</span></div>`);
    const copy = mk(`<button class="small">Copy</button>`);
    copy.addEventListener('click', ()=>navigator.clipboard.writeText(obj.run_id));
    const replayBtn = mk(`<button class="small">Replay</button>`);
    replayBtn.addEventListener('click', ()=>{
      el('replayId').value = obj.run_id;
      el('replayBtn').click();
    });
    runLine.appendChild(copy); runLine.appendChild(replayBtn);
    card.appendChild(runLine);
  }

  if (obj.canonical) {
    const c = mk(`<details open><summary>Canonical</summary><pre>${JSON.stringify(obj.canonical, null, 2)}</pre></details>`);
    card.appendChild(c);
  }
  if (obj.netsuite_payload) {
    const n = mk(`<details><summary>Netsuite Payload</summary><pre>${JSON.stringify(obj.netsuite_payload, null, 2)}</pre></details>`);
    card.appendChild(n);
  }
  if (obj.stored){
    const s = mk(`<details><summary>Stored</summary><pre>${JSON.stringify(obj.stored, null, 2)}</pre></details>`);
    card.appendChild(s);
  }
  if (obj.error){
    const err = mk(`<pre class="error">${obj.error}</pre>`);
    card.appendChild(err);
  }

  area.appendChild(card);
}

// Guided items handling
function addItemRow(sku='',qty=''){
  const div = document.createElement('div'); div.className = 'item-row';
  div.innerHTML = `<input placeholder="SKU" class="sku" value="${sku}"/> <input placeholder="Qty" class="qty" value="${qty}"/> <button class="rm small">Remove</button>`;
  div.querySelector('.rm').addEventListener('click', ()=>div.remove());
  el('itemsList').appendChild(div);
}

// Build XML from guided fields
function buildXml(){
  const doc = el('docType').value;
  const po = el('poNumber').value.trim();
  const raw = el('rawXml').value.trim();
  if (raw) return raw;
  if (doc === '850'){
    return `<?xml version="1.0"?>\n<order>\n  <poNumber>${po}</poNumber>\n</order>`;
  } else {
    const ship = el('shipmentNumber').value.trim();
    const items = Array.from(document.querySelectorAll('#itemsList .item-row')).map(r=>{
      const sku = r.querySelector('.sku').value.trim();
      const qty = r.querySelector('.qty').value.trim();
      return `  <item>\n    <itemIdentifier>${sku}</itemIdentifier>\n    <quantityShipped>${qty}</quantityShipped>\n  </item>`;
    }).join('\n');
    return `<?xml version="1.0"?>\n<asn>\n  <shipmentIdentificationNumber>${ship}</shipmentIdentificationNumber>\n  <poNumber>${po}</poNumber>\n${items}\n</asn>`;
  }
}

el('docType').addEventListener('change', (e)=>{
  el('asnFields').style.display = e.target.value === '856' ? 'block' : 'none';
});

el('addItem').addEventListener('click', (e)=>{ e.preventDefault(); addItemRow(); });

el('clearForm').addEventListener('click', ()=>{
  el('poNumber').value=''; el('shipmentNumber').value=''; el('rawXml').value=''; el('itemsList').innerHTML='';
});

el('buildAndSend').addEventListener('click', async ()=>{
  try{
    const xml = buildXml();
    const doc = el('docType').value;
    const path = doc === '850' ? '/ingest/850' : '/ingest/856';
    const res = await postJson(path, { raw_xml: xml });
    showResult(res);
  }catch(err){
    showResult({ error: JSON.stringify(err) });
  }
});

el('replayBtn').addEventListener('click', async ()=>{
  const id = el('replayId').value.trim(); if(!id) return;
  try{
    const res = await fetch(`/replay/${encodeURIComponent(id)}`);
    if(!res.ok) throw await res.json();
    const j = await res.json();
    showResult({ message:'Replay executed', stored: j.stored, canonical: j.replay.canonical, netsuite_payload: j.replay.netsuite_payload, run_id: id });
  }catch(err){ showResult({ error: JSON.stringify(err) }); }
});

// initial sample
addItemRow('SKU-001','10');
addItemRow('SKU-002','5');

// ---- Chat UI ----
// Chat collapse toggle
const chatPanel = document.querySelector('.chat-panel');
const toggleChatBtn = document.getElementById('toggleChat');
function setChatCollapsed(collapsed){
  if(!chatPanel) return;
  chatPanel.classList.toggle('collapsed', collapsed);
  if(toggleChatBtn) toggleChatBtn.textContent = collapsed ? '+' : '−';
  chatPanel.setAttribute('aria-expanded', collapsed ? 'false' : 'true');
  try{ localStorage.setItem('chatCollapsed', collapsed ? '1' : '0'); }catch(e){}
}
if(toggleChatBtn){
  toggleChatBtn.addEventListener('click', ()=> setChatCollapsed(!chatPanel.classList.contains('collapsed')));
  try{
    const saved = localStorage.getItem('chatCollapsed');
    if(saved === '1') setChatCollapsed(true);
  }catch(e){}
}

function appendChat(role, text){
  const win = el('chatWindow');
  const div = document.createElement('div');
  div.className = 'chat-msg ' + (role==='user'? 'user':'bot');
  div.innerHTML = `<div class="role">${role}</div><div class="text">${text}</div>`;
  win.appendChild(div);
  win.scrollTop = win.scrollHeight;
}

el('sendChat').addEventListener('click', async ()=>{
  const msg = el('chatInput').value.trim(); if(!msg) return;
  appendChat('user', msg);
  el('chatInput').value='';
  appendChat('bot','Thinking...');
  try{
    const res = await fetch('/chat/map', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({message: msg}) });
    const j = await res.json();
    // replace last bot 'Thinking...'
    const bots = Array.from(document.querySelectorAll('.chat-msg.bot'));
    if (bots.length) bots[bots.length-1].querySelector('.text').textContent = j.reply || JSON.stringify(j);
    else appendChat('bot', j.reply || JSON.stringify(j));
  }catch(err){
    const bots = Array.from(document.querySelectorAll('.chat-msg.bot'));
    if (bots.length) bots[bots.length-1].querySelector('.text').textContent = String(err);
  }
});



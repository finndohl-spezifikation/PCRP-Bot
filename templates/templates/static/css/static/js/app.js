/* Paradise City Admin Dashboard \u2014 Frontend JS */

const $ = id => document.getElementById(id);
const fmt = n => typeof n === 'number' ? n.toLocaleString('de-DE') : (n ?? '\u2013');
const fmtMoney = n => (typeof n === 'number' ? (n < 0 ? `<span class="money-neg">-$${Math.abs(n).toLocaleString('de-DE')}</span>` : `<span class="money">$${n.toLocaleString('de-DE')}</span>`) : '\u2013');

// \u2500\u2500 Navigation \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

function goto(id) {
  document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
  const sec = document.getElementById('sec-' + id);
  if (sec) sec.classList.add('active');
  const nav = [...document.querySelectorAll('.nav-item')].find(n => n.getAttribute('onclick')?.includes("'" + id + "'"));
  if (nav) nav.classList.add('active');
  loadSection(id);
}

function switchTab(btn, show, hide) {
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  $(show).style.display = '';
  $(hide).style.display = 'none';
}

// \u2500\u2500 API helper \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

async function api(path, opts = {}) {
  try {
    const r = await fetch(path, { headers: {'Content-Type':'application/json'}, ...opts });
    if (!r.ok) return null;
    return await r.json();
  } catch { return null; }
}

// \u2500\u2500 Section loaders \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

function loadSection(id) {
  ({
    overview:    loadOverview,
    economy:     loadEconomy,
    warns:       loadWarns,
    inventories: loadInventories,
    shops:       loadShops,
    bans:        loadBans,
    blacklist:   loadBlacklist,
    logs:        loadLogs,
    warnings:    loadWarnings,
    invites:     loadInvites,
    players:     loadPlayers,
    notes:       loadNotes,
    status:      loadStatus,
  }[id] || (() => {}))();
}

// \u2500\u2500 Overview \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

async function loadOverview() {
  const [status, players, bans, warns, warnlog, logs] = await Promise.all([
    api('/api/status'), api('/api/players'), api('/api/bans'),
    api('/api/warns'), api('/api/warnings-log?limit=5'), api('/api/activity-log?limit=10'),
  ]);
  if (status) {
    $('stat-members').textContent = fmt(status.members);
    $('stat-latency').textContent = status.latency_ms ? status.latency_ms + ' ms' : '\u2013';
    $('stat-ram').textContent = status.ram_mb ? status.ram_mb + ' MB' : '\u2013';
  }
  if (players)  $('stat-players').textContent = fmt(players.count);
  if (bans)     $('stat-bans').textContent    = fmt(bans.length);
  if (warns)    $('stat-warns').textContent   = fmt(warns.reduce((s,w) => s + w.count, 0));
  if (warnlog)  renderWarningEntries(warnlog, 'overview-warnings');
  if (logs)     renderLogEntries(logs, 'overview-logs');
}

// \u2500\u2500 Economy \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

async function loadEconomy() {
  const rows = await api('/api/economy');
  if (!rows) return;
  $('eco-tbody').innerHTML = rows.length ? rows.map(r => `
    <tr data-search="${(r.name+' '+r.id).toLowerCase()}">
      <td><b>${esc(r.name)}</b></td>
      <td><span class="uid-small">${r.id}</span></td>
      <td>${fmtMoney(r.kasse)}</td>
      <td>${fmtMoney(r.bank)}</td>
      <td>${fmtMoney(r.gesamt)}</td>
      <td>${fmtMoney(r.dispo)}</td>
      <td>${r.schulden ? fmtMoney(-r.schulden) : '\u2013'}</td>
    </tr>`).join('') : '<tr><td colspan="7" class="loading">Keine Daten</td></tr>';
}

// \u2500\u2500 Warns \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

async function loadWarns() {
  const [w, tw] = await Promise.all([api('/api/warns'), api('/api/team-warns')]);
  renderWarnTable(w, 'warn-tbody', 4);
  renderWarnTable(tw, 'teamwarn-tbody', 4);
}

function renderWarnTable(rows, tbodyId, cols) {
  if (!rows) return;
  $(tbodyId).innerHTML = rows.length ? rows.map(r => `
    <tr data-search="${(r.name+' '+r.id).toLowerCase()}">
      <td><b>${esc(r.name)}</b></td>
      <td><span class="uid-small">${r.id}</span></td>
      <td><span class="badge badge-red">${r.count}</span></td>
      <td style="font-size:12px;color:var(--text-dim)">${r.warns.map(w=>esc(w.grund||w.reason||JSON.stringify(w))).join(' | ')}</td>
    </tr>`).join('') : `<tr><td colspan="${cols}" class="loading">Keine Verwarnungen</td></tr>`;
}

// \u2500\u2500 Inventories \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

async function loadInventories() {
  const rows = await api('/api/inventories');
  if (!rows) return;
  $('inv-tbody').innerHTML = rows.length ? rows.map(r => `
    <tr data-search="${(r.name+' '+r.id).toLowerCase()}">
      <td><b>${esc(r.name)}</b></td>
      <td><span class="uid-small">${r.id}</span></td>
      <td style="font-size:12px">${(r.inv||[]).join(', ') || '\u2013'}</td>
      <td style="font-size:12px">${(r.lager||[]).join(', ') || '\u2013'}</td>
    </tr>`).join('') : '<tr><td colspan="4" class="loading">Keine Inventare</td></tr>';
}

// \u2500\u2500 Shops \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

let _shopData = {};

async function loadShops() {
  const data = await api('/api/shops');
  if (!data) return;
  _shopData = data;

  const sel = $('shop-sel');
  sel.innerHTML = '<option value="">Shop w\xe4hlen\u2026</option>' +
    Object.keys(data).map(k => `<option value="${esc(k)}">${esc(k)}</option>`).join('');

  $('shop-panels').innerHTML = Object.entries(data).map(([shop, info]) => `
    <div class="shop-section" id="shopsec-${btoa(shop).replace(/=/g,'')}">
      <div class="shop-header">\U0001f3ea ${esc(shop)}</div>
      <div class="shop-items">
        ${(info.items||[]).length ? (info.items||[]).map((item,i) => `
          <div class="shop-item-row">
            <span>${esc(item.name || item.emoji+' '+item.itemname || JSON.stringify(item))}</span>
            <div style="display:flex;gap:12px;align-items:center">
              <span class="item-price">$${fmt(item.preis||item.price||0)}</span>
              <button class="btn-danger" onclick="deleteShopItem('${esc(shop)}',${i})">\U0001f5d1\ufe0f</button>
            </div>
          </div>`).join('') : '<div style="padding:12px 18px;color:var(--text-dim);font-size:13px">Keine Items</div>'}
      </div>
    </div>`).join('');
}

async function addShopItem() {
  const shop  = $('shop-sel').value;
  const emoji = $('shop-emoji').value.trim();
  const name  = $('shop-name').value.trim();
  const preis = $('shop-preis').value;
  const msg   = $('shop-msg');
  if (!shop || !name || !preis) { msg.className='form-msg err'; msg.textContent='\u274c Bitte alle Felder ausf\xfcllen.'; return; }
  const r = await api('/api/shop-item', { method:'POST', body: JSON.stringify({shop,emoji,name,preis:parseInt(preis)}) });
  if (r?.ok) {
    msg.className='form-msg ok'; msg.textContent='\u2705 Item hinzugef\xfcgt!';
    $('shop-emoji').value=''; $('shop-name').value=''; $('shop-preis').value='';
    loadShops();
  } else { msg.className='form-msg err'; msg.textContent='\u274c ' + (r?.error || 'Fehler'); }
}

async function deleteShopItem(shop, idx) {
  if (!confirm('Item wirklich l\xf6schen?')) return;
  const r = await api('/api/shop-item', { method:'DELETE', body: JSON.stringify({shop, index:idx}) });
  if (r?.ok) loadShops();
  else alert('Fehler beim L\xf6schen');
}

// \u2500\u2500 Bans \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

async function loadBans() {
  const bans = await api('/api/bans');
  renderBans(bans || []);
}

function renderBans(bans) {
  $('ban-tbody').innerHTML = bans.length ? bans.map(b => `
    <tr data-search="${(b.name+' '+b.id).toLowerCase()}">
      <td><b>${esc(b.name)}</b></td>
      <td><span class="uid-small">${b.id}</span></td>
      <td style="font-size:12px">${esc(b.reason||'\u2013')}</td>
      <td><button class="btn-success" onclick="unbanUser('${b.id}','${esc(b.name)}')">\u2705 Entbannen</button></td>
    </tr>`).join('') : '<tr><td colspan="4" class="loading">Keine gebannten Spieler</td></tr>';
}

async function refreshBans() {
  $('ban-tbody').innerHTML = '<tr><td colspan="4" class="loading">Aktualisiere\u2026</td></tr>';
  const bans = await api('/api/bans/refresh', { method:'POST' });
  renderBans(bans || []);
}

async function unbanUser(id, name) {
  if (!confirm(`${name} (${id}) wirklich entbannen?`)) return;
  const r = await api('/api/unban', { method:'POST', body: JSON.stringify({user_id:id}) });
  if (r?.ok) { alert('\u2705 Entbannt!'); loadBans(); }
  else alert('\u274c Fehler beim Entbannen');
}

// \u2500\u2500 Blacklist \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

async function loadBlacklist() {
  const bl = await api('/api/blacklist');
  if (!bl) return;
  $('bl-tbody').innerHTML = bl.length ? bl.map((e,i) => `
    <tr data-search="${(e.name+' '+(e.id||'')).toLowerCase()}">
      <td><b>${esc(e.name)}</b></td>
      <td><span class="uid-small">${e.id||'\u2013'}</span></td>
      <td style="font-size:12px">${esc(e.reason||'\u2013')}</td>
      <td style="font-size:11px;color:var(--text-dim)">${esc(e.added_at||'\u2013')}</td>
      <td><button class="btn-danger" onclick="deleteBlacklist(${i})">\U0001f5d1\ufe0f Entfernen</button></td>
    </tr>`).join('') : '<tr><td colspan="5" class="loading">Keine Eintr\xe4ge</td></tr>';
}

async function addBlacklist() {
  const name   = $('bl-name').value.trim();
  const discId = $('bl-id').value.trim();
  const reason = $('bl-reason').value.trim();
  if (!name && !discId) { alert('Name oder Discord-ID erforderlich'); return; }
  const r = await api('/api/blacklist', { method:'POST', body: JSON.stringify({name, discord_id:discId, reason}) });
  if (r?.ok) { $('bl-name').value=''; $('bl-id').value=''; $('bl-reason').value=''; loadBlacklist(); }
  else alert('\u274c Fehler');
}

async function deleteBlacklist(idx) {
  if (!confirm('Eintrag wirklich entfernen?')) return;
  const r = await api(`/api/blacklist/${idx}`, { method:'DELETE' });
  if (r?.ok) loadBlacklist();
}

// \u2500\u2500 Logs \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

let _allLogs = [];

async function loadLogs() {
  const logs = await api('/api/activity-log?limit=200');
  if (!logs) return;
  _allLogs = logs;
  filterLogs();
}

function filterLogs() {
  const q    = ($('log-search')?.value || '').toLowerCase();
  const type = $('log-type-filter')?.value || '';
  const filtered = _allLogs.filter(e =>
    (!type || e.type === type) &&
    (!q || (e.desc||'').toLowerCase().includes(q) || (e.user||'').includes(q))
  );
  renderLogEntries(filtered, 'log-list');
}

function renderLogEntries(entries, containerId) {
  const el = $(containerId);
  if (!el) return;
  if (!entries || !entries.length) { el.innerHTML = '<div style="color:var(--text-dim);font-size:13px">Keine Logs</div>'; return; }
  el.innerHTML = entries.map(e => `
    <div class="log-entry type-${e.type||''}">
      <div><span class="badge badge-orange" style="margin-right:8px">${e.type||'LOG'}</span>${esc(e.desc||'')}</div>
      ${e.user ? `<div class="uid-small">Nutzer: ${e.user}</div>` : ''}
      <div class="log-time">\U0001f550 ${e.time}</div>
    </div>`).join('');
}

// \u2500\u2500 Warnings \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

let _allWarnings = [];

async function loadWarnings() {
  const w = await api('/api/warnings-log?limit=200');
  if (!w) return;
  _allWarnings = w;
  filterWarnings();
}

function filterWarnings() {
  const q = ($('aw-search')?.value || '').toLowerCase();
  const filtered = _allWarnings.filter(e => !q || (e.title+e.desc).toLowerCase().includes(q));
  renderWarningEntries(filtered, 'aw-list');
}

function renderWarningEntries(entries, containerId) {
  const el = $(containerId);
  if (!el) return;
  if (!entries || !entries.length) { el.innerHTML = '<div style="color:var(--text-dim);font-size:13px">Keine Warnungen</div>'; return; }
  el.innerHTML = entries.map(e => `
    <div class="warn-entry">
      <div class="warn-entry-title">\U0001f6a8 ${esc(e.title||'Warnung')}</div>
      <div style="font-size:13px;margin-top:4px;white-space:pre-line">${esc(e.desc||'')}</div>
      <div class="log-time">\U0001f550 ${e.time}</div>
    </div>`).join('');
}

// \u2500\u2500 Invites \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

async function loadInvites() {
  const data = await api('/api/invites');
  if (!data) return;
  const entries = Object.entries(data);
  $('inv2-tbody').innerHTML = entries.length ? entries.map(([code, inv]) => `
    <tr data-search="${(inv.inviter_name||inv.inviter||code).toLowerCase()}">
      <td><b>${esc(inv.inviter_name || inv.inviter || '\u2013')}</b></td>
      <td><span class="uid-small">${inv.inviter_id||'\u2013'}</span></td>
      <td><code style="font-size:12px">${esc(code)}</code></td>
      <td><span class="badge badge-orange">${inv.uses||0}</span></td>
    </tr>`).join('') : '<tr><td colspan="4" class="loading">Keine Einladungsdaten</td></tr>';
}

// \u2500\u2500 Players \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

async function loadPlayers() {
  const data = await api('/api/players');
  if (!data) return;
  $('player-count').textContent = fmt(data.count);
  const players = Object.entries(data.players || {});
  $('pl-tbody').innerHTML = players.length ? players.map(([uid, m]) => `
    <tr data-search="${(m.name||uid).toLowerCase()}">
      <td><b>${esc(m.name||m.tag||uid)}</b></td>
      <td><span class="uid-small">${uid}</span></td>
    </tr>`).join('') : '<tr><td colspan="2" class="loading">Keine Spieler</td></tr>';
}

// \u2500\u2500 Notes \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

let _allNotes = {};

async function loadNotes() {
  const data = await api('/api/notes');
  if (!data) return;
  _allNotes = data;
  filterNotes();
}

function filterNotes() {
  const q = ($('note-search')?.value || '').toLowerCase();
  const $el = $('notes-list');
  const entries = Object.entries(_allNotes).filter(([uid, d]) =>
    !q || (d.name||uid).toLowerCase().includes(q) ||
    (d.notes||[]).some(n => (n.note||'').toLowerCase().includes(q))
  );
  if (!entries.length) { $el.innerHTML = '<div style="color:var(--text-dim)">Keine Notizen</div>'; return; }
  $el.innerHTML = entries.map(([uid, d]) => `
    <div class="note-card">
      <div class="note-user">\U0001f464 ${esc(d.name||uid)} <span class="uid-small">${uid}</span></div>
      ${(d.notes||[]).map((n,i) => `
        <div class="note-entry">
          <div>
            <div>${esc(n.note)}</div>
            <div class="note-time">\U0001f550 ${n.time||'\u2013'}</div>
          </div>
          <button class="btn-danger" onclick="deleteNote('${uid}',${i})">\U0001f5d1\ufe0f</button>
        </div>`).join('')}
    </div>`).join('');
}

async function addNote() {
  const uid  = $('note-uid').value.trim();
  const note = $('note-text').value.trim();
  if (!uid || !note) { alert('ID und Notiz erforderlich'); return; }
  const r = await api('/api/notes', { method:'POST', body: JSON.stringify({user_id:uid, note}) });
  if (r?.ok) { $('note-uid').value=''; $('note-text').value=''; loadNotes(); }
  else alert('\u274c Fehler');
}

async function deleteNote(uid, idx) {
  if (!confirm('Notiz l\xf6schen?')) return;
  const r = await api(`/api/notes/${uid}/${idx}`, { method:'DELETE' });
  if (r?.ok) loadNotes();
}

// \u2500\u2500 Status \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

async function loadStatus() {
  const s = await api('/api/status');
  if (!s) return;
  $('ss-ram').textContent    = s.ram_mb + ' MB';
  $('ss-cpu').textContent    = s.cpu_pct + '%';
  $('ss-disk').textContent   = s.disk_pct + '%';
  $('ss-lat').textContent    = s.latency_ms ? s.latency_ms + ' ms' : '\u2013';
  $('ss-uptime').textContent = s.uptime || '\u2013';
  $('ss-members').textContent= fmt(s.members);

  const fl = $('features-list');
  if (s.features && Object.keys(s.features).length) {
    fl.innerHTML = Object.entries(s.features).map(([name, f]) =>
      `<div class="feature-item ${f.ok?'feature-ok':'feature-err'}">
        ${f.ok ? '\U0001f7e2' : '\U0001f534'} ${esc(name)}
        ${!f.ok && f.err ? `<span style="font-size:11px;color:var(--text-dim)"> \u2014 ${esc(f.err)}</span>` : ''}
      </div>`).join('');
  } else {
    fl.innerHTML = '<div style="color:var(--text-dim)">Keine Feature-Daten</div>';
  }
}

// \u2500\u2500 Table filter \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

function filterTable(tbodyId, searchId) {
  const q = ($(searchId)?.value || '').toLowerCase();
  document.querySelectorAll(`#${tbodyId} tr[data-search]`).forEach(row => {
    row.style.display = row.getAttribute('data-search').includes(q) ? '' : 'none';
  });
}

// \u2500\u2500 Escape HTML \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

function esc(str) {
  if (str === null || str === undefined) return '';
  return String(str).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

// \u2500\u2500 Auto-refresh (live sections) \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

function autoRefresh() {
  const active = document.querySelector('.section.active')?.id?.replace('sec-','');
  if (active === 'logs')     loadLogs();
  if (active === 'warnings') loadWarnings();
  if (active === 'overview') loadOverview();
  if (active === 'status')   loadStatus();
  if (active === 'players')  loadPlayers();
}

setInterval(autoRefresh, 8000);

// \u2500\u2500 Init \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
loadSection('overview');

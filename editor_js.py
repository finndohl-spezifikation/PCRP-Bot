# -*- coding: utf-8 -*-
# editor_js.py -- Bot-Editor JavaScript (served via /editor.js)

EDITOR_JS = r"""
/* â”€â”€ Bot-Editor: Embeds, Buttons, Commands â”€â”€ */

async function loadEmbeds() {
  const [cfgs, btns] = await Promise.all([
    api('/api/embed-configs'),
    api('/api/button-configs'),
  ]);
  if (!cfgs || !btns) return;
  const main = document.querySelector('.main-content');

  function colorHex(val) {
    return '#' + (val || 0x2ECC71).toString(16).padStart(6, '0');
  }

  function embedCard(key, data) {
    const ch = colorHex(data.color);
    return '<div class="card" style="margin-bottom:20px">' +
      '<div class="card-header"><span class="card-icon">&#x1F4DD;</span> Embed: <b>' + esc(key) + '</b></div>' +
      '<div class="card-body">' +
        '<div style="display:grid;gap:12px">' +
          '<div><label class="form-label">Titel</label>' +
            '<input class="form-control" id="emb-title-' + key + '" value="' + esc(data.title || '') + '"></div>' +
          '<div><label class="form-label">Farbe</label>' +
            '<div style="display:flex;gap:8px;align-items:center">' +
              '<input type="color" id="emb-color-' + key + '" value="' + ch + '" style="width:50px;height:36px;border:none;background:none;cursor:pointer">' +
              '<input class="form-control" id="emb-colorhex-' + key + '" value="' + ch + '" style="max-width:130px">' +
            '</div></div>' +
          '<div><label class="form-label">Beschreibung (Discord Markdown, \\n = Zeilenumbruch)</label>' +
            '<textarea class="form-control" id="emb-desc-' + key + '" rows="8" style="font-family:monospace;font-size:12px;resize:vertical">' + esc(data.description || '') + '</textarea></div>' +
          '<div><label class="form-label">Footer-Text</label>' +
            '<input class="form-control" id="emb-footer-' + key + '" value="' + esc(data.footer || '') + '"></div>' +
        '</div>' +
        '<div style="display:flex;gap:10px;margin-top:16px;flex-wrap:wrap">' +
          '<button class="btn btn-primary" onclick="saveEmbed(\'' + key + '\')">&#x1F4BE; Speichern</button>' +
          '<button class="btn" style="background:var(--orange-1)" onclick="refreshEmbed(\'' + key + '\')">&#x1F504; Discord aktualisieren</button>' +
          '<button class="btn btn-secondary" onclick="resetEmbedDesc(\'' + key + '\')">&#x21A9; Beschreibung zur\u00fccksetzen</button>' +
        '</div>' +
        '<div id="emb-status-' + key + '" style="margin-top:8px;font-size:13px"></div>' +
      '</div></div>';
  }

  function btnCard(key, data) {
    const opts = ['success','danger','primary','secondary'];
    const selOpts = opts.map(function(o) {
      return '<option value="' + o + '"' + (data.style === o ? ' selected' : '') + '>' + o + '</option>';
    }).join('');
    return '<div class="card" style="margin-bottom:20px">' +
      '<div class="card-header"><span class="card-icon">&#x1F5B1;&#xFE0F;</span> Button: <b>' + esc(key) + '</b></div>' +
      '<div class="card-body">' +
        '<div style="display:grid;gap:12px">' +
          '<div><label class="form-label">Label (Text / Emoji)</label>' +
            '<input class="form-control" id="btn-label-' + key + '" value="' + esc(data.label || '') + '"></div>' +
          '<div><label class="form-label">Stil</label>' +
            '<select class="form-control" id="btn-style-' + key + '">' + selOpts + '</select></div>' +
        '</div>' +
        '<div style="display:flex;gap:10px;margin-top:16px">' +
          '<button class="btn btn-primary" onclick="saveButton(\'' + key + '\')">&#x1F4BE; Speichern</button>' +
        '</div>' +
        '<p style="margin-top:10px;padding:10px;background:rgba(255,255,255,0.04);border-radius:8px;font-size:12px;color:var(--text-dim)">' +
          '&#x2139;&#xFE0F; Nach dem Speichern unter <b>Embeds</b> auf <b>Discord aktualisieren</b> klicken, damit der neue Button-Text in Discord sichtbar wird.</p>' +
        '<div id="btn-status-' + key + '" style="margin-top:8px;font-size:13px"></div>' +
      '</div></div>';
  }

  const embedKeys = Object.keys(cfgs);
  const btnKeys   = Object.keys(btns);

  main.innerHTML =
    '<div class="page-header"><h1 class="page-title">&#x270F;&#xFE0F; Bot-Editor</h1></div>' +
    '<div style="display:flex;gap:8px;margin-bottom:24px;flex-wrap:wrap">' +
      '<button class="btn" id="edtab-embeds" style="background:var(--orange-1)" onclick="edTab(\'embeds\')">&#x1F4DD; Embeds</button>' +
      '<button class="btn btn-secondary" id="edtab-buttons" onclick="edTab(\'buttons\')">&#x1F5B1;&#xFE0F; Buttons</button>' +
      '<button class="btn btn-secondary" id="edtab-cmds" onclick="edTab(\'cmds\')">&#x2328;&#xFE0F; Commands</button>' +
    '</div>' +
    '<div id="ed-embeds">' + embedKeys.map(function(k) { return embedCard(k, cfgs[k]); }).join('') + '</div>' +
    '<div id="ed-buttons" style="display:none">' + btnKeys.map(function(k) { return btnCard(k, btns[k]); }).join('') + '</div>' +
    '<div id="ed-cmds" style="display:none">' +
      '<div class="card"><div class="card-header">&#x2328;&#xFE0F; Registrierte Slash-Commands</div>' +
      '<div class="card-body"><div id="cmds-inner">Laden...</div></div></div>' +
    '</div>';

  embedKeys.forEach(function(key) {
    var picker = document.getElementById('emb-color-' + key);
    var hex    = document.getElementById('emb-colorhex-' + key);
    if (picker && hex) {
      picker.addEventListener('input', function() { hex.value = picker.value; });
      hex.addEventListener('input', function() {
        if (/^#[0-9a-fA-F]{6}$/.test(hex.value)) picker.value = hex.value;
      });
    }
  });

  loadCmdsInner();
}

function edTab(tab) {
  ['embeds', 'buttons', 'cmds'].forEach(function(t) {
    var el = document.getElementById('ed-' + t);
    var bt = document.getElementById('edtab-' + t);
    if (el) el.style.display = (t === tab) ? '' : 'none';
    if (bt) {
      bt.style.background = (t === tab) ? 'var(--orange-1)' : '';
      bt.className = (t === tab) ? 'btn' : 'btn btn-secondary';
    }
  });
}

async function saveEmbed(key) {
  var st = document.getElementById('emb-status-' + key);
  var hexVal = (document.getElementById('emb-colorhex-' + key) || {}).value || '#000000';
  var colorInt = parseInt(hexVal.replace('#', ''), 16);
  var desc = (document.getElementById('emb-desc-' + key) || {}).value || '';
  var body = {
    title:       ((document.getElementById('emb-title-'  + key) || {}).value || ''),
    description: desc || null,
    color:       colorInt,
    footer:      ((document.getElementById('emb-footer-' + key) || {}).value || ''),
  };
  if (st) st.textContent = 'Speichern\u2026';
  var r = await fetch('/api/embed-configs/' + key, {
    method: 'PATCH',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(body),
  });
  var d = await r.json();
  if (st) st.innerHTML = d.ok ? '&#x2705; Gespeichert' : ('&#x274C; ' + esc(d.error || 'Fehler'));
}

async function resetEmbedDesc(key) {
  var ta = document.getElementById('emb-desc-' + key);
  if (ta) ta.value = '';
  await saveEmbed(key);
}

async function refreshEmbed(key) {
  var st = document.getElementById('emb-status-' + key);
  if (st) st.textContent = 'Wird in Discord aktualisiert\u2026';
  var r = await fetch('/api/embed-configs/' + key + '/refresh', {method: 'POST'});
  var d = await r.json();
  if (st) st.innerHTML = d.ok
    ? ('&#x2705; ' + esc(d.message || 'Aktualisiert'))
    : ('&#x274C; ' + esc(d.error || 'Fehler'));
}

async function saveButton(key) {
  var st = document.getElementById('btn-status-' + key);
  var body = {
    label: ((document.getElementById('btn-label-' + key) || {}).value || ''),
    style: ((document.getElementById('btn-style-' + key) || {}).value || 'success'),
  };
  if (st) st.textContent = 'Speichern\u2026';
  var r = await fetch('/api/button-configs/' + key, {
    method: 'PATCH',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(body),
  });
  var d = await r.json();
  if (st) st.innerHTML = d.ok
    ? '&#x2705; Gespeichert \u2014 Embed aktualisieren damit Button sichtbar wird'
    : ('&#x274C; ' + esc(d.error || 'Fehler'));
}

async function loadCmdsInner() {
  var wrap = document.getElementById('cmds-inner');
  if (!wrap) return;
  var cmds = await api('/api/bot-commands');
  if (!cmds || cmds.error) {
    wrap.innerHTML = '<span style="color:var(--text-dim)">Keine Commands geladen \u2014 Bot verbunden?</span>';
    return;
  }
  var rows = cmds.map(function(c) {
    return '<tr><td><code>/' + esc(c.name) + '</code></td><td>' + esc(c.description) + '</td></tr>';
  }).join('');
  wrap.innerHTML = '<table class="data-table"><thead><tr><th>Command</th><th>Beschreibung</th></tr></thead><tbody>' + rows + '</tbody></table>';
}

function loadButtons()  { loadEmbeds(); setTimeout(function() { edTab('buttons'); }, 80); }
function loadCommands() { loadEmbeds(); setTimeout(function() { edTab('cmds'); }, 80); }
function loadEditor()   { loadEmbeds(); }
"""

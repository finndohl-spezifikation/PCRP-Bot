// Universal Ban Guard — von allen PCRP-Seiten eingebunden
// Prüft beim Laden, ob der Nutzer via /bannen-dashboard gebannt wurde.
// Zeigt sofort den roten Sperrbildschirm wenn gebannt.

(function(){
  var banKey = 'pcrp-banned';

  // Bereits bekannt gebannt → sofort sperren
  if(localStorage.getItem(banKey) === '1'){
    showBanScreen();
    return;
  }

  // User-ID ermitteln: aus localStorage (Token/Chat/PD) oder URL-Param
  var userId = null;
  try {
    // CityChat / Autohaus
    var cc = localStorage.getItem('cc-me');
    if(cc){ var m = JSON.parse(cc); userId = m.id || m.userId; }
    // LAPD Dashboard
    if(!userId){ var pm = localStorage.getItem('pd-me');
      if(pm){ var p = JSON.parse(pm); userId = p.id || p.userId; }
    }
  } catch(e){}

  // URL-Parameter
  if(!userId){
    var q = new URLSearchParams(location.search);
    userId = q.get('userId') || q.get('user');
  }

  if(!userId) return; // Keine ID, kein Check möglich

  // API-Call
  fetch('/api/web/check-banned?userId=' + encodeURIComponent(userId))
    .then(function(r){ return r.json(); })
    .then(function(d){
      if(d && d.banned){
        localStorage.setItem(banKey, '1');
        showBanScreen();
      }
    })
    .catch(function(){});

  function showBanScreen(){
    var div = document.createElement('div');
    div.id = 'pcrp-ban-overlay';
    div.innerHTML = '<div style="position:fixed;inset:0;z-index:99999;display:flex;align-items:center;justify-content:center;text-align:center;padding:30px;background:radial-gradient(circle at 50% 40%,rgba(239,68,68,.38),#2a0505 72%);animation:banPulse 1.6s ease-in-out infinite;font-family:system-ui,sans-serif">'
      +'<style>@keyframes banPulse{0%,100%{background:radial-gradient(circle at 50% 40%,rgba(239,68,68,.34),#2a0505 72%)}50%{background:radial-gradient(circle at 50% 40%,rgba(239,68,68,.54),#2a0505 72%)}}</style>'
      +'<div style="max-width:460px;background:rgba(22,6,6,.94);border:2px solid #ef4444;border-radius:18px;padding:42px 34px;box-shadow:0 0 60px rgba(239,68,68,.5)">'
      +'<div style="font-size:3rem;margin-bottom:14px">🚫</div>'
      +'<h1 style="color:#ef4444;font-size:1.4rem;letter-spacing:2px;margin-bottom:14px;text-transform:uppercase">Zugriff gesperrt</h1>'
      +'<p style="color:#e8d9d9;font-size:.95rem;line-height:1.7">Du wurdest von dieser Seite gebannt.<br><br>Bist du der Meinung, es handelt sich um einen Fehler?<br>Dann kontaktiere bitte das Highteam.</p>'
      +'</div></div>';
    document.body.appendChild(div);
    // Seite dahinter ausblenden
    if(document.body) document.body.style.overflow = 'hidden';
  }
})();

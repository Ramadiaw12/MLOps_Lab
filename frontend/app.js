/* ===== MLOps Lab — Student Success — logique frontend =====
   Toutes les prédictions passent par l'API Flask (/api/…). Les simulateurs marqués « Simulation »
   sont purement pédagogiques et n'utilisent jamais un calcul JS comme prédiction réelle. */
(() => {
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];
  const API = '/api';
  const fmt = (x, d = 3) => (x === undefined || x === null || isNaN(x)) ? '—' : Number(x).toFixed(d);
  const toast = (m) => { const t = $('#toast'); t.textContent = m; t.classList.add('show'); setTimeout(() => t.classList.remove('show'), 2200); };
  const esc = (s) => String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));

  // ---------- Navigation ----------
  const pages = $$('section.page');
  function show(id) {
    if (!$('#' + id)) id = 'accueil';
    pages.forEach(p => p.classList.toggle('active', p.id === id));
    $$('#nav a').forEach(a => a.classList.toggle('active', a.getAttribute('href') === '#' + id));
    $('#crumbs').textContent = 'MLOps Lab · ' + $('#' + id).dataset.title;
    $('#sidebar').classList.remove('open');
    window.scrollTo({ top: 0 });
    if (id === 'monitoring') refreshMonitoring();
    if (id === 'versionnement') loadVersions();
  }
  window.addEventListener('hashchange', () => show(location.hash.slice(1)));
  $('#hamb').addEventListener('click', () => $('#sidebar').classList.toggle('open'));
  document.addEventListener('keydown', e => {           // navigation clavier ← →
    if (['INPUT', 'SELECT', 'TEXTAREA'].includes(e.target.tagName)) return;
    const links = $$('#nav a'); const i = links.findIndex(a => a.classList.contains('active'));
    if (e.key === 'ArrowRight' && i < links.length - 1) location.hash = links[i + 1].getAttribute('href');
    if (e.key === 'ArrowLeft' && i > 0) location.hash = links[i - 1].getAttribute('href');
  });

  // Boutons « copier » sur tous les blocs de code
  $$('pre').forEach(pre => {
    if (pre.closest('.sim') && pre.querySelector('#httpReq, #httpRes')) return;
    const b = document.createElement('button'); b.className = 'cp'; b.textContent = 'Copier';
    b.addEventListener('click', () => navigator.clipboard.writeText(pre.innerText.replace(/Copier$/, '').trim()).then(() => toast('Copié ✔')));
    pre.appendChild(b);
  });

  // ---------- API : état, métadonnées ----------
  let META = null, METRICS = null;
  async function api(path, opts) {
    const r = await fetch(API + path, { headers: { 'Content-Type': 'application/json' }, ...opts });
    const body = await r.json().catch(() => ({}));
    return { status: r.status, body };
  }
  async function checkApi() {
    try {
      const { status, body } = await api('/health');
      if (status !== 200) throw new Error();
      $('#apiStatus').innerHTML = `<span class="dot ok"></span>API en ligne · modèle v${body.model_version} (${body.model_type})`;
      $('#modeTag').textContent = '● Modèle réel (API Flask)'; $('#modeTag').className = 'tag real';
      $('#versionTag').textContent = 'modèle v' + body.model_version;
      $('#kVer').textContent = 'v' + body.model_version;
      const m = await api('/metadata'); META = m.body.metadata; METRICS = m.body.metrics;
      $('#kAcc').textContent = fmt(METRICS.accuracy);
      $('#mAcc').textContent = fmt(METRICS.accuracy); $('#mPrec').textContent = fmt(METRICS.precision);
      $('#mRec').textContent = fmt(METRICS.recall); $('#mF1').textContent = fmt(METRICS.f1);
      $('#metricSrc').textContent = `Métriques réelles du modèle v${METRICS.version} (${METRICS.model_type}) servies par l'API — ${METRICS.n_test} étudiants de test.`;
      $('#metaDump').textContent = JSON.stringify({ metadata: META, metrics: METRICS }, null, 2);
      const cm = METRICS.confusion_matrix; if (cm) { $('#cmTN').value = cm[0][0]; $('#cmFP').value = cm[0][1]; $('#cmFN').value = cm[1][0]; $('#cmTP').value = cm[1][1]; cmUpdate(); }
      const s = await api('/metrics'); $('#kPred').textContent = s.body.predictions; $('#kLat').textContent = fmt(s.body.latency_ms_avg, 1);
      return true;
    } catch {
      $('#apiStatus').innerHTML = '<span class="dot ko"></span>API hors ligne — voir Dépannage';
      $('#modeTag').textContent = '● API hors ligne'; $('#modeTag').className = 'tag';
      $('#metaDump').textContent = 'API non joignable. Démarrez la pile : docker compose up -d --build';
      return false;
    }
  }
  checkApi(); setInterval(checkApi, 15000);

  // ---------- Simulateur 1 : pipeline animé ----------
  const PIPE_TXT = ['Collecte des données (CSV synthétique).', 'Nettoyage, standardisation, séparation train/test.', 'Le modèle apprend les poids (fit).', 'Accuracy, précision, rappel, F1 sur le test.', 'model.joblib + metrics.json + metadata.json = version v1.', 'API Flask dans Docker, servie derrière Nginx.', 'Latence, erreurs, dérive des données.', 'Nouvelles données → v2 → comparaison → redéploiement. La boucle recommence !'];
  let pipeTimer = null;
  function pipeRun() {
    pipeReset(); const st = $$('#pipeline .st'); let i = 0;
    pipeTimer = setInterval(() => {
      if (i > 0) { st[i - 1].classList.remove('on'); st[i - 1].classList.add('done'); }
      if (i >= st.length) { clearInterval(pipeTimer); $('#pipeOut').textContent = '✅ Cycle complet. Le MLOps est une boucle : la surveillance déclenche le réentraînement.'; return; }
      st[i].classList.add('on'); $('#pipeOut').textContent = `Étape ${i + 1}/8 — ${st[i].textContent.trim()} : ${PIPE_TXT[i]}`; i++;
    }, 900);
  }
  function pipeReset() { clearInterval(pipeTimer); $$('#pipeline .st').forEach(s => s.classList.remove('on', 'done')); $('#pipeOut').textContent = 'Prêt. Chaque étape sera expliquée au passage.'; }

  // ---------- Simulateur 2 : dataset interactif (génération JS locale, même logique que le notebook) ----------
  function rng(seed) { let s = seed >>> 0; return () => { s = (s * 1664525 + 1013904223) >>> 0; return s / 4294967296; }; }
  function normal(r) { return Math.sqrt(-2 * Math.log(r() || 1e-9)) * Math.cos(2 * Math.PI * r()); }
  function genRows(n, seed = 42) {
    const r = rng(seed), rows = [];
    for (let i = 0; i < n; i++) {
      const note = Math.min(20, Math.max(0, 11.5 + 3.2 * normal(r))), abs = Math.max(0, Math.min(30, Math.round(5 + 2.2 * normal(r)))), part = Math.min(10, Math.max(0, 6 + 2 * normal(r)));
      const score = 0.55 * (note - 10) - 0.18 * (abs - 5) + 0.35 * (part - 5), p = 1 / (1 + Math.exp(-score));
      rows.push({ note: +note.toFixed(1), absences: abs, participation: +part.toFixed(1), reussite: r() < p ? 1 : 0 });
    }
    return rows;
  }
  let dsRows = [], dsSort = { k: null, asc: true };
  function dsRender() {
    const rows = [...dsRows]; if (dsSort.k) rows.sort((a, b) => (a[dsSort.k] - b[dsSort.k]) * (dsSort.asc ? 1 : -1));
    const cols = ['note', 'absences', 'participation', 'reussite'];
    $('#dsTable').innerHTML = `<table><thead><tr>${cols.map(c => `<th data-k="${c}" class="${dsSort.k === c ? 'sorted' : ''}">${c}</th>`).join('')}</tr></thead><tbody>${rows.map(r => `<tr>${cols.map(c => `<td>${c === 'reussite' ? (r[c] ? '<span class="tag real">1 · réussite</span>' : '<span class="tag" style="color:var(--danger)">0 · échec</span>') : r[c]}</td>`).join('')}</tr>`).join('')}</tbody></table>`;
    $$('#dsTable th').forEach(th => th.addEventListener('click', () => { dsSort = { k: th.dataset.k, asc: dsSort.k === th.dataset.k ? !dsSort.asc : true }; dsRender(); }));
    const rate = dsRows.reduce((s, r) => s + r.reussite, 0) / dsRows.length;
    $('#dsOut').innerHTML = `<b>${dsRows.length} lignes</b> · taux de réussite : <b>${(100 * rate).toFixed(0)} %</b> · note moyenne : ${(dsRows.reduce((s, r) => s + r.note, 0) / dsRows.length).toFixed(1)}/20`;
  }
  function dsGen() { dsRows = genRows(+$('#dsN').value || 12, 42 + (+$('#dsN').value || 12)); dsSort = { k: null, asc: true }; dsRender(); }

  // ---------- Simulateur 3 : visualisation des variables ----------
  const VIZ_EXPL = { note: 'La note sépare nettement les classes : c\'est la variable la plus informative (poids le plus élevé).', absences: 'Les absences décalent la distribution vers la droite pour la classe « échec » : effet négatif mais plus faible.', participation: 'La participation aide modérément : les deux courbes se chevauchent davantage.' };
  function vizRender() {
    const v = $('#vizVar').value, rows = genRows(600, 7), max = { note: 20, absences: 30, participation: 10 }[v], bins = 15;
    const h = [new Array(bins).fill(0), new Array(bins).fill(0)];
    rows.forEach(r => h[r.reussite][Math.min(bins - 1, Math.floor(r[v] / max * bins))]++);
    const W = 640, H = 220, pad = 30, top = Math.max(...h[0], ...h[1]), bw = (W - 2 * pad) / bins;
    let svg = `<svg class="chart" viewBox="0 0 ${W} ${H}" width="100%"><line x1="${pad}" y1="${H - pad}" x2="${W - pad}" y2="${H - pad}" stroke="#cbd5e1"/>`;
    for (let i = 0; i < bins; i++) {
      const y0 = (H - pad) - h[0][i] / top * (H - 2 * pad), y1 = (H - pad) - h[1][i] / top * (H - 2 * pad);
      svg += `<rect x="${pad + i * bw + 1}" y="${y1}" width="${bw / 2 - 1}" height="${H - pad - y1}" fill="#16a34a" opacity=".8"/><rect x="${pad + i * bw + bw / 2}" y="${y0}" width="${bw / 2 - 1}" height="${H - pad - y0}" fill="#dc2626" opacity=".8"/>`;
      if (i % 3 === 0) svg += `<text x="${pad + i * bw}" y="${H - 10}">${(i / bins * max).toFixed(0)}</text>`;
    }
    svg += `<text x="${W - 150}" y="18"><tspan fill="#16a34a">■</tspan> réussite <tspan fill="#dc2626">■</tspan> échec</text></svg>`;
    $('#vizChart').innerHTML = svg; $('#vizExpl').innerHTML = `<b>Explication :</b> ${VIZ_EXPL[v]} <b>Vérification :</b> la variable « note » doit être la plus séparatrice.`;
  }
  $('#vizVar').addEventListener('change', vizRender);

  // ---------- Simulateur 4 : train/test ----------
  function splitRender() {
    const p = +$('#splitR').value, n = 1000, nt = Math.round(n * p / 100);
    $('#splitViz').innerHTML = `<div style="display:flex;height:34px;border-radius:8px;overflow:hidden;border:1px solid var(--line)"><div style="width:${100 - p}%;background:var(--primary);color:#fff;display:grid;place-items:center;font-size:13px">Entraînement ${100 - p} %</div><div style="width:${p}%;background:var(--warn);color:#fff;display:grid;place-items:center;font-size:13px">Test ${p} %</div></div>`;
    $('#splitOut').innerHTML = `<code>train_test_split(X, y, test_size=${(p / 100).toFixed(2)}, random_state=42, stratify=y)</code> → <b>${n - nt}</b> lignes d'entraînement, <b>${nt}</b> de test.`;
  }
  $('#splitR').addEventListener('input', splitRender);

  // ---------- Simulateur 5 : matrice de confusion ----------
  function cmUpdate() {
    const TN = +$('#cmTN').value || 0, FP = +$('#cmFP').value || 0, FN = +$('#cmFN').value || 0, TP = +$('#cmTP').value || 0, tot = TN + FP + FN + TP || 1;
    const acc = (TP + TN) / tot, prec = TP / ((TP + FP) || 1), rec = TP / ((TP + FN) || 1), f1 = (prec + rec) ? 2 * prec * rec / (prec + rec) : 0;
    $('#cmOut').innerHTML = `<table><tr><td>Accuracy</td><td><b>${fmt(acc)}</b></td><td class="mini">(${TP}+${TN})/${tot}</td></tr><tr><td>Précision</td><td><b>${fmt(prec)}</b></td><td class="mini">${TP}/(${TP}+${FP})</td></tr><tr><td>Rappel</td><td><b>${fmt(rec)}</b></td><td class="mini">${TP}/(${TP}+${FN})</td></tr><tr><td>F1</td><td><b>${fmt(f1)}</b></td><td class="mini">2·P·R/(P+R)</td></tr></table>`;
  }
  ['#cmTN', '#cmFP', '#cmFN', '#cmTP'].forEach(s => $(s).addEventListener('input', cmUpdate));
  function cmReset() { const cm = METRICS && METRICS.confusion_matrix || [[40, 25], [20, 115]]; $('#cmTN').value = cm[0][0]; $('#cmFP').value = cm[0][1]; $('#cmFN').value = cm[1][0]; $('#cmTP').value = cm[1][1]; cmUpdate(); }

  // ---------- Simulateur 6 : requêtes HTTP (réelles) ----------
  async function httpSend() {
    const sel = $('#httpSel').value; let path, opts = {}, bodyObj = null;
    if (sel === 'GET /health') path = '/health'; else if (sel === 'GET /metadata') path = '/metadata';
    else if (sel === 'GET /predict') path = '/predict'; else if (sel === 'GET /inconnu') path = '/inconnu';
    else { path = '/predict'; bodyObj = sel.endsWith('ok') ? { note: 14, absences: 2, participation: 8 } : sel.endsWith('bad') ? { note: 25, absences: 2, participation: 8 } : { note: 14, absences: 2 }; opts = { method: 'POST', body: JSON.stringify(bodyObj) }; }
    $('#httpReq').textContent = `${opts.method || 'GET'} ${API}${path} HTTP/1.1\nHost: 127.0.0.1:8501\nContent-Type: application/json${bodyObj ? '\n\n' + JSON.stringify(bodyObj, null, 2) : ''}`;
    $('#httpRes').textContent = 'envoi…';
    try { const { status, body } = await api(path, opts); $('#httpRes').textContent = `HTTP ${status}\n\n${JSON.stringify(body, null, 2)}`; }
    catch (e) { $('#httpRes').textContent = 'Erreur réseau : API hors ligne ? ' + e; }
  }

  // ---------- Simulateur 7 : terminal Docker pédagogique ----------
  const TERM = {
    help: 'Commandes connues : docker --version · docker ps · docker ps -a · docker images · docker compose up -d --build · docker compose ps · docker compose logs api · docker compose down · clear',
    'docker --version': 'Docker version 28.x, build (simulé)',
    'docker ps': 'CONTAINER ID   IMAGE                       STATUS                   PORTS                      NAMES\n3f2a9c1e77b1   mlops-lab/frontend:latest   Up 2 minutes (healthy)   127.0.0.1:8501->80/tcp     mlops-frontend\nb81d0e5f4a22   mlops-lab/api:latest        Up 2 minutes (healthy)   127.0.0.1:5000->5000/tcp   mlops-api',
    'docker ps -a': '(idem docker ps, plus les conteneurs arrêtés — colonne STATUS : Exited (0))',
    'docker images': 'REPOSITORY            TAG       SIZE\nmlops-lab/frontend    latest    52MB\nmlops-lab/api         latest    412MB\npython                3.12-slim 125MB\nnginx                 1.27-alpine 48MB',
    'docker compose up -d --build': '[+] Building 12.4s (18/18) FINISHED\n[+] Running 3/3\n ✔ Network mlops-lab-student-success_mlops-net  Created\n ✔ Container mlops-api                          Healthy\n ✔ Container mlops-frontend                     Started',
    'docker compose ps': 'NAME             IMAGE                       STATUS                   PORTS\nmlops-api        mlops-lab/api:latest        running (healthy)        127.0.0.1:5000->5000/tcp\nmlops-frontend   mlops-lab/frontend:latest   running (healthy)        127.0.0.1:8501->80/tcp',
    'docker compose logs api': '{"ts": "...", "level": "INFO", "msg": "model loaded", "version": 1, "model_type": "logreg"}\n{"ts": "...", "level": "INFO", "msg": "prediction", "input": {"note": 14.0, "absences": 2.0, "participation": 8.0}, "prediction": 1, "proba": 0.964, "latency_ms": 2.1}',
    'docker compose down': '[+] Running 3/3\n ✔ Container mlops-frontend  Removed\n ✔ Container mlops-api       Removed\n ✔ Network mlops-net         Removed',
  };
  function termRun(cmd) {
    const t = $('#term'), inp = $('#termIn'), line = document.createElement('div'); line.innerHTML = `<span class="dim">$</span> ${esc(cmd)}`; t.insertBefore(line, inp.parentElement);
    if (cmd === 'clear') { $$('#term > div:not(.in)').forEach(d => d.remove()); return; }
    const out = document.createElement('pre'); out.style.cssText = 'background:none;padding:4px 0;margin:0;white-space:pre-wrap';
    const k = cmd.trim().replace(/\s+/g, ' ');
    out.className = TERM[k] ? 'ok' : 'err'; out.textContent = TERM[k] || `commande inconnue dans ce simulateur : « ${cmd} » — tapez help`; t.insertBefore(out, inp.parentElement); inp.value = ''; t.scrollTop = t.scrollHeight;
  }
  $('#termIn').addEventListener('keydown', e => { if (e.key === 'Enter' && e.target.value.trim()) termRun(e.target.value); });

  // ---------- Simulateur 8 : prédiction réelle ----------
  const sync = () => { $('#vNote').textContent = $('#fNote').value; $('#vAbs').textContent = $('#fAbs').value; $('#vPart').textContent = $('#fPart').value; };
  ['#fNote', '#fAbs', '#fPart'].forEach(s => $(s).addEventListener('input', sync));
  async function predict() {
    const payload = { note: +$('#fNote').value, absences: +$('#fAbs').value, participation: +$('#fPart').value };
    $('#predReq').textContent = `POST /api/predict ${JSON.stringify(payload)}`; $('#predOut').textContent = 'Interrogation du modèle…';
    try {
      const { status, body } = await api('/predict', { method: 'POST', body: JSON.stringify(payload) });
      $('#predJson').textContent = JSON.stringify(body, null, 2);
      if (status !== 200) { $('#predOut').innerHTML = `<span style="color:var(--danger)"><b>Erreur ${status}</b> — ${esc(body.error || '')}</span>`; return; }
      const ok = body.prediction === 1, p = body.probability_success;
      $('#predOut').innerHTML = `<div style="font-size:22px;font-weight:700;color:${ok ? 'var(--success)' : 'var(--danger)'}">${ok ? '✅' : '⚠️'} ${esc(body.label)}</div><div class="mini" style="margin-top:6px">Classe prédite : <b>${body.prediction}</b> · modèle v${body.model_version} (${body.model_type}) · latence ${body.latency_ms} ms · <span class="tag real">${esc(body.mode)}</span></div>`;
      $('#predBar').style.width = (100 * p).toFixed(0) + '%'; $('#predBar').style.background = ok ? 'var(--success)' : 'var(--danger)';
      $('#predProba').textContent = `Probabilité de réussite estimée : ${(100 * p).toFixed(1)} %`;
      $('#kPred').textContent = (+$('#kPred').textContent || 0) + 1;
    } catch (e) { $('#predOut').innerHTML = '<span style="color:var(--danger)">API non joignable. Vérifiez que la pile Docker est démarrée (section Dépannage).</span>'; }
  }
  function predExample(k) { const v = k === 'good' ? [17, 1, 9] : [7, 15, 2]; $('#fNote').value = v[0]; $('#fAbs').value = v[1]; $('#fPart').value = v[2]; sync(); predict(); }
  function predReset() { $('#fNote').value = 14; $('#fAbs').value = 2; $('#fPart').value = 8; sync(); $('#predOut').textContent = 'Aucune prédiction pour l\'instant.'; $('#predBar').style.width = '0'; $('#predProba').textContent = ''; $('#predJson').textContent = '—'; $('#predReq').textContent = '—'; }

  // ---------- Monitoring ----------
  async function refreshMonitoring() {
    try {
      const { body: s } = await api('/metrics'), { body: logs } = await api('/logs');
      $('#monReq').textContent = s.requests; $('#monPred').textContent = s.predictions; $('#monErr').textContent = s.errors;
      $('#monLat').textContent = `${fmt(s.latency_ms_avg, 1)} / ${fmt(s.latency_ms_max, 1)}`;
      const c0 = s.class_counts['0'], c1 = s.class_counts['1'], tot = c0 + c1 || 1;
      $('#monDist').innerHTML = `<div class="mini">Classe 1 (réussite) : ${c1} · Classe 0 (échec) : ${c0}</div><div style="display:flex;height:28px;border-radius:8px;overflow:hidden;margin-top:6px;border:1px solid var(--line)"><div style="width:${100 * c1 / tot}%;background:var(--success)"></div><div style="width:${100 * c0 / tot}%;background:var(--danger)"></div></div><p class="mini" style="margin-top:8px">Une dérive brutale de cette répartition est un signal d'alerte : les données réelles ne ressemblent plus à celles de l'entraînement.</p>`;
      $('#monLogs').innerHTML = logs.length ? `<table><tr><th>Heure (UTC)</th><th>note</th><th>abs.</th><th>part.</th><th>préd.</th><th>p(1)</th><th>ms</th></tr>${logs.map(l => `<tr><td>${l.ts.slice(11, 19)}</td><td>${l.input.note}</td><td>${l.input.absences}</td><td>${l.input.participation}</td><td>${l.prediction}</td><td>${fmt(l.probability_success, 2)}</td><td>${l.latency_ms}</td></tr>`).join('')}</table>` : '<p class="mini">Aucune prédiction encore. Utilisez le simulateur (section 14) ou « Générer 20 requêtes ».</p>';
    } catch { $('#monLogs').innerHTML = '<p class="mini" style="color:var(--danger)">API hors ligne.</p>'; }
  }
  setInterval(() => { if ($('#monAuto').checked && $('#monitoring').classList.contains('active')) refreshMonitoring(); }, 5000);
  async function monLoad() {
    const r = rng(Date.now() & 0xffff);
    for (let i = 0; i < 20; i++) await api('/predict', { method: 'POST', body: JSON.stringify({ note: +(r() * 20).toFixed(1), absences: Math.round(r() * 30), participation: +(r() * 10).toFixed(1) }) });
    toast('20 requêtes envoyées'); refreshMonitoring();
  }

  // ---------- Comparateur de versions ----------
  async function loadVersions() {
    try {
      const { body: vs } = await api('/versions');
      if (!vs.length) { $('#verTable').innerHTML = '<p class="mini">Aucune version trouvée.</p>'; return; }
      const keys = ['accuracy', 'precision', 'recall', 'f1'];
      $('#verTable').innerHTML = `<table><tr><th>Version</th><th>Modèle</th><th>Données</th>${keys.map(k => `<th>${k}</th>`).join('')}<th>Entraîné le</th><th>État</th></tr>${vs.map(v => `<tr><td><b>v${v.metrics.version}</b></td><td>${v.metrics.model_type}</td><td>${v.metadata.dataset ? v.metadata.dataset.rows + ' lignes, drift ' + v.metadata.dataset.drift : '—'}</td>${keys.map(k => `<td>${fmt(v.metrics[k])}</td>`).join('')}<td class="mini">${(v.metadata.trained_at || '').slice(0, 16).replace('T', ' ')}</td><td>${v.active ? '<span class="tag real">active</span>' : '<span class="tag">disponible</span>'}</td></tr>`).join('')}</table>`;
      if (vs.length >= 2) { const a = vs[0].metrics, b = vs[vs.length - 1].metrics, d = b.f1 - a.f1; $('#verOut').innerHTML = `F1 : v${a.version} = ${fmt(a.f1)} → v${b.version} = ${fmt(b.f1)} (${d >= 0 ? '+' : ''}${fmt(d)}). ${d >= 0 ? 'La nouvelle version fait au moins aussi bien : candidate au déploiement.' : 'La nouvelle version régresse : ne pas déployer sans analyse.'} <span class="mini">Attention : jeux de test différents (dérive).</span>`; }
      else $('#verOut').textContent = 'Une seule version. Entraînez une v2 (commande ci-dessus) puis rechargez.';
    } catch { $('#verTable').innerHTML = '<p class="mini" style="color:var(--danger)">API hors ligne.</p>'; }
  }

  // ---------- QCM ----------
  const QCM = [
    ['Quelle est la variable cible du projet ?', ['note', 'reussite', 'participation', 'absences'], 1, 'La cible (target) est ce que l\'on cherche à prédire : reussite (0/1).'],
    ['Pourquoi sépare-t-on un jeu de test ?', ['Pour accélérer l\'entraînement', 'Pour mesurer la performance sur des données jamais vues', 'Pour réduire la taille du fichier', 'Parce que scikit-learn l\'exige'], 1, 'Évaluer sur le train donnerait une mesure trompeuse (surapprentissage).'],
    ['Que contient model.joblib ?', ['Seulement les poids', 'Le Pipeline complet (scaler + modèle)', 'Le dataset', 'Les logs'], 1, 'Le Pipeline sérialisé inclut la standardisation : l\'API n\'a rien à refaire.'],
    ['Précision = ?', ['VP/(VP+FN)', 'VP/(VP+FP)', '(VP+VN)/total', '2PR/(P+R)'], 1, 'Précision : parmi les prédits positifs, combien le sont vraiment.'],
    ['Quel code HTTP renvoie l\'API si note = 25 ?', ['200', '404', '400', '500'], 2, '400 Bad Request : l\'entrée est invalide (hors plage 0-20).'],
    ['Un Dockerfile est…', ['Un conteneur en cours d\'exécution', 'La recette pour construire une image', 'Un volume', 'Un réseau'], 1, 'Dockerfile → (build) → Image → (run) → Conteneur.'],
    ['Que fait « docker compose up -d --build » ?', ['Supprime les conteneurs', 'Reconstruit les images et démarre les services en arrière-plan', 'Affiche les logs', 'Met à jour Docker Desktop'], 1, '-d = détaché, --build = reconstruire.'],
    ['Pourquoi publier les ports sur 127.0.0.1 ?', ['C\'est plus rapide', 'Pour n\'exposer les services qu\'au Mac local', 'Nginx l\'impose', 'Pour éviter les conflits de noms'], 1, 'Rien n\'est accessible depuis le réseau Wi-Fi.'],
    ['Le rôle de Nginx dans ce projet ?', ['Entraîner le modèle', 'Servir le site et relayer /api/ vers Flask', 'Stocker les artefacts', 'Remplacer Docker'], 1, 'Reverse proxy : une seule origine pour le navigateur.'],
    ['Qu\'est-ce que la dérive des données (data drift) ?', ['Un bug de code', 'Les données réelles s\'éloignent de celles de l\'entraînement', 'Une perte de fichiers', 'Une erreur 404'], 1, 'Le modèle n\'a pas changé mais le monde oui → réentraîner.'],
    ['Quel fichier décrit version, date, graine et bibliothèques ?', ['metrics.json', 'metadata.json', 'compose.yaml', 'app.py'], 1, 'metadata.json = carte d\'identité du modèle.'],
    ['Un test d\'intégration vérifie…', ['Une fonction isolée', 'Le dialogue réel entre frontend, Nginx et API', 'La syntaxe Python', 'La couleur des boutons'], 1, 'Il faut la pile Docker démarrée.'],
  ];
  function qcmRender() {
    $('#qcmBody').innerHTML = QCM.map((q, i) => `<div class="q" data-i="${i}"><b>${i + 1}. ${q[0]}</b>${q[1].map((o, j) => `<label><input type="radio" name="q${i}" value="${j}"> ${o}</label>`).join('')}<div class="fb"></div></div>`).join('');
    $('#qcmScore').textContent = ''; $('#qcmBar').style.width = '0';
  }
  function qcmCheck() {
    let score = 0;
    QCM.forEach((q, i) => {
      const sel = $(`input[name=q${i}]:checked`), box = $(`.q[data-i="${i}"]`), fb = $('.fb', box);
      $$('label', box).forEach(l => l.classList.remove('good', 'bad'));
      const labels = $$('label', box); labels[q[2]].classList.add('good');
      if (sel && +sel.value === q[2]) { score++; fb.innerHTML = '✅ Correct. ' + q[3]; }
      else { if (sel) labels[+sel.value].classList.add('bad'); fb.innerHTML = (sel ? '❌ Incorrect. ' : '⚠️ Sans réponse. ') + q[3]; }
    });
    $('#qcmScore').textContent = `Score : ${score} / ${QCM.length} ${score >= 10 ? '🏆 Excellent' : score >= 7 ? '👍 Bien' : '📚 À revoir'}`;
    $('#qcmBar').style.width = (100 * score / QCM.length) + '%';
  }

  // ---------- Glossaire ----------
  const GLO = [['Accuracy', 'Proportion de prédictions correctes sur le jeu de test.'], ['API REST', 'Interface permettant à des programmes de dialoguer par HTTP et JSON.'], ['Artefact', 'Fichier produit par l\'entraînement : modèle, métriques, métadonnées.'], ['Classification', 'Tâche où le modèle prédit une catégorie (ici 0 ou 1).'], ['Conteneur', 'Instance isolée et en cours d\'exécution d\'une image Docker.'], ['Data drift (dérive des données)', 'Changement de la distribution des données réelles par rapport à l\'entraînement.'], ['Dockerfile', 'Fichier texte décrivant comment construire une image.'], ['Docker Compose', 'Outil décrivant et lançant plusieurs conteneurs avec un fichier YAML.'], ['Feature', 'Variable d\'entrée du modèle (note, absences, participation).'], ['F1-score', 'Moyenne harmonique de la précision et du rappel.'], ['Flask', 'Micro-framework web Python utilisé pour l\'API.'], ['Fuite de données', 'Utilisation involontaire d\'informations du test pendant l\'entraînement.'], ['Gunicorn', 'Serveur WSGI de production qui exécute l\'application Flask.'], ['Healthcheck', 'Sonde périodique vérifiant qu\'un conteneur est en bonne santé.'], ['Image', 'Modèle figé et versionné à partir duquel on crée des conteneurs.'], ['Inférence', 'Utilisation d\'un modèle entraîné pour prédire sur de nouvelles données.'], ['JSON', 'Format texte d\'échange de données (clés/valeurs).'], ['joblib', 'Bibliothèque Python pour sérialiser un modèle scikit-learn.'], ['Latence', 'Temps de réponse d\'une requête.'], ['Matrice de confusion', 'Tableau croisant classes réelles et prédites.'], ['MLOps', 'Pratiques pour industrialiser le cycle de vie des modèles ML.'], ['Monitoring', 'Surveillance d\'un service en production (requêtes, erreurs, latence).'], ['Nginx', 'Serveur web utilisé ici comme serveur statique et reverse proxy.'], ['Pipeline (scikit-learn)', 'Enchaînement de transformations et d\'un modèle, sauvegardé d\'un bloc.'], ['Précision', 'Parmi les prédictions positives, proportion de vrais positifs.'], ['Rappel', 'Parmi les positifs réels, proportion détectée par le modèle.'], ['Régression logistique', 'Modèle linéaire de classification produisant une probabilité.'], ['Reverse proxy', 'Serveur qui relaie les requêtes vers un autre service.'], ['Seed (graine)', 'Valeur fixant le générateur aléatoire pour reproduire les résultats.'], ['StandardScaler', 'Transformation ramenant chaque variable à moyenne 0 et écart-type 1.'], ['Target', 'Variable à prédire.'], ['Train/Test', 'Découpage des données en apprentissage et évaluation.'], ['Versionnement', 'Identification et conservation de chaque version du modèle (v1, v2…).'], ['Volume', 'Stockage persistant attaché à un conteneur.']];
  function gloRender(f = '') { $('#glo').innerHTML = GLO.filter(g => (g[0] + g[1]).toLowerCase().includes(f.toLowerCase())).map(g => `<dt>${g[0]}</dt><dd>${g[1]}</dd>`).join('') || '<dd>Aucun terme.</dd>'; }
  $('#gloSearch').addEventListener('input', e => gloRender(e.target.value));

  // ---------- Actions (délégation) ----------
  const ACT = { 'pipe-run': pipeRun, 'pipe-reset': pipeReset, 'ds-gen': dsGen, 'ds-reset': () => { $('#dsN').value = 12; dsGen(); }, 'viz-reset': () => { $('#vizVar').value = 'note'; vizRender(); }, 'split-reset': () => { $('#splitR').value = 20; splitRender(); }, 'cm-reset': cmReset, 'http-send': httpSend, 'http-reset': () => { $('#httpReq').textContent = 'Requête…'; $('#httpRes').textContent = 'Réponse…'; }, 'term-reset': () => { $$('#term > div:not(.in), #term > pre').forEach(d => d.remove()); }, 'predict': predict, 'pred-example': (b) => predExample(b.dataset.ex), 'pred-reset': predReset, 'mon-refresh': refreshMonitoring, 'mon-load': monLoad, 'ver-load': loadVersions, 'qcm-check': qcmCheck, 'qcm-reset': qcmRender };
  document.addEventListener('click', e => { const b = e.target.closest('[data-act]'); if (b && ACT[b.dataset.act]) ACT[b.dataset.act](b); });

  // ---------- Init ----------
  dsGen(); vizRender(); splitRender(); cmUpdate(); qcmRender(); gloRender(); sync();
  show(location.hash.slice(1) || 'accueil');
})();

(() => {
  const $ = s => document.querySelector(s);
  const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const norm = s => String(s||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();
  const MES = {enero:0,febrero:1,marzo:2,abril:3,mayo:4,junio:5,julio:6,agosto:7,septiembre:8,octubre:9,noviembre:10,diciembre:11};
  const fechaNum = p => { const m = norm(p.fecha).match(/(\d+)\s+de\s+(\w+)\s+de\s+(\d+)/); return m ? new Date(+m[3], MES[m[2]], +m[1]).getTime() : 0; };

  let DATA = [], carrera = 'Todas';
  const cg = $('#cg'); addEventListener('mousemove', e => { cg.style.left = e.clientX+'px'; cg.style.top = e.clientY+'px'; });

  fetch('data/proyectos.json').then(r => r.json()).then(d => {
    DATA = d.map(p => ({...p, _s: norm([p.titulo,p.caso,p.autor,p.carrera,p.fecha].join(' '))}));
    const cars = ['Todas', ...new Set(DATA.map(p => p.carrera))];
    $('#chips').innerHTML = cars.map(c => `<button class="chip ${c===carrera?'on':''}" data-c="${esc(c)}">${esc(c)}</button>`).join('');
    render();
  }).catch(() => { $('#grid').innerHTML = '<div class="empty">No se pudieron cargar los proyectos.</div>'; });

  $('#chips').addEventListener('click', e => {
    const b = e.target.closest('.chip'); if (!b) return;
    carrera = b.dataset.c;
    document.querySelectorAll('.chip').forEach(c => c.classList.toggle('on', c === b));
    render();
  });
  $('#q').addEventListener('input', render);
  $('#sort').addEventListener('change', render);

  function render() {
    const q = norm($('#q').value.trim()), by = $('#sort').value;
    const list = DATA.filter(p => (carrera==='Todas' || p.carrera===carrera) && q.split(/\s+/).every(w => p._s.includes(w)))
      .sort((a,b) => by==='fecha' ? fechaNum(a)-fechaNum(b) : norm(a[by]).localeCompare(norm(b[by])));
    $('#count').innerHTML = `<b>${list.length}</b> ${list.length===1?'proyecto':'proyectos'}`;
    $('#grid').innerHTML = list.length ? list.map(p => `
      <button class="card" data-id="${p.id}">
        <span class="tag ${p.carrera==='Autotrónica'?'auto':''}">${esc(p.carrera)}</span>
        <h3>${esc(p.titulo)}</h3>
        ${p.caso ? `<div class="caso">Caso: ${esc(p.caso)}</div>` : ''}
        <div class="autor">${esc(p.autor)}</div>
        <div class="meta"><span>${esc(p.fecha)}</span><span class="read">Leer →</span></div>
        <span class="num">${String(p.id).padStart(2,'0')}</span>
      </button>`).join('') : '<div class="empty">Ningún proyecto coincide con su búsqueda.</div>';
  }
  $('#grid').addEventListener('click', e => { const c = e.target.closest('.card'); if (c) open(+c.dataset.id); });

  /* ---------- Modal + visor PDF (solo lectura) ---------- */
  let token = 0;
  function open(id) {
    const p = DATA.find(x => x.id === id); if (!p) return;
    const row = (k,v) => v ? `<div><dt>${k}</dt><dd>${esc(v)}</dd></div>` : '';
    $('#side').innerHTML = `
      <span class="tag ${p.carrera==='Autotrónica'?'auto':''}">${esc(p.carrera)}</span>
      <h2>${esc(p.titulo)}</h2>
      <dl>${row('Caso de aplicación',p.caso)}${row('Estudiante',p.autor)}${row('Nivel',p.nivel)}
      ${row('Fecha de defensa',`${p.dia}, ${p.fecha}`)}${row('Horario',p.inicio&&p.fin?`${p.inicio} – ${p.fin}`:'')}
      ${row('Lugar',`${p.ciudad}, ${p.departamento}`)}${row('Proyecto Nº',p.id)}</dl>`;
    $('#modal').classList.add('open'); document.body.style.overflow = 'hidden';
    viewPDF(p);
  }
  function closeModal() { token++; $('#modal').classList.remove('open'); document.body.style.overflow = ''; $('#viewer').innerHTML = ''; }
  $('#close').onclick = closeModal;
  $('#modal').addEventListener('mousedown', e => { if (e.target.id === 'modal') closeModal(); });

  async function viewPDF(p) {
    const v = $('#viewer'), my = ++token; v.scrollTop = 0;
    if (!p.pdf) { v.innerHTML = '<div class="vmsg"><b>Documento no disponible</b>El PDF de este proyecto aún no ha sido publicado.</div>'; return; }
    v.innerHTML = '<div class="vmsg">Cargando documento…</div>';
    try {
      pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';
      const pdf = await pdfjsLib.getDocument({url: p.pdf, disableAutoFetch: false}).promise;
      if (my !== token) return;
      v.innerHTML = `<div class="vbar"><span id="pgi">${pdf.numPages} páginas · solo lectura</span></div><div class="pages" id="pages"></div>`;
      const pages = $('#pages'), holders = [];
      for (let i = 1; i <= pdf.numPages; i++) { const h = document.createElement('div'); h.className = 'pg-ph'; h.textContent = 'Página ' + i; h.dataset.n = i; pages.appendChild(h); holders.push(h); }
      const io = new IntersectionObserver(es => es.forEach(async en => {
        if (!en.isIntersecting) return; io.unobserve(en.target);
        const h = en.target, pg = await pdf.getPage(+h.dataset.n); if (my !== token) return;
        const vp = pg.getViewport({scale: 1.6}), cv = document.createElement('canvas');
        cv.width = vp.width; cv.height = vp.height;
        await pg.render({canvasContext: cv.getContext('2d'), viewport: vp}).promise;
        if (my !== token) return; h.replaceWith(cv);
      }), {root: v, rootMargin: '800px 0px'});
      holders.forEach(h => io.observe(h));
    } catch (err) {
      if (my === token) v.innerHTML = '<div class="vmsg"><b>No se pudo abrir el documento</b>Intente nuevamente en unos minutos.</div>';
    }
  }

  /* ---------- Disuasión de descarga / impresión ---------- */
  $('#modal').addEventListener('contextmenu', e => e.preventDefault());
  $('#modal').addEventListener('dragstart', e => e.preventDefault());
  addEventListener('keydown', e => {
    if (e.key === 'Escape') closeModal();
    if ($('#modal').classList.contains('open') && (e.ctrlKey||e.metaKey) && ['s','p','u'].includes(e.key.toLowerCase())) e.preventDefault();
  });
})();

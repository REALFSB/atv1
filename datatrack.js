/* DataTrack · utilitários compartilhados pelas 4 páginas.
 * Lê window.DASH_DATA (gerado por `python -m src.dashboard` a partir dos 3 CSVs do Kaggle).
 * Nenhum indicador do painel é digitado à mão: tudo é agregado aqui a partir dos dados. */
(function () {
  const D = window.DASH_DATA;
  const METRICS = ['prod', 'hours', 'ot', 'sat', 'proj', 'train', 'remote', 'sick', 'salary', 'tenure'];

  const nf = (v, d = 0) => (v === null || v === undefined || Number.isNaN(v)) ? '–'
    : Number(v).toLocaleString('pt-BR', { minimumFractionDigits: d, maximumFractionDigits: d });
  const pf = (v, d = 1) => (v === null || v === undefined || Number.isNaN(v)) ? '–' : nf(v, d) + '%';

  /* ---------- agregação (média ponderada correta ao combinar fontes) ---------- */
  function aggregate(rows) {
    const o = { n: 0, resigned: 0, sick_high: 0 };
    METRICS.forEach((m) => { o[m] = [0, 0]; });
    rows.forEach((r) => {
      o.n += r.n; o.resigned += r.resigned || 0; o.sick_high += r.sick_high || 0;
      METRICS.forEach((m) => { o[m][0] += r[m][0]; o[m][1] += r[m][1]; });
    });
    return o;
  }
  const mean = (agg, m) => (agg[m][1] ? agg[m][0] / agg[m][1] : null);
  const rowsOf = (source) => D.by_dept.filter((r) => !source || source === 'all' || r.source === source);

  function departments(source) {
    const map = {};
    rowsOf(source).forEach((r) => { (map[r.department] = map[r.department] || []).push(r); });
    return Object.keys(map).map((name) => {
      const rows = map[name];
      return Object.assign({ department: name, sources: [...new Set(rows.map((r) => r.source))] }, aggregate(rows));
    });
  }

  /* ---------- metas e status ---------- */
  const metaDef = (id) => D.params.metas.find((m) => m.id === id);
  function attainment(def, value) {
    if (value === null || value === undefined || !value) return null;
    return def.sentido === 'min' ? (def.alvo / value) * 100 : (value / def.alvo) * 100;
  }
  const STATUS = {
    superada: { label: 'Superada', cls: 'bg-emerald-50 text-emerald-700 border-emerald-200', bar: 'bg-emerald-500', txt: 'text-emerald-600', hex: '#10b981' },
    na_meta: { label: 'Na Meta', cls: 'bg-blue-50 text-blue-700 border-blue-200', bar: 'bg-blue-600', txt: 'text-blue-600', hex: '#3b82f6' },
    atencao: { label: 'Atenção', cls: 'bg-amber-50 text-amber-700 border-amber-200', bar: 'bg-amber-500', txt: 'text-amber-600', hex: '#f59e0b' },
    critica: { label: 'Crítica', cls: 'bg-rose-50 text-rose-700 border-rose-200', bar: 'bg-rose-500', txt: 'text-rose-600', hex: '#ef4444' },
  };
  function statusOf(pct) {
    const f = D.params.faixas;
    const key = pct >= f.superada ? 'superada' : pct >= f.na_meta ? 'na_meta' : pct >= f.atencao ? 'atencao' : 'critica';
    return Object.assign({ key }, STATUS[key]);
  }
  const badge = (st) => '<span class="px-2 py-0.5 rounded-full text-[11px] font-semibold border ' + st.cls + '">' + st.label + '</span>';

  /* valor de uma meta para um agregado (departamento ou total) */
  function metaValue(agg, id) { return mean(agg, id); }
  /* linhas meta × departamento, só onde existe dado */
  function metaRows(source) {
    const out = [];
    departments(source).forEach((dep) => {
      D.params.metas.forEach((def) => {
        const v = metaValue(dep, def.id);
        const pct = attainment(def, v);
        if (pct === null) return;
        out.push({ def, dep: dep.department, n: dep.n, sources: dep.sources, valor: v, pct, status: statusOf(pct) });
      });
    });
    return out;
  }

  /* ---------- interface ---------- */
  const NAV = [
    { href: 'index.html', icon: 'layout-dashboard', label: 'Dashboard Geral', badge: () => departments().length },
    { href: 'equipes.html', icon: 'users', label: 'Equipes & Escalas', badge: () => nf(D.quality.linhas) },
    { href: 'metas.html', icon: 'target', label: 'Gestão de Metas', badge: () => metaRows().length },
    { href: 'relatorios.html', icon: 'file-text', label: 'Relatórios', badge: () => 'PDF' },
  ];
  function sidebar(active) {
    const el = document.getElementById('sidebar');
    if (!el) return;
    const items = NAV.map((i) => {
      const on = i.href === active;
      return '<a href="' + i.href + '" class="flex items-center gap-3 px-3.5 py-2.5 rounded-lg font-medium text-sm transition ' +
        (on ? 'bg-blue-600 text-white' : 'hover:bg-slate-800 text-slate-400 hover:text-white') + '">' +
        '<i data-lucide="' + i.icon + '" class="w-4 h-4"></i> ' + i.label +
        '<span class="ml-auto ' + (on ? 'bg-white/20 text-white' : 'bg-blue-500/20 text-blue-400') + ' text-[10px] font-bold px-2 py-0.5 rounded-full">' + i.badge() + '</span></a>';
    }).join('');
    el.innerHTML = '<div><div class="h-16 flex items-center px-6 border-b border-slate-800">' +
      '<div class="flex items-center gap-2 font-bold text-lg text-white"><span class="p-1.5 bg-blue-600 rounded-lg text-white shadow-md shadow-blue-500/20">' +
      '<i data-lucide="activity" class="w-5 h-5"></i></span><span>Data<span class="text-blue-500">Track</span></span></div></div>' +
      '<nav class="p-4 space-y-1.5">' + items + '</nav></div>' +
      '<div class="p-4 border-t border-slate-800"><div class="flex items-center gap-3">' +
      '<div class="w-9 h-9 rounded-full bg-blue-500/20 text-blue-400 border border-blue-500/30 flex items-center justify-center font-bold text-xs">GR</div>' +
      '<div class="text-xs truncate"><p class="font-semibold text-white">Guilherme Ramos</p><p class="text-slate-400">Head de Operações</p></div></div></div>';
  }

  /* seletor de base (substitui o antigo Hoje/Semana/Mês: as bases não têm série diária) */
  function sourceTabs(container, onChange, initial) {
    let current = initial || 'all';
    const opts = [['all', 'Todas as bases']].concat(Object.keys(D.sources).map((k) => [k, D.sources[k].label]));
    function draw() {
      container.innerHTML = opts.map((o) => '<button data-src="' + o[0] + '" class="px-3 py-1 rounded-md ' +
        (o[0] === current ? 'bg-white shadow-sm text-slate-900 font-semibold' : 'hover:text-slate-900') + '">' + o[1] + '</button>').join('');
      container.querySelectorAll('button').forEach((b) => b.addEventListener('click', () => { current = b.dataset.src; draw(); onChange(current); }));
    }
    draw();
    return () => current;
  }

  function sourceNote(source) {
    if (!source || source === 'all') return Object.keys(D.sources).map((k) => D.sources[k].label + ' (' + nf(D.sources[k].linhas) + ')').join(' · ');
    return D.sources[source].label + ' (' + nf(D.sources[source].linhas) + ' registros)';
  }

  /* ---------- CSV ---------- */
  function csv(filename, header, lines) {
    const esc = (v) => { const s = (v === null || v === undefined) ? '' : String(v); return /[",;\n]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s; };
    const text = '\ufeff' + [header].concat(lines).map((l) => l.map(esc).join(',')).join('\n');
    return download(filename, new Blob([text], { type: 'text/csv;charset=utf-8' }));
  }
  function download(filename, blob) {
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob); a.download = filename; document.body.appendChild(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(a.href), 2000);
    return blob.size;
  }

  const generatedAt = () => new Date(D.generated_at).toLocaleString('pt-BR', { dateStyle: 'short', timeStyle: 'short' });

  if (!D) {
    document.addEventListener('DOMContentLoaded', () => {
      document.body.insertAdjacentHTML('afterbegin', '<div class="p-4 text-sm bg-red-50 text-red-700 border-b border-red-200">Sem dados: rode <code>python -m src.dashboard</code> para gerar <code>dashboard-data.js</code>.</div>');
    });
  }

  window.DT = { D, nf, pf, aggregate, mean, rowsOf, departments, metaDef, attainment, statusOf, badge, STATUS, metaRows,
    sidebar, sourceTabs, sourceNote, csv, download, generatedAt };
})();

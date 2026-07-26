const routineList = document.getElementById('routine-list');
const addRowBtn = document.getElementById('add-row-btn');
const analyzeBtn = document.getElementById('analyze-btn');
const statusText = document.getElementById('status-text');
const results = document.getElementById('results');

const MARKER_COLORS = ['#0F6659', '#B54A3F', '#C97A2B', '#3D6FA8', '#7FA05A', '#4A4A9E'];

let products = [];
let rowCounter = 0;

function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str || '';
  return div.innerHTML;
}

async function loadProducts() {
  try {
    const res = await fetch('/api/products');
    products = await res.json();
  } catch (e) {
    console.error('Ürünler yüklenemedi', e);
    products = [];
  }
  addRow();
  addRow();
}

function productOptionsHtml(selectedId) {
  if (!products.length) {
    return '<option value="">Veritabanında ürün yok — manuel eklemeyi kullan</option>';
  }
  return ['<option value="">Seç…</option>']
    .concat(products.map(p => `<option value="${p.id}" ${String(p.id) === String(selectedId) ? 'selected' : ''}>${escapeHtml(p.product_name)}</option>`))
    .join('');
}

function addRow() {
  rowCounter += 1;
  const rowId = `row-${rowCounter}`;

  const row = document.createElement('div');
  row.className = 'routine-row';
  row.dataset.rowId = rowId;
  row.dataset.mode = 'db';

  row.innerHTML = `
    <div class="routine-row__header">
      <span class="routine-row__num">${String(routineList.children.length + 1).padStart(2, '0')}</span>
      <div class="routine-row__mode-toggle">
        <button type="button" class="mode-btn active" data-mode="db">Veritabanından</button>
        <button type="button" class="mode-btn" data-mode="manual">Manuel Ekle</button>
      </div>
      <button type="button" class="remove-row" title="Kaldır">✕</button>
    </div>
    <div class="routine-row__db">
      <select class="db-select">${productOptionsHtml()}</select>
      <div class="ingredients-preview"></div>
    </div>
    <div class="routine-row__manual hidden">
      <input type="text" class="manual-name" placeholder="Ürün adı (opsiyonel, örn. Kutumdaki Serum)">
      <textarea class="manual-ingredients" placeholder="İçindekiler listesini buraya yapıştır: Aqua, Retinol, Niacinamide, ..."></textarea>
    </div>
  `;

  routineList.appendChild(row);

  const modeButtons = row.querySelectorAll('.mode-btn');
  const dbSection = row.querySelector('.routine-row__db');
  const manualSection = row.querySelector('.routine-row__manual');

  modeButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      modeButtons.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      row.dataset.mode = btn.dataset.mode;
      if (btn.dataset.mode === 'db') {
        dbSection.classList.remove('hidden');
        manualSection.classList.add('hidden');
      } else {
        dbSection.classList.add('hidden');
        manualSection.classList.remove('hidden');
      }
      updateAnalyzeButton();
    });
  });

  const select = row.querySelector('.db-select');
  const preview = row.querySelector('.ingredients-preview');
  select.addEventListener('change', () => {
    const product = products.find(p => String(p.id) === select.value);
    preview.textContent = product ? product.ingredients_text : '';
    updateAnalyzeButton();
  });

  row.querySelector('.remove-row').addEventListener('click', () => {
    row.remove();
    renumberRows();
    updateAnalyzeButton();
  });

  row.querySelector('.manual-ingredients').addEventListener('input', updateAnalyzeButton);

  renumberRows();
  updateAnalyzeButton();
}

function renumberRows() {
  [...routineList.children].forEach((row, i) => {
    row.querySelector('.routine-row__num').textContent = String(i + 1).padStart(2, '0');
  });
}

function collectItems() {
  const items = [];
  for (const row of routineList.children) {
    if (row.dataset.mode === 'db') {
      const select = row.querySelector('.db-select');
      if (select.value) items.push({ type: 'db', product_id: Number(select.value) });
    } else {
      const name = row.querySelector('.manual-name').value.trim();
      const ingredients = row.querySelector('.manual-ingredients').value.trim();
      if (ingredients) items.push({ type: 'manual', name: name || 'Manuel ürün', ingredients_text: ingredients });
    }
  }
  return items;
}

function updateAnalyzeButton() {
  const items = collectItems();
  analyzeBtn.disabled = items.length < 2;
}

addRowBtn.addEventListener('click', addRow);
analyzeBtn.addEventListener('click', runAnalysis);

async function runAnalysis() {
  const items = collectItems();
  if (items.length < 2) return;

  analyzeBtn.disabled = true;
  statusText.textContent = 'Analiz ediliyor… (yerel LLM yanıt üretiyor, biraz sürebilir)';
  results.classList.add('hidden');

  try {
    const res = await fetch('/api/analyze-routine', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ items }),
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.error || 'Bilinmeyen hata');
    }

    const data = await res.json();
    renderResults(data);
    statusText.textContent = '';
  } catch (e) {
    statusText.textContent = 'Hata: ' + e.message;
  } finally {
    analyzeBtn.disabled = false;
  }
}

function renderResults(data) {
  results.classList.remove('hidden');

  renderPhStrip(data.products);
  renderFindings(data.pairwise_findings);
  renderProductsOverview(data.products);

  document.getElementById('report-body').textContent = data.llm_analysis;

  results.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function renderPhStrip(productList) {
  const strip = document.getElementById('ph-strip');
  strip.innerHTML = '';

  productList.forEach((p, idx) => {
    const color = MARKER_COLORS[idx % MARKER_COLORS.length];
    p.actives.filter(a => a.is_acid).forEach(a => {
      const mid = (a.typical_ph_min + a.typical_ph_max) / 2;
      const pct = (mid / 14) * 100;
      const marker = document.createElement('div');
      marker.className = 'ph-marker';
      marker.style.left = `calc(${pct}% - 1.5px)`;
      marker.style.background = color;
      marker.dataset.label = `${p.name} · ${a.inci_name}`;
      strip.appendChild(marker);
    });
  });

  if (!strip.children.length) {
    strip.insertAdjacentHTML('beforeend', '<span style="position:absolute;top:8px;left:12px;font-family:var(--mono);font-size:11px;color:rgba(255,255,255,0.85)">Rutinde asit bulunmuyor</span>');
  }
}

function severityClass(sev) {
  if (sev === 'yüksek') return 'yuksek';
  if (sev === 'orta') return 'orta';
  if (sev === 'düşük') return 'dusuk';
  return 'ph';
}

function renderFindings(findings) {
  const el = document.getElementById('findings-list');

  const hasAny = findings.some(f => f.ph_overlaps.length || f.known_conflicts.length);
  if (!hasAny) {
    el.innerHTML = '<div class="no-findings">Rutindeki ürünler arasında bilinen bir çakışma tespit edilmedi.</div>';
    return;
  }

  el.innerHTML = findings.map(f => {
    if (!f.ph_overlaps.length && !f.known_conflicts.length) return '';

    const phItems = f.ph_overlaps.map(o => `
      <div class="finding-item">
        <span class="severity-badge ph">pH çakışması</span>
        ${escapeHtml(o.acid_a)} (${o.acid_a_range[0]}–${o.acid_a_range[1]}) ile
        ${escapeHtml(o.acid_b)} (${o.acid_b_range[0]}–${o.acid_b_range[1]}) aynı pH bandında.
      </div>
    `).join('');

    const conflictItems = f.known_conflicts.map(c => `
      <div class="finding-item">
        <span class="severity-badge ${severityClass(c.severity)}">${escapeHtml(c.severity)} risk</span>
        ${escapeHtml(c.ingredient_a)} × ${escapeHtml(c.ingredient_b)}: ${escapeHtml(c.reason)}
        <span class="reco">${escapeHtml(c.recommendation)}</span>
      </div>
    `).join('');

    return `
      <div class="finding-card">
        <div class="finding-card__pair">${escapeHtml(f.product_a)} × ${escapeHtml(f.product_b)}</div>
        ${phItems}${conflictItems}
      </div>
    `;
  }).join('');
}

function renderProductsOverview(productList) {
  const el = document.getElementById('products-overview-list');
  el.innerHTML = productList.map(p => {
    const activesStr = p.actives.length
      ? p.actives.map(a => a.inci_name).join(', ')
      : '(bilinen aktif bileşen yok)';
    return `
      <div class="product-card">
        <div class="product-card__name">${escapeHtml(p.name)}</div>
        <div class="product-card__actives">${escapeHtml(activesStr)}</div>
      </div>
    `;
  }).join('');
}

loadProducts();

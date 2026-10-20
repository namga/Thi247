import './style.css';

const state = {
  items: [], grade: '', subject: '', type: '', q: '',
  page: 'home',
  settings: { theme: 'system', accent: '#167c68', fontSize: 'medium' }
};
const app = document.querySelector('#app');
const accents = [
  {name:'Xanh ngọc', value:'#167c68'}, {name:'Xanh dương', value:'#2563eb'},
  {name:'Tím', value:'#7c3aed'}, {name:'Cam', value:'#ea580c'}, {name:'Hồng', value:'#db2777'}
];
function escapeHtml(value='') {
  return String(value).replace(/[&<>"']/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
}
function loadSettings() {
  try { state.settings = {...state.settings, ...JSON.parse(localStorage.getItem('kht-settings') || '{}')}; } catch {}
  applySettings();
}
function saveSettings() {
  try { localStorage.setItem('kht-settings', JSON.stringify(state.settings)); } catch {}
  applySettings();
}
function applySettings() {
  const root = document.documentElement;
  const dark = state.settings.theme === 'dark' ||
    (state.settings.theme === 'system' && window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches);
  root.dataset.theme = dark ? 'dark' : 'light';
  root.style.setProperty('--accent', state.settings.accent || '#167c68');
  root.dataset.fontSize = state.settings.fontSize || 'medium';
  const meta = document.querySelector('meta[name="theme-color"]');
  if (meta) meta.content = state.settings.accent || '#167c68';
}
function options(key, label) {
  const values = [...new Set(state.items.map(x => x[key]).filter(Boolean))].sort((a,b)=>String(a).localeCompare(String(b),'vi'));
  return `<label>${label}<select data-filter="${key}"><option value="">Tất cả</option>${values.map(v=>`<option value="${escapeHtml(v)}" ${state[key]===v?'selected':''}>${escapeHtml(v)}</option>`).join('')}</select></label>`;
}
function nav() {
  return `<nav class="bottom-nav">
    <button data-page="home" class="${state.page==='home'?'active':''}">⌂<span>Trang chủ</span></button>
    <button data-page="library" class="${state.page==='library'?'active':''}">▤<span>Tài liệu</span></button>
    <button data-page="settings" class="${state.page==='settings'?'active':''}">⚙<span>Cài đặt</span></button>
  </nav>`;
}
function settingsView() {
  return `<main class="settings-page">
    <div class="section-title"><div><h2>Cài đặt giao diện</h2><p>Tùy chỉnh theo thiết bị của bạn.</p></div></div>
    <section class="settings-card">
      <h3>Chế độ hiển thị</h3>
      <div class="theme-options">
        ${[['light','☀','Sáng'],['dark','☾','Tối'],['system','▣','Theo hệ thống']].map(([v,ic,label])=>`<button class="theme-choice ${state.settings.theme===v?'selected':''}" data-theme-choice="${v}"><b>${ic}</b><span>${label}</span></button>`).join('')}
      </div>
      <p class="hint">Chế độ hệ thống tự đổi theo cài đặt sáng/tối của thiết bị.</p>
    </section>
    <section class="settings-card">
      <h3>Màu nhấn</h3>
      <div class="accent-options">${accents.map(a=>`<button title="${a.name}" aria-label="${a.name}" class="accent-dot ${state.settings.accent===a.value?'selected':''}" data-accent="${a.value}" style="--dot:${a.value}"></button>`).join('')}</div>
      <p class="hint">Màu được dùng cho nút, liên kết và mục đang chọn.</p>
    </section>
    <section class="settings-card">
      <h3>Cỡ chữ</h3>
      <div class="font-options">${[['small','Nhỏ'],['medium','Vừa'],['large','Lớn']].map(([v,label])=>`<button class="${state.settings.fontSize===v?'selected':''}" data-font="${v}">${label}</button>`).join('')}</div>
      <p class="hint">Thay đổi kích thước chữ trong toàn bộ giao diện.</p>
    </section>
    <section class="settings-card">
      <h3>Dữ liệu & quyền sử dụng</h3>
      <p>Crawler có thể tải file tài liệu trực tiếp khi đường dẫn được robots.txt cho phép. File đã tải được đóng gói trong /resources; quyền phân phối lại vẫn cần được xác minh trước khi phát hành công khai.</p>
      <a class="source" href="https://thi247.com/" target="_blank" rel="noopener noreferrer">Mở THI247.com ↗</a>
      <button class="secondary-button" id="reset-settings">Khôi phục cài đặt mặc định</button>
    </section>
    <p class="settings-foot">Cài đặt giao diện được lưu trên thiết bị này.</p>
  </main>`;
}
function resourceCards(list) {
  return list.length ? `<section class="cards">${list.map(x=>`<article class="card"><div class="chips"><span>${escapeHtml(x.grade ? 'Lớp '+x.grade : 'Chưa phân lớp')}</span><span>${escapeHtml(x.subject||'Chưa phân môn')}</span></div><h3>${escapeHtml(x.title||'Tài liệu chưa có tiêu đề')}</h3><p>${escapeHtml(x.description||'Mở nguồn để xem thông tin chi tiết.')}</p><div class="meta">${escapeHtml(({textbook:'Tài liệu',exam:'Đề thi',article:'Chuyên đề'})[x.resource_type]||x.resource_type||'Tài liệu')} · ${escapeHtml(x.rights_status==='unknown'?'Quyền sử dụng chưa xác minh':(x.rights_status||''))}</div>${x.content_stored && x.local_file ? `<a class="source" href="${escapeHtml(x.local_file)}" target="_blank" rel="noopener noreferrer">Mở tài liệu đã tải ↗</a>` : `<a class="source" href="${escapeHtml(x.source_url||'#')}" target="_blank" rel="noopener noreferrer">Mở trang nguồn ↗</a>`}</article>`).join('')}</section>` :
  `<div class="empty"><div class="empty-icon">⌕</div><h3>Chưa có tài liệu phù hợp</h3><p>Chạy crawler metadata, kiểm tra quyền sử dụng và đưa dữ liệu đã duyệt vào kho trước khi phát hành.</p></div>`;
}
function homeView() {
  const list = state.items.filter(x =>
    (!state.grade || x.grade === state.grade) &&
    (!state.subject || x.subject === state.subject) &&
    (!state.type || x.resource_type === state.type) &&
    (!state.q || `${x.title||''} ${x.description||''} ${x.subject||''} ${x.grade||''}`.toLowerCase().includes(state.q.toLowerCase()))
  );
  return `<header class="hero"><div class="brand"><img src="/icons/icon-192.png" alt="Kho Học Tập"><div><div class="eyebrow">HỌC TẬP • MIỄN PHÍ</div><h1>Kho Học Tập</h1></div></div><p>Tìm tài liệu theo lớp, môn học và chủ đề. ${state.items.filter(x=>x.content_stored&&x.local_file).length} file đã tải trong kho · ${state.items.length} mục được lập chỉ mục.</p></header>
  <main><section class="search-panel"><label class="search">Tìm tài liệu<input id="q" placeholder="Ví dụ: Toán lớp 8, lịch sử..." value="${escapeHtml(state.q)}"></label>
  <div class="filters">${options('grade','Lớp')}${options('subject','Môn học')}${options('resource_type','Loại tài liệu')}</div></section>
  <div class="results-head"><h2>${state.page==='library'?'Thư viện tài liệu':'Tài liệu nổi bật'}</h2><span>${list.length} kết quả</span></div>
  ${resourceCards(list)}
  <footer>Ưu tiên tài liệu được phép sử dụng. Nội dung nguồn ngoài thuộc quyền của chủ sở hữu tương ứng.</footer></main>`;
}
function render() {
  app.innerHTML = `${state.page==='settings' ? settingsView() : homeView()}${nav()}`;
  document.querySelectorAll('[data-page]').forEach(el=>el.addEventListener('click',()=>{state.page=el.dataset.page;render();window.scrollTo({top:0,behavior:'smooth'});}));
  const q = document.querySelector('#q');
  if (q) q.addEventListener('input', e=>{state.q=e.target.value; const pos=e.target.selectionStart; render(); const input=document.querySelector('#q'); input.focus(); input.setSelectionRange(pos,pos);});
  document.querySelectorAll('[data-filter]').forEach(el=>el.addEventListener('change',e=>{state[e.target.dataset.filter]=e.target.value;render();}));
  document.querySelectorAll('[data-theme-choice]').forEach(el=>el.addEventListener('click',()=>{state.settings.theme=el.dataset.themeChoice;saveSettings();render();}));
  document.querySelectorAll('[data-accent]').forEach(el=>el.addEventListener('click',()=>{state.settings.accent=el.dataset.accent;saveSettings();render();}));
  document.querySelectorAll('[data-font]').forEach(el=>el.addEventListener('click',()=>{state.settings.fontSize=el.dataset.font;saveSettings();render();}));
  const reset = document.querySelector('#reset-settings');
  if(reset) reset.addEventListener('click',()=>{state.settings={theme:'system',accent:'#167c68',fontSize:'medium'};saveSettings();render();});
}
async function init() {
  loadSettings();
  try { const response = await fetch('/data/catalog.json'); if(response.ok) state.items = await response.json(); } catch {}
  if (!state.items.length) {
    try { const seed = await fetch('/data/seed-catalog.json'); if (seed.ok) state.items = await seed.json(); } catch {}
  }
  render();
  if ('serviceWorker' in navigator && location.protocol.startsWith('http')) navigator.serviceWorker.register('/sw.js').catch(()=>{});
  if(window.matchMedia) window.matchMedia('(prefers-color-scheme: dark)').addEventListener?.('change',()=>{if(state.settings.theme==='system')applySettings();});
}
init();

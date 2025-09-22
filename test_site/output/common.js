(function() {
  const root = document.documentElement;
  const THEME_KEY = 'ssg-theme';
  const OPEN_KEY = 'ssg-open-dirs';

  // Theme bootstrap
  const storedTheme = localStorage.getItem(THEME_KEY);
  if (storedTheme) {
    root.dataset.theme = storedTheme;
  } else {
    root.dataset.theme = 'light'; // Default to light for classic theme
  }

  const themeToggleBtn = document.getElementById('themeToggle');
  const themeIcon = themeToggleBtn ? themeToggleBtn.querySelector('i') : null;

  function updateThemeIcon(theme) {
    if (themeIcon) {
      // For classic theme, always show sun (light theme icon)
      themeIcon.classList.remove('fa-moon');
      themeIcon.classList.add('fa-sun');
    }
  }

  // Initialize icon
  updateThemeIcon(root.dataset.theme);

  if (themeToggleBtn) {
    // For classic theme, don't toggle, but keep button functional (could open settings or something, but here do nothing)
    // themeToggleBtn.addEventListener('click', () => {
    //   // No toggle for classic theme, as it's always light
    // });
    // But since button is there, perhaps make it static
    themeToggleBtn.disabled = true; // Disable theme toggle for classic theme
    themeToggleBtn.style.opacity = '0.5';
  }

  // Sidebar open-state persistence
  const openSet = new Set(JSON.parse(localStorage.getItem(OPEN_KEY) || '[]'));
  const detailsList = document.querySelectorAll('.sidebar details');
  detailsList.forEach(d => {
    const link = d.querySelector('summary a[data-target]');
    const key = link ? link.getAttribute('data-target') : null;
    if (key && openSet.has(key)) d.setAttribute('open', '');
    d.addEventListener('toggle', () => {
      if (!key) return;
      if (d.open) openSet.add(key); else openSet.delete(key);
      localStorage.setItem(OPEN_KEY, JSON.stringify([...openSet]));
    });
  });

  // Simple client-side search
  const input = document.getElementById('searchInput');
  const panel = document.getElementById('searchResults');
  let index = [];
  let loaded = false;

  function escapeRegExp(s){return s.replace(/[.*+?^${}()|[\]\\]/g,'\\$&');}

  async function ensureIndex() {
    if (loaded) return;
    try {
      const base = document.querySelector('link[rel=stylesheet]')?.getAttribute('href') || 'theme.css';
      // Compute relative path to search-index.json based on CSS path
      const url = base.replace(/[^\/]*$/, 'search-index.json');
      const res = await fetch(url, { cache: 'no-store' });
      if (!res.ok) throw new Error('HTTP ' + res.status);
      index = await res.json();
      loaded = true;
    } catch (e) {
      console.error('Search index load failed', e);
    }
  }

  function renderResults(items, query) {
    if (!items.length || !query) {
      panel.hidden = true;
      panel.innerHTML = '';
      return;
    }
    const q = query.trim();
    const rx = new RegExp(escapeRegExp(q), 'ig');
    panel.innerHTML = items.slice(0, 20).map(it => {
      const snippet = (it.content || '').slice(0, 200).replace(rx, m => `<mark>${m}</mark>`);
      return `<a class="result" href="${it.url}"><strong>${it.title}</strong><span>${snippet}…</span></a>`;
    }).join('');
    panel.hidden = false;
  }

  async function onInput() {
    const q = input.value.trim();
    if (!q) { renderResults([], ''); return; }
    await ensureIndex();
    const ql = q.toLowerCase();
    const results = index.filter(it => (it.title || '').toLowerCase().includes(ql) || (it.content || '').toLowerCase().includes(ql));
    renderResults(results, q);
  }

  if (input) {
    input.addEventListener('input', onInput);
    input.addEventListener('focus', onInput);
    document.addEventListener('click', (e) => {
      if (!panel.contains(e.target) && e.target !== input) panel.hidden = true;
    });
  }
})();

(function() {
  const root = document.documentElement;
  const THEME_KEY = 'ssg-theme';
  const OPEN_KEY = 'ssg-open-dirs';

  // Theme bootstrap
  const storedTheme = localStorage.getItem(THEME_KEY);
  if (storedTheme) {
    root.dataset.theme = storedTheme;
  } else {
    root.dataset.theme = 'dark'; // Set dark theme as default
  }

  const themeToggleBtn = document.getElementById('themeToggle');
  const themeIcon = themeToggleBtn ? themeToggleBtn.querySelector('i') : null;

  function updateThemeIcon(theme) {
    if (themeIcon) {
      if (theme === 'light') {
        themeIcon.classList.remove('fa-moon');
        themeIcon.classList.add('fa-sun');
      } else {
        themeIcon.classList.remove('fa-sun');
        themeIcon.classList.add('fa-moon');
      }
    }
  }

  // Initialize icon based on current theme
  updateThemeIcon(root.dataset.theme);

  if (themeToggleBtn) {
    themeToggleBtn.addEventListener('click', () => {
      const next = root.dataset.theme === 'light' ? 'dark' : 'light';
      root.dataset.theme = next;
      localStorage.setItem(THEME_KEY, next);
      updateThemeIcon(next);
    });
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

  // Sidebar toggle
  const sidebarToggle = document.querySelector('.sidebar-toggle');
  const sidebarClose = document.querySelector('.sidebar-close');
  const layout = document.querySelector('.layout');
  const sidebarBackdrop = document.querySelector('.sidebar-backdrop');

  if (sidebarToggle) {
    sidebarToggle.addEventListener('click', (e) => {
      e.preventDefault();
      if (window.innerWidth > 900) {
        layout.classList.toggle('sidebar-closed');
      } else {
        layout.classList.toggle('sidebar-open');
      }
    });
  }

  if (sidebarClose) {
    sidebarClose.addEventListener('click', () => {
      if (window.innerWidth > 900) {
        layout.classList.toggle('sidebar-closed');
      } else {
        layout.classList.remove('sidebar-open');
      }
    });
  }

  if (sidebarBackdrop) {
    sidebarBackdrop.addEventListener('click', () => {
      layout.classList.remove('sidebar-open');
    });
  }

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

(function() {
  const root = document.documentElement;
  const THEME_KEY = 'ssg-theme';

  // For Windows 98 theme, always use light theme
  const storedTheme = localStorage.getItem(THEME_KEY);
  if (storedTheme) {
    root.dataset.theme = storedTheme;
  } else {
    root.dataset.theme = 'light';
  }

  // Update clock
  function updateClock() {
    const clock = document.querySelector('.taskbar-clock');
    if (clock) {
      const now = new Date();
      clock.textContent = now.toLocaleTimeString('en-US', {hour: '2-digit', minute: '2-digit', hour12: false});
    }
  }
  setInterval(updateClock, 1000);
  updateClock();

  // Toggle Start menu popup
  const startBtn = document.querySelector('.taskbar-start');
  const startMenu = document.querySelector('.start-menu-popup');
  if (startBtn && startMenu) {
    startBtn.addEventListener('click', () => {
      startMenu.classList.toggle('visible');
    });
    // Close menu when clicking outside
    document.addEventListener('click', (e) => {
      if (!startMenu.contains(e.target) && e.target !== startBtn) {
        startMenu.classList.remove('visible');
      }
    });
  }

  // Power options functionality
  const powerBtns = document.querySelectorAll('.power-btn');
  powerBtns.forEach(btn => {
    btn.addEventListener('click', (e) => {
      const action = e.target.classList.contains('shutdown') ? 'shutdown' :
                     e.target.classList.contains('restart') ? 'restart' :
                     e.target.classList.contains('sleep') ? 'sleep' : 'hibernate';
      alert(`Power action: ${action}\n(This is just a demonstration - actual shutdown would be handled by the operating system)`);
    });
  });

  // Menu item interactions (prevent default behavior for demo purposes)
  const menuItems = document.querySelectorAll('.start-menu-item');
  menuItems.forEach(item => {
    item.addEventListener('click', (e) => {
      const itemText = e.target.textContent || e.target.innerText;
      console.log(`Menu item clicked: ${itemText}`);
      // In a real application, this would navigate to the corresponding page
    });
  });

  // Simple client-side search with popup window
  const input = document.getElementById('searchInput');
  const panel = document.getElementById('searchResults');
  const searchPopup = document.getElementById('searchPopup');
  let index = [];
  let loaded = false;

  function escapeRegExp(s){return s.replace(/[.*+?^${}()|[\]\\]/g,'\\$&');}

  async function ensureIndex() {
    if (loaded) return;
    try {
      const url = '/unstable/output/search-index.json';
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
      searchPopup.hidden = true;
      panel.innerHTML = '';
      return;
    }
    const q = query.trim();
    const rx = new RegExp(escapeRegExp(q), 'ig');

    // Update popup title with search query
    const titleSpan = searchPopup.querySelector('.title-text');
    if (titleSpan) {
      titleSpan.textContent = `Risultati Ricerca - "${q}"`;
    }

    panel.innerHTML = items.slice(0, 20).map(it => {
      const snippet = (it.content || '').slice(0, 200).replace(rx, m => `<mark>${m}</mark>`);
      return `<a class="result" href="${it.url}"><strong>${it.title}</strong><span>${snippet}…</span></a>`;
    }).join('');

    // Show the search popup
    searchPopup.hidden = false;

    // Focus the popup for better accessibility
    searchPopup.focus();
  }

  async function onInput() {
    const q = input.value.trim();
    if (!q) {
      renderResults([], '');
      return;
    }
    await ensureIndex();
    const results = index.filter(it =>
      (it.title || '').toLowerCase().includes(q.toLowerCase()) ||
      (it.content || '').toLowerCase().includes(q.toLowerCase())
    );
    renderResults(results, q);
  }

  // Close search popup functionality
  function closeSearchPopup() {
    if (searchPopup) {
      searchPopup.hidden = true;
      panel.innerHTML = '';
      const titleSpan = searchPopup.querySelector('.title-text');
      if (titleSpan) {
        titleSpan.textContent = 'Risultati Ricerca';
      }
    }
  }

  if (input) {
    input.addEventListener('input', onInput);
    input.addEventListener('focus', onInput);

    // Handle search input focus/clear
    input.addEventListener('keyup', (e) => {
      if (e.key === 'Escape') {
        input.value = '';
        closeSearchPopup();
        input.blur();
      }
    });

    // Close popup when clicking outside
    document.addEventListener('click', (e) => {
      if (searchPopup && !searchPopup.contains(e.target) && e.target !== input) {
        closeSearchPopup();
      }
    });
  }

  // Close search popup button
  const closeBtn = document.querySelector('.close-search');
  if (closeBtn) {
    closeBtn.addEventListener('click', closeSearchPopup);
  }

  // Make search popup focusable for accessibility
  if (searchPopup) {
    searchPopup.tabIndex = -1; // Make focusable but not in tab order
    searchPopup.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        closeSearchPopup();
      }
    });
  }
})();

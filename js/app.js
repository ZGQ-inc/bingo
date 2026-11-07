/**
 * Main Application Logic for Bingo & Bottle Hub (bingo.zgqinc.gq)
 */
import { Storage } from './storage.js';
import { checkBingo } from './bingo-logic.js';
import { CanvasRenderer } from './canvas-renderer.js';

class BingoApp {
  constructor() {
    this.games = [];
    this.categories = [];
    this.currentCard = null;
    this.currentChecks = new Set();
    this.currentBottleLevels = {};
    this.activeCategory = 'all';
    this.searchQuery = '';
    this.currentViewMode = 'canvas'; // 'canvas' | 'list' | 'split'
    this.settings = Storage.getSettings();
    this.authorRecords = null;
    this.isViewingAuthor = false;

    this.savedGalleryScrollY = 0;

    this.renderer = null;
    this.imageElement = null;

    this.init();
  }

  async init() {
    this.initTheme();
    await this.loadData();
    this.initDOM();
    this.renderCategoryChips();
    this.initRouter();
    this.initDialogs();
    this.initPersonalShowcase();
  }

  initTheme() {
    const apply = (theme) => {
      let resolved = theme;
      if (theme === 'auto') {
        const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
        resolved = prefersDark ? 'dark' : 'light';
      }
      document.documentElement.setAttribute('data-theme', resolved);
      const themeIcon = document.getElementById('theme-icon');
      if (themeIcon) {
        themeIcon.textContent = resolved === 'dark' ? 'light_mode' : 'dark_mode';
      }
    };

    apply(this.settings.theme);

    // Watch system changes if in auto mode
    if (window.matchMedia) {
      window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
        if (this.settings.theme === 'auto') {
          apply('auto');
        }
      });
    }

    // Toggle theme button (Quick switch between light and dark)
    document.getElementById('theme-toggle')?.addEventListener('click', () => {
      const currentResolved = document.documentElement.getAttribute('data-theme') || 'light';
      const nextTheme = currentResolved === 'dark' ? 'light' : 'dark';
      this.settings.theme = nextTheme;
      Storage.saveSettings(this.settings);
      apply(nextTheme);
      this.showToast(`主题已切换为: ${nextTheme === 'dark' ? '深色模式' : '浅色模式'}`);
    });
  }

  async loadData() {
    try {
      const [gamesRes, catRes] = await Promise.all([
        fetch('data/games.json'),
        fetch('data/categories.json')
      ]);
      this.games = await gamesRes.json();
      this.categories = await catRes.json();
    } catch (e) {
      console.error('Failed to load bingo data:', e);
      this.showToast('数据加载失败');
    }

    // Attempt to load author personal records
    this.authorRecords = await Storage.loadAuthorRecords();
  }

  initDOM() {
    this.gallerySection = document.getElementById('gallery-section');
    this.playerSection = document.getElementById('player-section');
    this.canvas = document.getElementById('bingo-canvas');
    this.canvasContainer = document.getElementById('canvas-container');
    this.checklistContainer = document.getElementById('checklist-container');
    this.searchField = document.getElementById('search-input');
    this.toast = document.getElementById('app-toast');

    this.renderer = new CanvasRenderer(this.canvas);
    this.renderer.setSettings(this.settings);

    this.renderer.onCellClick = (idx) => this.toggleCell(idx);
    this.renderer.onBottleChange = (idx, pct) => this.updateBottleLevel(idx, pct);

    // Passive scroll listener to always record exact gallery scroll position
    window.addEventListener('scroll', () => {
      if (this.gallerySection && this.gallerySection.style.display !== 'none') {
        this.savedGalleryScrollY = window.scrollY;
      }
    }, { passive: true });

    // Search & Clear
    const clearBtn = document.getElementById('search-clear-btn');
    this.searchField?.addEventListener('input', (e) => {
      this.searchQuery = (e.target.value || '').trim().toLowerCase();
      if (clearBtn) {
        clearBtn.style.display = this.searchQuery ? 'flex' : 'none';
      }
      this.renderGallery();
      const url = this._buildUrl({ cardId: null, q: this.searchQuery });
      window.history.replaceState(
        { view: 'gallery', cat: this.activeCategory, scrollY: window.scrollY },
        '',
        url
      );
    });

    clearBtn?.addEventListener('click', () => {
      if (this.searchField) {
        this.searchField.value = '';
        this.searchQuery = '';
        clearBtn.style.display = 'none';
        this.searchField.focus();
        this.renderGallery();
        const url = this._buildUrl({ cardId: null, q: '' });
        window.history.replaceState(
          { view: 'gallery', cat: this.activeCategory, scrollY: window.scrollY },
          '',
          url
        );
      }
    });

    // Brand logo click navigates to home gallery without full page reload
    document.querySelector('.brand')?.addEventListener('click', (e) => {
      e.preventDefault();
      if (this.currentCard) {
        this.closePlayer(true);
      } else {
        if (this.activeCategory !== 'all') {
          this.setCategory('all', true);
        }
        window.scrollTo({ top: 0, behavior: 'smooth' });
      }
    });

    // Horizontal wheel scroll for category chips
    const chipScroll = document.querySelector('.chip-scroll');
    if (chipScroll) {
      chipScroll.addEventListener('wheel', (e) => {
        if (e.deltaY !== 0) {
          e.preventDefault();
          chipScroll.scrollBy({ left: e.deltaY * 1.5, behavior: 'smooth' });
        }
      }, { passive: false });
    }

    // Back to gallery
    document.getElementById('back-to-gallery')?.addEventListener('click', () => {
      this.closePlayer(true);
    });

    // View Mode Segmented Pill Buttons
    const modeBtns = document.querySelectorAll('.mode-pill-btn');
    modeBtns.forEach((btn) => {
      btn.addEventListener('click', () => {
        const mode = btn.dataset.mode;
        if (mode) this.setViewMode(mode);
      });
    });

    // Player Toolbar Actions
    document.getElementById('btn-clear-checks')?.addEventListener('click', () => {
      this.clearCurrentCard();
    });

    document.getElementById('btn-random-checks')?.addEventListener('click', () => {
      this.randomFillCurrentCard();
    });

    // Init Scroll Header (Hide/reveal category bar on scroll)
    this.initScrollHeader();

    // Dual-mode Fit/Fullscreen Toggle (Desktop: vertical fit vs width fit; Mobile: in-app edge-to-edge full width)
    const fitBtn = document.getElementById('btn-toggle-fit') || document.getElementById('btn-toggle-fullscreen');
    fitBtn?.addEventListener('click', () => {
      const isMobile = window.innerWidth <= 768;
      if (isMobile) {
        const playerSec = document.getElementById('player-section');
        const isImmersive = playerSec?.classList.toggle('mobile-immersive');
        this.updateFitButtonUI();
        if (this.renderer) {
          this.renderer.resizeCanvas();
          this.renderer.render();
        }
        this.showToast(isImmersive ? '已开启满宽全屏' : '已恢复标准边距视图');
      } else {
        const mode = this.renderer.toggleFitMode();
        this.updateFitButtonUI();
        this.showToast(mode === 'vertical' ? '已开启满高适应' : '已切换为适宽模式');
      }
    });

    window.addEventListener('resize', () => {
      this.updateFitButtonUI();
    });

    document.getElementById('btn-view-original')?.addEventListener('click', () => {
      this.openOriginalDialog();
    });

    document.getElementById('btn-export-image')?.addEventListener('click', () => {
      this.exportImage();
    });

    document.getElementById('btn-settings')?.addEventListener('click', () => {
      this.openWatermarkDialog();
    });

    // Stamp Style Chips
    const stampChips = document.querySelectorAll('.stamp-style-chip');
    stampChips.forEach((chip) => {
      chip.addEventListener('click', () => {
        stampChips.forEach(c => c.removeAttribute('selected'));
        chip.setAttribute('selected', '');
        const style = chip.dataset.style;
        this.settings.stampStyle = style;
        Storage.saveSettings(this.settings);
        this.renderer.setSettings(this.settings);
      });
    });

    // Stamp / Liquid Color Dots
    const colorDots = document.querySelectorAll('.color-dot');
    colorDots.forEach((dot) => {
      dot.addEventListener('click', () => {
        colorDots.forEach(d => d.classList.remove('active'));
        dot.classList.add('active');
        const color = dot.dataset.color;
        if (this.currentCard?.type === 'bottle') {
          this.settings.liquidColor = color;
        } else {
          this.settings.stampColor = color;
        }
        Storage.saveSettings(this.settings);
        this.renderer.setSettings(this.settings);
      });
    });

    // Personal Records Buttons in Header / Gallery
    document.getElementById('btn-export-personal')?.addEventListener('click', () => {
      this.exportPersonalJSON();
    });

    document.getElementById('btn-import-personal')?.addEventListener('click', () => {
      document.getElementById('import-file-input')?.click();
    });

    document.getElementById('import-file-input')?.addEventListener('change', (e) => {
      this.handleImportFile(e);
    });
  }

  updateFitButtonUI() {
    const fitBtn = document.getElementById('btn-toggle-fit') || document.getElementById('btn-toggle-fullscreen');
    const fitText = document.getElementById('btn-fit-text') || document.getElementById('btn-fullscreen-text');
    const fitIcon = document.getElementById('btn-fit-icon') || document.getElementById('btn-fullscreen-icon');
    if (!fitBtn || !fitText) return;

    const isMobile = window.innerWidth <= 768;
    if (isMobile) {
      const isImmersive = document.getElementById('player-section')?.classList.contains('mobile-immersive');
      fitText.textContent = isImmersive ? '恢复边距' : '满宽全屏';
      if (fitIcon) fitIcon.textContent = isImmersive ? 'fit_screen' : 'aspect_ratio';
      fitBtn.setAttribute('title', isImmersive ? '恢复标准卡片边距' : '取消边距，满宽全屏显示图片');
    } else {
      const mode = this.renderer?.fitMode || 'vertical';
      fitText.textContent = mode === 'vertical' ? '垂直适屏' : '宽度自适应';
      if (fitIcon) fitIcon.textContent = mode === 'vertical' ? 'fit_screen' : 'width_full';
      fitBtn.setAttribute('title', mode === 'vertical' ? '已开启满高适应' : '已切换为宽度自适应模式');
    }
  }

  initScrollHeader() {
    const filterBar = document.getElementById('header-filter-bar');
    if (!filterBar) return;

    let lastScrollY = window.scrollY;
    let isHidden = false;
    const threshold = 12;

    window.addEventListener('scroll', () => {
      // Only run scroll animation in gallery view
      if (this.gallerySection && this.gallerySection.style.display === 'none') return;

      const currentScrollY = window.scrollY;

      // Always show at or near top
      if (currentScrollY <= 24) {
        if (isHidden) {
          filterBar.classList.remove('filter-hidden');
          isHidden = false;
        }
        lastScrollY = currentScrollY;
        return;
      }

      const diff = currentScrollY - lastScrollY;
      if (Math.abs(diff) < threshold) return;

      if (diff > 0 && !isHidden) {
        // Scrolling down -> hide only category bar with smooth transition
        filterBar.classList.add('filter-hidden');
        isHidden = true;
      } else if (diff < 0 && isHidden) {
        // Scrolling up -> reveal category bar with smooth transition
        filterBar.classList.remove('filter-hidden');
        isHidden = false;
      }

      lastScrollY = currentScrollY;
    }, { passive: true });
  }

  initPersonalShowcase() {
    const ownerToggle = document.getElementById('owner-showcase-toggle');
    if (!ownerToggle) return;

    if (this.authorRecords) {
      ownerToggle.style.display = 'flex';
      ownerToggle.addEventListener('click', () => {
        this.isViewingAuthor = !this.isViewingAuthor;
        ownerToggle.classList.toggle('active', this.isViewingAuthor);
        if (this.isViewingAuthor) {
          ownerToggle.innerHTML = `<span>👑 作者记录展示中</span>`;
          this.showToast('已切换至作者的个人打卡结果展示');
        } else {
          ownerToggle.innerHTML = `<span>👤 切换作者记录</span>`;
          this.showToast('已切回您的个人打卡');
        }
        if (this.currentCard) {
          this.loadCardState(this.currentCard);
        } else {
          this.renderGallery();
        }
      });
    } else {
      ownerToggle.style.display = 'none';
    }
  }

  _buildUrl(options = {}) {
    const params = new URLSearchParams();
    
    // Determine card ID
    let id = undefined;
    if ('cardId' in options) {
      id = options.cardId;
    } else {
      id = this.currentCard?.id || null;
    }
    if (id) {
      params.set('id', id);
    }

    // Determine category
    const cat = ('cat' in options) ? options.cat : this.activeCategory;
    if (cat && cat !== 'all') {
      params.set('cat', cat);
    }

    // Determine query
    const q = ('q' in options) ? options.q : this.searchQuery;
    if (q) {
      params.set('q', q);
    }

    const qs = params.toString();
    return qs ? `${window.location.pathname}?${qs}` : window.location.pathname;
  }

  syncCategoryChipUI() {
    const chips = document.querySelectorAll('#category-chips md-filter-chip');
    chips.forEach((chip) => {
      if (chip.dataset.catId === this.activeCategory) {
        chip.setAttribute('selected', '');
      } else {
        chip.removeAttribute('selected');
      }
    });
  }

  setCategory(catId, pushHistory = true) {
    if (this.activeCategory === catId && !this.currentCard) return;

    if (!this.currentCard && this.gallerySection.style.display !== 'none') {
      window.history.replaceState(
        { view: 'gallery', cat: this.activeCategory, scrollY: window.scrollY },
        '',
        this._buildUrl({ cardId: null, cat: this.activeCategory })
      );
    }

    this.activeCategory = catId;
    this.syncCategoryChipUI();

    if (this.currentCard) {
      this.closePlayer(false);
    }

    const grid = document.getElementById('bingo-grid') || document.getElementById('games-grid');
    if (grid) {
      grid.classList.remove('gallery-grid-entering');
      void grid.offsetWidth;
      grid.classList.add('gallery-grid-entering');
    }
    this.renderGallery();

    this.savedGalleryScrollY = 0;
    window.scrollTo({ top: 0, behavior: 'instant' });

    if (pushHistory) {
      const url = this._buildUrl({ cardId: null, cat: this.activeCategory });
      window.history.pushState(
        { view: 'gallery', cat: this.activeCategory, scrollY: 0 },
        '',
        url
      );
    }
  }

  renderCategoryChips() {
    const chipSet = document.getElementById('category-chips');
    if (!chipSet) return;
    chipSet.innerHTML = '';

    this.categories.forEach((cat) => {
      const chip = document.createElement('md-filter-chip');
      chip.setAttribute('label', `${cat.icon} ${cat.name}`);
      chip.dataset.catId = cat.id;
      if (cat.id === this.activeCategory) {
        chip.setAttribute('selected', '');
      }

      chip.addEventListener('click', () => {
        this.setCategory(cat.id, true);
      });

      chipSet.appendChild(chip);
    });
  }

  initRouter() {
    if ('scrollRestoration' in window.history) {
      window.history.scrollRestoration = 'manual';
    }

    window.addEventListener('popstate', (e) => {
      this.handlePopState(e.state);
    });

    const params = new URLSearchParams(window.location.search);
    const initialCat = params.get('cat') || params.get('category');
    if (initialCat) {
      this.activeCategory = initialCat;
    }
    this.syncCategoryChipUI();

    const initialQuery = params.get('q');
    if (initialQuery) {
      this.searchQuery = initialQuery;
      if (this.searchField) {
        this.searchField.value = initialQuery;
        const clearBtn = document.getElementById('search-clear-btn');
        if (clearBtn) clearBtn.style.display = 'flex';
      }
    }

    const initialCardId = params.get('id') || params.get('card');
    if (initialCardId) {
      const game = this.games.find(g => g.id === initialCardId);
      if (game) {
        this.savedGalleryScrollY = 0;
        this.openPlayer(game, false);
        window.history.replaceState(
          { view: 'player', id: game.id, cat: this.activeCategory, scrollY: 0, directEntry: true },
          '',
          window.location.href
        );
        return;
      }
    }

    this.renderGallery();
    window.history.replaceState(
      { view: 'gallery', cat: this.activeCategory, scrollY: window.scrollY },
      '',
      window.location.href
    );
  }

  handlePopState(state) {
    const params = new URLSearchParams(window.location.search);
    const targetId = params.get('id') || params.get('card');
    const targetCat = params.get('cat') || params.get('category') || 'all';
    const targetQuery = params.get('q') || '';

    if (this.searchQuery !== targetQuery) {
      this.searchQuery = targetQuery;
      if (this.searchField) {
        this.searchField.value = targetQuery;
        const clearBtn = document.getElementById('search-clear-btn');
        if (clearBtn) clearBtn.style.display = targetQuery ? 'flex' : 'none';
      }
    }

    if (targetId) {
      const game = this.games.find(g => g.id === targetId);
      if (game) {
        if (!this.currentCard || this.currentCard.id !== targetId) {
          if (!this.currentCard && this.gallerySection.style.display !== 'none') {
            this.savedGalleryScrollY = window.scrollY;
          }
          this.openPlayer(game, false);
        }
      }
    } else {
      const catChanged = this.activeCategory !== targetCat;
      this.activeCategory = targetCat;
      this.syncCategoryChipUI();

      if (this.currentCard) {
        this.currentCard = null;
        this.playerSection.style.display = 'none';
        this.gallerySection.style.display = 'block';

        const headerFilter = document.getElementById('header-filter-bar');
        if (headerFilter) {
          headerFilter.style.display = 'block';
          headerFilter.classList.remove('filter-hidden');
        }

        this.renderGallery();
      } else if (catChanged) {
        this.renderGallery();
      }

      void document.body.offsetHeight;
      const targetScrollY = (state?.scrollY !== undefined && state?.scrollY > 0)
        ? state.scrollY
        : (this.savedGalleryScrollY || 0);

      requestAnimationFrame(() => {
        window.scrollTo({ top: targetScrollY, behavior: 'instant' });
      });
    }
  }

  renderGallery() {
    const grid = document.getElementById('games-grid');
    if (!grid) return;
    grid.innerHTML = '';

    const stats = Storage.getAllCardStats();

    const filtered = this.games.filter((game) => {
      if (game.hidden) return false;
      if (this.activeCategory !== 'all') {
        if (this.activeCategory === 'bottle' && game.type !== 'bottle') return false;
        if (this.activeCategory !== 'bottle' && game.categoryId !== this.activeCategory) return false;
      }
      if (this.searchQuery) {
        const q = this.searchQuery;
        const matchesTitle = game.title.toLowerCase().includes(q);
        const matchesSub = game.subtitle?.toLowerCase().includes(q);
        const matchesCat = game.category.toLowerCase().includes(q);
        const matchesCells = game.cells?.some(c => (c.text || c.label || '').toLowerCase().includes(q));
        if (!matchesTitle && !matchesSub && !matchesCat && !matchesCells) return false;
      }
      return true;
    });

    const countLabel = document.getElementById('card-count-label');
    if (countLabel) {
      countLabel.classList.remove('card-count-loading');
      countLabel.classList.add('card-count-loaded');
      countLabel.innerHTML = `
        <span class="count-badge">
          <span class="count-pulse-dot"></span>
          共 <strong>${filtered.length}</strong> 款宾果与量表
        </span>
      `;
    }

    if (filtered.length === 0) {
      grid.innerHTML = `
        <div class="empty-state">
          <div class="empty-icon">🔍</div>
          <h3>未找到匹配的宾果游戏</h3>
          <p>请尝试不同的搜索词或选择其它分类</p>
        </div>
      `;
      return;
    }

    filtered.forEach((game, idx) => {
      const cardEl = document.createElement('div');
      cardEl.className = 'bingo-card-item';
      cardEl.dataset.id = game.id;

      const checkedCount = stats[game.id] || 0;
      const progressBadge = checkedCount > 0
        ? `<div class="progress-badge">${game.type === 'bottle' ? '已填' : '已选'} ${checkedCount}/${game.cellCount}</div>`
        : '';

      const typeBadge = game.type === 'bottle'
        ? `<div class="type-pill bottle">🧪 罐子量表</div>`
        : game.type === 'checklist'
        ? `<div class="type-pill checklist">📋 打卡清单</div>`
        : `<div class="type-pill">🎯 ${game.grid.rows}×${game.grid.cols} 宾果</div>`;

      cardEl.innerHTML = `
        <div class="card-thumb-wrap">
          <img src="${encodeURI(game.filename)}" alt="${game.title}" loading="lazy" class="card-thumb">
          <div class="category-pill">${game.categoryIcon} ${game.category}</div>
          ${progressBadge}
        </div>
        <div class="card-info">
          <div class="card-title" title="${game.title}">${game.title}</div>
          <div class="card-sub" title="${game.subtitle}">${game.subtitle || '点击卡片即可打卡'}</div>
          <div class="card-footer">
            <span class="grid-badge">${game.cellCount} 项</span>
            ${typeBadge}
          </div>
        </div>
      `;

      cardEl.style.animationDelay = `${Math.min(idx * 22, 280)}ms`;
      cardEl.addEventListener('click', () => {
        this.openPlayer(game, true);
      });

      grid.appendChild(cardEl);
    });
  }

  async openPlayer(game, pushHistory = true) {
    if (this.gallerySection.style.display !== 'none') {
      this.savedGalleryScrollY = window.scrollY;
      const currentGalleryUrl = this._buildUrl({ cardId: null });
      window.history.replaceState(
        { view: 'gallery', cat: this.activeCategory, scrollY: this.savedGalleryScrollY },
        '',
        currentGalleryUrl
      );
    }

    let card = game;
    if (!game.cells?.[0]?.x) {
      try {
        const res = await fetch(`data/cards/${game.id}.json`);
        if (res.ok) {
          card = await res.json();
        }
      } catch (err) {
        console.warn('Could not fetch card JSON', err);
      }
    }
    this.currentCard = card;

    // Hide category chips bar in header when player is open
    const headerFilter = document.getElementById('header-filter-bar');
    if (headerFilter) {
      headerFilter.style.display = 'none';
      headerFilter.classList.remove('filter-hidden');
    }

    // Reset mobile immersive class on entering card
    document.getElementById('player-section')?.classList.remove('mobile-immersive');
    this.updateFitButtonUI();

    // Header info
    document.getElementById('player-title').textContent = card.title;
    document.getElementById('player-sub').textContent = card.subtitle || '点击加盖戳印打卡';
    document.getElementById('player-category').textContent = `${card.categoryIcon} ${card.category}`;

    // Switch view with Jekyll page-enter animation
    this.gallerySection.style.display = 'none';
    this.playerSection.style.display = 'block';
    this.playerSection.classList.remove('page-entering');
    void this.playerSection.offsetWidth;
    this.playerSection.classList.add('page-entering');
    window.scrollTo({ top: 0, behavior: 'instant' });

    if (pushHistory) {
      const url = this._buildUrl({ cardId: game.id });
      window.history.pushState(
        { view: 'player', id: game.id, cat: this.activeCategory, scrollY: this.savedGalleryScrollY },
        '',
        url
      );
    }

    // Update Toolbar controls depending on card type
    this.updateToolbarForCardType(card.type);

    // Load Image
    this.imageElement = new Image();
    this.imageElement.src = encodeURI(card.filename);
    this.imageElement.onload = () => {
      this.renderer.setCard(card, this.imageElement);
      this.loadCardState(card);
    };

    this.setViewMode(this.currentViewMode, true);
  }

  updateToolbarForCardType(type) {
    const stampGroup = document.getElementById('toolbar-stamp-group');
    const colorLabel = document.getElementById('toolbar-color-label');
    if (stampGroup) {
      stampGroup.style.display = type === 'bottle' ? 'none' : 'flex';
    }
    if (colorLabel) {
      colorLabel.textContent = type === 'bottle' ? '液体颜色:' : '印记颜色:';
    }
  }

  loadCardState(game) {
    if (this.isViewingAuthor && this.authorRecords?.records?.[game.id]) {
      const rec = this.authorRecords.records[game.id];
      this.currentChecks = new Set(rec.checked || []);
      this.currentBottleLevels = rec.bottleLevels || {};
    } else {
      this.currentChecks = new Set(Storage.getChecks(game.id));
      this.currentBottleLevels = Storage.getBottleLevels(game.id);
    }

    this.renderer.setChecked(Array.from(this.currentChecks));
    this.renderer.setBottleLevels(this.currentBottleLevels);

    this.updatePlayerState();
    this.renderChecklist();
  }

  closePlayer(updateHistory = true) {
    if (!this.currentCard && this.gallerySection.style.display !== 'none') return;

    if (updateHistory) {
      if (window.history.state?.view === 'player' && !window.history.state?.directEntry) {
        window.history.back();
        return;
      }
    }

    this.currentCard = null;
    this.playerSection.style.display = 'none';
    this.gallerySection.style.display = 'block';

    const headerFilter = document.getElementById('header-filter-bar');
    if (headerFilter) {
      headerFilter.style.display = 'block';
      headerFilter.classList.remove('filter-hidden');
    }
    this.renderGallery();

    void document.body.offsetHeight;
    const scrollY = this.savedGalleryScrollY || 0;
    requestAnimationFrame(() => {
      window.scrollTo({ top: scrollY, behavior: 'instant' });
    });

    if (updateHistory) {
      const url = this._buildUrl({ cardId: null });
      window.history.pushState(
        { view: 'gallery', cat: this.activeCategory, scrollY: scrollY },
        '',
        url
      );
    }
  }

  setViewMode(mode, force = false) {
    const playerContent = document.getElementById('player-content-area');
    if (!playerContent) return;
    if (!force && this.currentViewMode === mode && playerContent.classList.contains(`mode-${mode}`)) return;
    
    this.currentViewMode = mode;

    // Sync segmented pill buttons
    const modeBtns = document.querySelectorAll('.mode-pill-btn');
    modeBtns.forEach((btn) => {
      const isActive = btn.dataset.mode === mode;
      btn.classList.toggle('active', isActive);
      btn.setAttribute('aria-selected', isActive ? 'true' : 'false');
    });

    // Apply layout class
    playerContent.className = `player-content-area mode-${mode}`;

    if (mode === 'canvas') {
      this.canvasContainer.style.display = 'flex';
      this.checklistContainer.style.display = 'none';
    } else if (mode === 'list') {
      this.canvasContainer.style.display = 'none';
      this.checklistContainer.style.display = 'grid';
    } else if (mode === 'split') {
      this.canvasContainer.style.display = 'flex';
      this.checklistContainer.style.display = 'grid';
    }

    this.renderer.resizeCanvas();
    this.renderer.render();
  }

  renderChecklist() {
    if (!this.currentCard || !this.checklistContainer) return;
    this.checklistContainer.innerHTML = '';

    const cols = Math.min(this.currentCard.grid.cols, 6);
    this.checklistContainer.style.gridTemplateColumns = `repeat(auto-fill, minmax(160px, 1fr))`;

    if (this.currentCard.type === 'bottle') {
      // Bottle slider cards
      this.currentCard.cells.forEach((cell) => {
        const item = document.createElement('div');
        item.className = 'bottle-cell';
        const pct = this.currentBottleLevels[cell.index] || 0;

        item.innerHTML = `
          <div class="bottle-cell-header">
            <span class="bottle-label">${cell.label || cell.text}</span>
            <span class="bottle-pct-badge" id="pct-badge-${cell.index}">${pct}%</span>
          </div>
          <div class="bottle-slider-wrap">
            <input type="range" class="bottle-slider" min="0" max="100" value="${pct}" data-idx="${cell.index}">
          </div>
        `;

        const slider = item.querySelector('.bottle-slider');
        slider?.addEventListener('input', (e) => {
          const val = parseInt(e.target.value, 10);
          this.updateBottleLevel(cell.index, val);
        });

        this.checklistContainer.appendChild(item);
      });
    } else {
      // Standard Bingo or checklist
      this.currentCard.cells.forEach((cell) => {
        const item = document.createElement('div');
        item.className = 'checklist-cell';
        if (this.currentChecks.has(cell.index)) {
          item.classList.add('checked');
        }

        item.innerHTML = `
          <div class="cell-coords">${cell.row + 1}-${cell.col + 1}</div>
          <div class="cell-text">${cell.text}</div>
          <div class="cell-check-indicator">
            <md-checkbox touch-target="none" ${this.currentChecks.has(cell.index) ? 'checked' : ''}></md-checkbox>
          </div>
        `;

        item.addEventListener('click', () => {
          this.toggleCell(cell.index);
        });

        this.checklistContainer.appendChild(item);
      });
    }
  }

  toggleCell(idx) {
    if (this.isViewingAuthor) {
      this.showToast('正在查看作者打卡，点击右上角切回个人模式以修改');
      return;
    }
    if (this.currentChecks.has(idx)) {
      this.currentChecks.delete(idx);
    } else {
      this.currentChecks.add(idx);
    }

    Storage.setChecks(this.currentCard.id, Array.from(this.currentChecks));
    this.updatePlayerState();
    this.syncChecklistCell(idx);
  }

  updateBottleLevel(idx, pct) {
    if (this.isViewingAuthor) {
      this.showToast('正在查看作者打卡，点击右上角切回个人模式以修改');
      return;
    }
    this.currentBottleLevels[idx] = pct;
    Storage.setBottleLevels(this.currentCard.id, this.currentBottleLevels);

    this.renderer.setBottleLevels(this.currentBottleLevels);

    // Sync badge and slider
    const badge = document.getElementById(`pct-badge-${idx}`);
    if (badge) badge.textContent = `${pct}%`;
    const slider = document.querySelector(`.bottle-slider[data-idx="${idx}"]`);
    if (slider && parseInt(slider.value, 10) !== pct) slider.value = pct;

    this.updatePlayerState();
  }

  syncChecklistCell(idx) {
    const cells = this.checklistContainer.querySelectorAll('.checklist-cell');
    const cellEl = cells[idx];
    if (!cellEl) return;

    const isChecked = this.currentChecks.has(idx);
    cellEl.classList.toggle('checked', isChecked);
    const cb = cellEl.querySelector('md-checkbox');
    if (cb) cb.checked = isChecked;
  }

  updatePlayerState() {
    if (!this.currentCard) return;

    if (this.currentCard.type === 'bottle') {
      const filledCount = Object.values(this.currentBottleLevels).filter(v => v > 0).length;
      const total = this.currentCard.cellCount;
      const statsText = document.getElementById('player-checked-stats');
      if (statsText) {
        statsText.textContent = `已填满 ${filledCount} / ${total} 个罐子`;
      }
      const linesBadge = document.getElementById('player-lines-badge');
      if (linesBadge) {
        linesBadge.textContent = `平均容量: ${this._calcAverageBottle()}%`;
        linesBadge.className = 'lines-badge';
      }
    } else {
      const result = checkBingo(
        this.currentCard.grid.rows,
        this.currentCard.grid.cols,
        Array.from(this.currentChecks)
      );

      this.renderer.setChecked(Array.from(this.currentChecks), result.lines);

      const count = this.currentChecks.size;
      const total = this.currentCard.cellCount;
      const percent = Math.round((count / total) * 100);

      const statsText = document.getElementById('player-checked-stats');
      if (statsText) {
        statsText.textContent = `已选 ${count} / ${total} (${percent}%)`;
      }

      const linesBadge = document.getElementById('player-lines-badge');
      if (linesBadge) {
        if (result.lineCount > 0) {
          linesBadge.textContent = `🎉 达成 ${result.lineCount} 条 BINGO 连线！`;
          linesBadge.className = 'lines-badge active';
        } else {
          linesBadge.textContent = `当前连线: 0 条`;
          linesBadge.className = 'lines-badge';
        }
      }
    }
  }

  _calcAverageBottle() {
    const vals = Object.values(this.currentBottleLevels);
    if (!vals || vals.length === 0) return 0;
    const sum = vals.reduce((a, b) => a + b, 0);
    return Math.round(sum / this.currentCard.cellCount);
  }

  clearCurrentCard() {
    if (!this.currentCard) return;
    if (this.currentCard.type === 'bottle') {
      this.currentBottleLevels = {};
      Storage.clearBottleLevels(this.currentCard.id);
      this.renderer.setBottleLevels({});
    } else {
      this.currentChecks.clear();
      Storage.clearChecks(this.currentCard.id);
      this.renderer.setChecked([]);
    }
    this.updatePlayerState();
    this.renderChecklist();
    this.showToast('已清空当前项目记录');
  }

  randomFillCurrentCard() {
    if (!this.currentCard) return;
    if (this.currentCard.type === 'bottle') {
      this.currentBottleLevels = {};
      this.currentCard.cells.forEach(c => {
        if (Math.random() > 0.4) {
          this.currentBottleLevels[c.index] = Math.round(Math.random() * 8 + 2) * 10;
        }
      });
      Storage.setBottleLevels(this.currentCard.id, this.currentBottleLevels);
      this.renderer.setBottleLevels(this.currentBottleLevels);
    } else {
      this.currentChecks.clear();
      const count = Math.floor(this.currentCard.cellCount * 0.4);
      const all = Array.from({ length: this.currentCard.cellCount }, (_, i) => i);
      all.sort(() => Math.random() - 0.5);
      for (let i = 0; i < count; i++) this.currentChecks.add(all[i]);
      Storage.setChecks(this.currentCard.id, Array.from(this.currentChecks));
      this.renderer.setChecked(Array.from(this.currentChecks));
    }
    this.updatePlayerState();
    this.renderChecklist();
    this.showToast('已随机生成打卡');
  }

  exportPersonalJSON() {
    const data = Storage.exportAllPersonalJSON();
    const str = JSON.stringify(data, null, 2);
    const blob = new Blob([str], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `personal_records.json`;
    a.click();
    URL.revokeObjectURL(url);
    this.showToast('📁 个人打卡记录已导出为 personal_records.json！放入 personal/ 文件夹即可向大家展示');
  }

  handleImportFile(e) {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (evt) => {
      try {
        const json = JSON.parse(evt.target.result);
        if (Storage.importPersonalJSON(json)) {
          this.showToast('🎉 成功导入个人打卡记录！');
          if (this.currentCard) this.loadCardState(this.currentCard);
          else this.renderGallery();
        } else {
          this.showToast('导入失败：文件格式不匹配');
        }
      } catch (err) {
        this.showToast('解析 JSON 失败');
      }
    };
    reader.readAsText(file);
    e.target.value = '';
  }

  openOriginalDialog() {
    if (!this.currentCard) return;
    const dialog = document.getElementById('original-dialog');
    const img = document.getElementById('original-dialog-img');
    const title = document.getElementById('original-dialog-title');
    if (img && title && dialog) {
      img.src = encodeURI(this.currentCard.filename);
      title.textContent = `原图查看 · ${this.currentCard.title}`;
      dialog.show();
    }
  }

  openWatermarkDialog() {
    const dialog = document.getElementById('watermark-dialog');
    const siteInput = document.getElementById('watermark-site-input');
    const subInput = document.getElementById('watermark-sub-input');
    const enableSwitch = document.getElementById('watermark-enable-switch');

    if (siteInput) siteInput.value = this.settings.watermarkSite || 'bingo.zgqinc.gq';
    if (subInput) subInput.value = this.settings.watermarkSub || '互联网宾果游戏个人收集 · 打卡记录';
    if (enableSwitch) enableSwitch.selected = this.settings.watermarkEnabled !== false;

    dialog?.show();
  }

  initDialogs() {
    // Download original image
    document.getElementById('btn-download-original')?.addEventListener('click', () => {
      if (!this.currentCard) return;
      const a = document.createElement('a');
      a.href = encodeURI(this.currentCard.filename);
      a.download = `[原图]_${this.currentCard.title}.${this.currentCard.filename.split('.').pop()}`;
      a.click();
    });

    // Save watermark settings
    document.getElementById('btn-save-watermark')?.addEventListener('click', () => {
      const siteInput = document.getElementById('watermark-site-input');
      const subInput = document.getElementById('watermark-sub-input');
      const enableSwitch = document.getElementById('watermark-enable-switch');

      this.settings.watermarkSite = siteInput?.value.trim() || 'bingo.zgqinc.gq';
      this.settings.watermarkSub = subInput?.value.trim() || '互联网宾果游戏个人收集 · 打卡记录';
      this.settings.watermarkEnabled = enableSwitch ? enableSwitch.selected : true;

      Storage.saveSettings(this.settings);
      this.renderer.setSettings(this.settings);
      document.getElementById('watermark-dialog')?.close();
      this.showToast('水印与域名设置已保存！');
    });
  }

  async exportImage() {
    if (!this.renderer || !this.currentCard) return;

    this.showToast('正在渲染高分辨率打卡图片...');
    const offscreenCanvas = await this.renderer.exportImageCanvas();
    if (!offscreenCanvas) {
      this.showToast('导出图片失败');
      return;
    }

    offscreenCanvas.toBlob((blob) => {
      if (!blob) {
        this.showToast('生成图片失败');
        return;
      }
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      const now = new Date();
      const timeStr = `${now.getFullYear()}${String(now.getMonth() + 1).padStart(2, '0')}${String(now.getDate()).padStart(2, '0')}_${String(now.getHours()).padStart(2, '0')}${String(now.getMinutes()).padStart(2, '0')}`;
      a.href = url;
      a.download = `${this.currentCard.title}_打卡_${timeStr}.png`;
      a.click();
      URL.revokeObjectURL(url);
      this.showToast('🎉 图片导出成功！');
    }, 'image/png');
  }

  showToast(msg) {
    if (!this.toast) return;
    this.toast.textContent = msg;
    this.toast.classList.add('show');
    clearTimeout(this._toastTimer);
    this._toastTimer = setTimeout(() => {
      this.toast.classList.remove('show');
    }, 2800);
  }
}

function initBingoApp() {
  if (!window.bingoApp) {
    window.bingoApp = new BingoApp();
  }
}

if (document.readyState === 'loading') {
  window.addEventListener('DOMContentLoaded', initBingoApp);
} else {
  initBingoApp();
}

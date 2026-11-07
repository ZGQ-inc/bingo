/**
 * Storage & Personal Records Management for Bingo & Bottle Web App
 */
const STORAGE_PREFIX = 'bingo_app_';

export const Storage = {
  // Checks for Bingo grids
  getChecks(cardId) {
    try {
      const data = localStorage.getItem(`${STORAGE_PREFIX}checks_${cardId}`);
      return data ? JSON.parse(data) : [];
    } catch (e) {
      console.warn('Failed to read checks from storage:', e);
      return [];
    }
  },

  setChecks(cardId, checkedIndices) {
    try {
      localStorage.setItem(`${STORAGE_PREFIX}checks_${cardId}`, JSON.stringify(checkedIndices));
    } catch (e) {
      console.warn('Failed to save checks to storage:', e);
    }
  },

  clearChecks(cardId) {
    try {
      localStorage.removeItem(`${STORAGE_PREFIX}checks_${cardId}`);
    } catch (e) {
      console.warn('Failed to clear checks:', e);
    }
  },

  // Bottle percentage levels { [itemIndex]: percent 0..100 }
  getBottleLevels(cardId) {
    try {
      const data = localStorage.getItem(`${STORAGE_PREFIX}bottles_${cardId}`);
      return data ? JSON.parse(data) : {};
    } catch (e) {
      console.warn('Failed to read bottle levels:', e);
      return {};
    }
  },

  setBottleLevels(cardId, levels) {
    try {
      localStorage.setItem(`${STORAGE_PREFIX}bottles_${cardId}`, JSON.stringify(levels));
    } catch (e) {
      console.warn('Failed to save bottle levels:', e);
    }
  },

  clearBottleLevels(cardId) {
    try {
      localStorage.removeItem(`${STORAGE_PREFIX}bottles_${cardId}`);
    } catch (e) {
      console.warn('Failed to clear bottle levels:', e);
    }
  },

  getAllCardStats() {
    const stats = {};
    try {
      for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i);
        if (key && key.startsWith(`${STORAGE_PREFIX}checks_`)) {
          const cardId = key.replace(`${STORAGE_PREFIX}checks_`, '');
          const val = JSON.parse(localStorage.getItem(key) || '[]');
          stats[cardId] = (stats[cardId] || 0) + val.length;
        } else if (key && key.startsWith(`${STORAGE_PREFIX}bottles_`)) {
          const cardId = key.replace(`${STORAGE_PREFIX}bottles_`, '');
          const val = JSON.parse(localStorage.getItem(key) || '{}');
          const filledCount = Object.values(val).filter(v => v > 0).length;
          stats[cardId] = (stats[cardId] || 0) + filledCount;
        }
      }
    } catch (e) {
      console.warn('Failed to get all card stats:', e);
    }
    return stats;
  },

  getSettings() {
    const defaultSettings = {
      watermarkEnabled: true,
      watermarkSite: 'bingo.zgqinc.gq',
      watermarkSub: 'ZGQ 的个人宾果收集 · 打卡记录',
      watermarkPos: 'bottom',
      stampStyle: 'circle',
      stampColor: '#e53935',
      liquidColor: '#e91e63', // pink/magenta for bottle fluid
      theme: 'auto',          // 'auto' | 'light' | 'dark'
      showWinningLines: true,
      viewingOwnerMode: false
    };
    try {
      const saved = localStorage.getItem(`${STORAGE_PREFIX}settings`);
      return saved ? { ...defaultSettings, ...JSON.parse(saved) } : defaultSettings;
    } catch (e) {
      return defaultSettings;
    }
  },

  saveSettings(settings) {
    try {
      localStorage.setItem(`${STORAGE_PREFIX}settings`, JSON.stringify(settings));
    } catch (e) {
      console.warn('Failed to save settings:', e);
    }
  },

  // Export full user records to JSON for personal folder
  exportAllPersonalJSON() {
    const records = {};
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (key && key.startsWith(`${STORAGE_PREFIX}checks_`)) {
        const cardId = key.replace(`${STORAGE_PREFIX}checks_`, '');
        records[cardId] = records[cardId] || {};
        records[cardId].checked = JSON.parse(localStorage.getItem(key) || '[]');
      } else if (key && key.startsWith(`${STORAGE_PREFIX}bottles_`)) {
        const cardId = key.replace(`${STORAGE_PREFIX}bottles_`, '');
        records[cardId] = records[cardId] || {};
        records[cardId].bottleLevels = JSON.parse(localStorage.getItem(key) || '{}');
      }
    }

    return {
      version: '1.0',
      owner: 'ZGQ',
      website: 'bingo.zgqinc.gq',
      exportedAt: new Date().toISOString(),
      records
    };
  },

  // Import personal JSON
  importPersonalJSON(data) {
    if (!data || !data.records) return false;
    try {
      for (const [cardId, val] of Object.entries(data.records)) {
        if (val.checked) {
          localStorage.setItem(`${STORAGE_PREFIX}checks_${cardId}`, JSON.stringify(val.checked));
        }
        if (val.bottleLevels) {
          localStorage.setItem(`${STORAGE_PREFIX}bottles_${cardId}`, JSON.stringify(val.bottleLevels));
        }
      }
      return true;
    } catch (e) {
      console.error('Failed to import personal records:', e);
      return false;
    }
  },

  // Fetch author's preloaded records from personal/personal_records.json
  async loadAuthorRecords() {
    try {
      const res = await fetch('personal/personal_records.json');
      if (res.ok) {
        return await res.json();
      }
    } catch (e) {
      console.warn('Author personal_records.json not available');
    }
    return null;
  }
};

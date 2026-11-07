/**
 * Enhanced Canvas Renderer for Bingo Cards & Bottle/Jar Percentage Sliders
 * Supports high-DPI interactive canvas and full-resolution export with watermark
 */

export class CanvasRenderer {
  constructor(canvas) {
    this.canvas = canvas;
    this.ctx = canvas.getContext('2d');
    this.image = null;
    this.card = null;
    this.checkedIndices = new Set();
    this.bottleLevels = {}; // { [index]: percent 0..100 }
    this.winningLines = [];
    this.hoverIndex = -1;
    this.isDragging = false;
    this.dragIndex = -1;

    this.settings = {
      stampStyle: 'circle',
      stampColor: '#e53935',
      liquidColor: '#e91e63',
      showWinningLines: true,
      watermarkEnabled: true,
      watermarkSite: 'bingo.zgqinc.gq',
      watermarkSub: '互联网宾果游戏个人收集 · 打卡记录',
      watermarkPos: 'bottom'
    };

    this.dpr = window.devicePixelRatio || 1;
    this.fitMode = "vertical";
    this._initEvents();
  }

  setCard(card, imageElement) {
    this.card = card;
    this.image = imageElement;
    this.resizeCanvas();
    this.render();
  }

  setChecked(checkedIndices, winningLines = []) {
    this.checkedIndices = new Set(checkedIndices);
    this.winningLines = winningLines;
    this.render();
  }

  setBottleLevels(levels) {
    this.bottleLevels = { ...levels };
    this.render();
  }

  setSettings(settings) {
    this.settings = { ...this.settings, ...settings };
    this.render();
  }

  resizeCanvas() {
    if (!this.image || !this.card) return;
    const playerArea = document.getElementById('player-content-area');
    const container = this.canvas.parentElement;
    if (!container) return;

    const aspect = this.image.naturalHeight / this.image.naturalWidth;
    const isMobile = window.innerWidth <= 768;
    const isSplit = playerArea?.classList.contains('mode-split');
    const isImmersive = isMobile && !!document.getElementById('player-section')?.classList.contains('mobile-immersive');

    const baseWidth = playerArea ? playerArea.clientWidth : (window.innerWidth - 32);

    let displayWidth, displayHeight;

    if (isMobile) {
      if (isImmersive) {
        // Mobile Full Width Immersive: spans full viewport width, exactly proportional height!
        displayWidth = window.innerWidth;
        displayHeight = Math.round(displayWidth * aspect);
      } else if (isSplit) {
        // Mobile Split Mode: fit neatly inside top preview area without inner scrolling
        const maxMobileH = Math.max(260, Math.round(window.innerHeight * 0.44));
        displayHeight = Math.min(maxMobileH, (baseWidth - 36) * aspect);
        displayWidth = Math.round(displayHeight / aspect);
        if (displayWidth > (baseWidth - 36)) {
          displayWidth = baseWidth - 36;
          displayHeight = Math.round(displayWidth * aspect);
        }
      } else {
        // Mobile Standard Canvas Mode: fit comfortably inside card container without horizontal overflow
        const availW = Math.max(260, baseWidth - 36);
        displayWidth = Math.min(availW, this.image.naturalWidth);
        displayHeight = Math.round(displayWidth * aspect);
      }
    } else {
      // PC / Desktop
      if (this.fitMode === 'vertical') {
        const availHeight = Math.max(360, window.innerHeight - 230);
        displayHeight = Math.min(availHeight, this.image.naturalHeight);
        displayWidth = Math.round(displayHeight / aspect);
        const maxAvailW = Math.max(320, baseWidth - 40);
        if (displayWidth > maxAvailW) {
          displayWidth = maxAvailW;
          displayHeight = Math.round(displayWidth * aspect);
        }
      } else {
        const maxAvailW = Math.max(320, baseWidth - 40);
        displayWidth = Math.min(maxAvailW, Math.max(this.image.naturalWidth, 880));
        displayHeight = Math.round(displayWidth * aspect);
      }
    }

    this.canvas.style.aspectRatio = `${this.image.naturalWidth} / ${this.image.naturalHeight}`;
    this.canvas.style.width = `${Math.round(displayWidth)}px`;
    this.canvas.style.height = `${Math.round(displayHeight)}px`;

    this.canvas.width = Math.round(displayWidth * this.dpr);
    this.canvas.height = Math.round(displayHeight * this.dpr);

    this.scale = this.canvas.width / this.image.naturalWidth;
  }

  toggleFitMode() {
    this.fitMode = this.fitMode === 'vertical' ? 'width' : 'vertical';
    this.resizeCanvas();
    this.render();
    return this.fitMode;
  }

  _initEvents() {
    const getPos = (clientX, clientY) => {
      if (!this.card) return { x: 0, y: 0, index: -1 };
      const rect = this.canvas.getBoundingClientRect();
      if (!rect.width || !rect.height) return { x: 0, y: 0, index: -1 };
      const x = (clientX - rect.left) * (this.image.naturalWidth / rect.width);
      const y = (clientY - rect.top) * (this.image.naturalHeight / rect.height);

      let hitIdx = -1;
      for (let i = 0; i < this.card.cells.length; i++) {
        const c = this.card.cells[i];
        if (x >= c.x && x < c.x + c.w && y >= c.y && y < c.y + c.h) {
          hitIdx = i;
          break;
        }
      }
      return { x, y, index: hitIdx };
    };

    const updateBottleDrag = (x, y, idx) => {
      if (this.card.type !== 'bottle' || idx === -1) return;
      const cell = this.card.cells[idx];
      if (!cell) return;

      const yBot = cell.y_bottom || (cell.y + cell.h);
      const bh = cell.bh || cell.h;
      const pct = Math.max(0, Math.min(100, Math.round(((yBot - y) / bh) * 100)));

      this.bottleLevels[idx] = pct;
      this.render();
      if (this.onBottleChange) {
        this.onBottleChange(idx, pct);
      }
    };

    this.canvas.addEventListener('mousedown', (e) => {
      const pos = getPos(e.clientX, e.clientY);
      if (pos.index !== -1) {
        if (this.card?.type === 'bottle') {
          this.isDragging = true;
          this.dragIndex = pos.index;
          updateBottleDrag(pos.x, pos.y, pos.index);
        } else {
          if (this.onCellClick) this.onCellClick(pos.index);
        }
      }
    });

    window.addEventListener('mousemove', (e) => {
      if (this.isDragging && this.dragIndex !== -1) {
        const pos = getPos(e.clientX, e.clientY);
        updateBottleDrag(pos.x, pos.y, this.dragIndex);
        return;
      }

      const pos = getPos(e.clientX, e.clientY);
      if (pos.index !== this.hoverIndex) {
        this.hoverIndex = pos.index;
        this.render();
        this.canvas.style.cursor = pos.index !== -1 ? 'pointer' : 'default';
      }
    });

    window.addEventListener('mouseup', () => {
      if (this.isDragging) {
        this.isDragging = false;
        this.dragIndex = -1;
      }
    });

    // Touch events for mobile
    this.canvas.addEventListener('touchstart', (e) => {
      if (e.touches.length === 1) {
        const t = e.touches[0];
        const pos = getPos(t.clientX, t.clientY);
        if (pos.index !== -1) {
          this.hoverIndex = pos.index;
          if (this.card?.type === 'bottle') {
            this.isDragging = true;
            this.dragIndex = pos.index;
            updateBottleDrag(pos.x, pos.y, pos.index);
          } else {
            if (this.onCellClick) this.onCellClick(pos.index);
          }
          this.render();
        }
      }
    }, { passive: true });

    this.canvas.addEventListener('touchmove', (e) => {
      if (this.isDragging && this.dragIndex !== -1 && e.touches.length === 1) {
        const t = e.touches[0];
        const pos = getPos(t.clientX, t.clientY);
        updateBottleDrag(pos.x, pos.y, this.dragIndex);
      }
    }, { passive: true });

    this.canvas.addEventListener('touchend', () => {
      this.isDragging = false;
      this.dragIndex = -1;
      this.hoverIndex = -1;
      this.render();
    });

    this.canvas.addEventListener('mouseleave', () => {
      if (!this.isDragging && this.hoverIndex !== -1) {
        this.hoverIndex = -1;
        this.render();
      }
    });

    window.addEventListener('resize', () => {
      this.resizeCanvas();
      this.render();
    });
  }

  render() {
    if (!this.image || !this.card || !this.ctx) return;
    const ctx = this.ctx;
    ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

    ctx.save();
    ctx.scale(this.scale, this.scale);

    // 1. Draw base image
    ctx.drawImage(this.image, 0, 0, this.image.naturalWidth, this.image.naturalHeight);

    // 2. Draw Bottle Fluid if card is bottle type
    if (this.card.type === 'bottle') {
      this._renderAllBottles(ctx);
    } else {
      // 3. Draw Bingo Marks
      for (const idx of this.checkedIndices) {
        const cell = this.card.cells[idx];
        if (cell) this._drawStamp(ctx, cell, idx);
      }

      // 4. Draw Winning Lines
      if (this.settings.showWinningLines && this.winningLines.length > 0) {
        this._drawWinningLines(ctx);
      }
    }

    // 5. Draw Hover indicator
    if (this.hoverIndex !== -1 && this.card.cells[this.hoverIndex]) {
      const cell = this.card.cells[this.hoverIndex];
      ctx.save();
      if (this.card.type === 'bottle') {
        ctx.fillStyle = 'rgba(233, 30, 99, 0.12)';
        ctx.strokeStyle = '#e91e63';
        const bx = cell.bx || cell.x;
        const bw = cell.bw || cell.w;
        const by = cell.by || cell.y;
        const bh = cell.bh || cell.h;
        ctx.beginPath();
        if (ctx.roundRect) {
          ctx.roundRect(bx - 2, by - 2, bw + 4, bh + 4, 8);
        } else {
          ctx.rect(bx - 2, by - 2, bw + 4, bh + 4);
        }
        ctx.fill();
        ctx.lineWidth = 2;
        ctx.stroke();
      } else if (cell.check_box) {
        // Checklist with explicit checkbox: soft row highlight + crisp checkbox stroke
        ctx.fillStyle = 'rgba(25, 118, 210, 0.08)';
        ctx.beginPath();
        if (ctx.roundRect) {
          ctx.roundRect(cell.x, cell.y, cell.w, cell.h, 6);
        } else {
          ctx.rect(cell.x, cell.y, cell.w, cell.h);
        }
        ctx.fill();

        const cb = cell.check_box;
        ctx.strokeStyle = '#1976d2';
        ctx.lineWidth = 2.5;
        ctx.beginPath();
        if (ctx.roundRect) {
          ctx.roundRect(cb.x - 1, cb.y - 1, cb.w + 2, cb.h + 2, 4);
        } else {
          ctx.rect(cb.x - 1, cb.y - 1, cb.w + 2, cb.h + 2);
        }
        ctx.stroke();
      } else {
        ctx.fillStyle = 'rgba(25, 118, 210, 0.15)';
        ctx.strokeStyle = '#1976d2';
        ctx.beginPath();
        if (ctx.roundRect) {
          ctx.roundRect(cell.x + 1, cell.y + 1, cell.w - 2, cell.h - 2, 4);
        } else {
          ctx.rect(cell.x + 1, cell.y + 1, cell.w - 2, cell.h - 2);
        }
        ctx.fill();
        ctx.lineWidth = 2.5;
        ctx.stroke();
      }
      ctx.restore();
    }

    ctx.restore();
  }

  _renderAllBottles(ctx) {
    const liquidColor = this.settings.liquidColor || '#e91e63';

    for (let i = 0; i < this.card.cells.length; i++) {
      const cell = this.card.cells[i];
      const pct = this.bottleLevels[i] || 0;
      if (pct <= 0) continue;

      const yBot = cell.y_bottom || (cell.y + cell.h);
      const bh = cell.bh || cell.h;
      const bw = cell.bw || (cell.w - 4);
      const bx = cell.bx || cell.x;
      const fillHeight = bh * (pct / 100);
      const fillY = yBot - fillHeight;

      ctx.save();
      // Fluid Fill
      ctx.fillStyle = liquidColor;
      ctx.globalAlpha = 0.68;

      // Rounded bottom contour matching jar bottom curve; round top at 100%
      ctx.beginPath();
      const cornerR = Math.min(10, fillHeight);
      const topR = pct >= 98 ? 4 : 0;
      if (ctx.roundRect) {
        ctx.roundRect(bx, fillY, bw, fillHeight, [topR, topR, cornerR, cornerR]);
      } else {
        ctx.rect(bx, fillY, bw, fillHeight);
      }
      ctx.fill();

      // Fluid surface highlight
      if (pct > 0 && pct < 100) {
        ctx.globalAlpha = 0.9;
        ctx.fillStyle = '#ffffff';
        ctx.fillRect(bx + 2, fillY, bw - 4, 2);
      }

      // Percentage Text Tag with clear pill badge for 100% contrast
      ctx.globalAlpha = 1.0;
      const fontSize = Math.max(11, Math.round(bw * 0.28));
      ctx.font = `bold ${fontSize}px sans-serif`;
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      const textX = cell.cx || (bx + bw / 2);
      let textY = fillHeight >= (fontSize + 8) ? (fillY + fillHeight / 2) : (fillY - fontSize / 2 - 3);

      const txt = `${pct}%`;
      const tw = ctx.measureText(txt).width;
      ctx.fillStyle = 'rgba(0, 0, 0, 0.62)';
      if (ctx.roundRect) {
        ctx.beginPath();
        ctx.roundRect(textX - tw / 2 - 4, textY - fontSize / 2 - 2, tw + 8, fontSize + 4, 4);
        ctx.fill();
      }
      ctx.fillStyle = '#ffffff';
      ctx.fillText(txt, textX, textY);

      ctx.restore();
    }
  }

  _drawStamp(ctx, cell, idx) {
    let cx = cell.x + cell.w / 2;
    let cy = cell.y + cell.h / 2;
    let radius = Math.min(cell.w, cell.h) * 0.38;
    const color = this.settings.stampColor || '#e53935';

    if (cell.check_box) {
      cx = cell.check_box.x + cell.check_box.w / 2;
      cy = cell.check_box.y + cell.check_box.h / 2;
      radius = Math.min(cell.check_box.w, cell.check_box.h) * 0.42;
    }

    ctx.save();
    switch (this.settings.stampStyle) {
      case 'stamp': {
        ctx.translate(cx, cy);
        const tilt = ((idx % 7) - 3) * 0.05;
        ctx.rotate(tilt);
        ctx.strokeStyle = color;
        ctx.fillStyle = color;
        ctx.lineWidth = Math.max(2.5, cell.w * 0.035);

        ctx.beginPath();
        ctx.arc(0, 0, radius, 0, Math.PI * 2);
        ctx.stroke();

        ctx.beginPath();
        ctx.arc(0, 0, radius * 0.82, 0, Math.PI * 2);
        ctx.stroke();

        ctx.font = `bold ${Math.round(radius * 0.68)}px sans-serif`;
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText('PASS', 0, 0);
        ctx.globalAlpha = 0.88;
        break;
      }
      case 'highlighter': {
        ctx.fillStyle = color;
        ctx.globalAlpha = 0.35;
        const padX = cell.w * 0.08;
        const padY = cell.h * 0.08;
        ctx.beginPath();
        if (ctx.roundRect) {
          ctx.roundRect(cell.x + padX, cell.y + padY, cell.w - padX * 2, cell.h - padY * 2, 8);
        } else {
          ctx.rect(cell.x + padX, cell.y + padY, cell.w - padX * 2, cell.h - padY * 2);
        }
        ctx.fill();
        ctx.globalAlpha = 0.6;
        ctx.strokeStyle = color;
        ctx.lineWidth = 2;
        ctx.stroke();
        break;
      }
      case 'check': {
        ctx.strokeStyle = color;
        ctx.lineWidth = Math.max(4, cell.w * 0.06);
        ctx.lineCap = 'round';
        ctx.lineJoin = 'round';
        ctx.globalAlpha = 0.9;
        const size = radius * 0.9;
        ctx.beginPath();
        ctx.moveTo(cx - size * 0.6, cy);
        ctx.lineTo(cx - size * 0.15, cy + size * 0.5);
        ctx.lineTo(cx + size * 0.65, cy - size * 0.6);
        ctx.stroke();
        break;
      }
      case 'cross': {
        ctx.strokeStyle = color;
        ctx.lineWidth = Math.max(4, cell.w * 0.06);
        ctx.lineCap = 'round';
        ctx.globalAlpha = 0.88;
        const size = radius * 0.65;
        ctx.beginPath();
        ctx.moveTo(cx - size, cy - size);
        ctx.lineTo(cx + size, cy + size);
        ctx.moveTo(cx + size, cy - size);
        ctx.lineTo(cx - size, cy + size);
        ctx.stroke();
        break;
      }
      case 'circle':
      default: {
        ctx.strokeStyle = color;
        ctx.lineWidth = Math.max(3.5, cell.w * 0.045);
        ctx.lineCap = 'round';
        ctx.globalAlpha = 0.82;

        const points = 16;
        const seed = (idx + 1) * 9301 + 49297;
        ctx.beginPath();
        for (let i = 0; i <= points; i++) {
          const angle = (i / points) * Math.PI * 2;
          const pseudoRand = Math.sin(seed + i * 2.1) * (radius * 0.09);
          const r = radius + pseudoRand;
          const px = cx + Math.cos(angle) * r;
          const py = cy + Math.sin(angle) * r;
          if (i === 0) ctx.moveTo(px, py);
          else ctx.lineTo(px, py);
        }
        ctx.closePath();
        ctx.stroke();
        ctx.fillStyle = color;
        ctx.globalAlpha = 0.12;
        ctx.fill();
        break;
      }
    }
    ctx.restore();
  }

  _drawWinningLines(ctx) {
    ctx.save();
    ctx.lineWidth = Math.max(6, (this.card.cells[0]?.w || 100) * 0.08);
    ctx.lineCap = 'round';
    ctx.strokeStyle = '#ff9800';
    ctx.shadowColor = 'rgba(255, 152, 0, 0.7)';
    ctx.shadowBlur = 12;

    for (const line of this.winningLines) {
      if (!line.cells || line.cells.length === 0) continue;
      const firstCell = this.card.cells[line.cells[0]];
      const lastCell = this.card.cells[line.cells[line.cells.length - 1]];
      if (!firstCell || !lastCell) continue;

      const x1 = firstCell.x + firstCell.w / 2;
      const y1 = firstCell.y + firstCell.h / 2;
      const x2 = lastCell.x + lastCell.w / 2;
      const y2 = lastCell.y + lastCell.h / 2;

      ctx.beginPath();
      ctx.moveTo(x1, y1);
      ctx.lineTo(x2, y2);
      ctx.stroke();
    }
    ctx.restore();
  }

  async exportImageCanvas() {
    if (!this.image || !this.card) return null;
    const nativeW = this.image.naturalWidth;
    const nativeH = this.image.naturalHeight;
    const watermarkHeight = this.settings.watermarkEnabled ? Math.max(56, Math.round(nativeH * 0.065)) : 0;
    const totalH = nativeH + watermarkHeight;

    const offscreen = document.createElement('canvas');
    offscreen.width = nativeW;
    offscreen.height = totalH;
    const ctx = offscreen.getContext('2d');

    // 1. Draw image
    ctx.drawImage(this.image, 0, 0, nativeW, nativeH);

    // 2. Draw bottle fills or marks
    if (this.card.type === 'bottle') {
      this._renderAllBottles(ctx);
    } else {
      for (const idx of this.checkedIndices) {
        const cell = this.card.cells[idx];
        if (cell) this._drawStamp(ctx, cell, idx);
      }
      if (this.settings.showWinningLines && this.winningLines.length > 0) {
        this._drawWinningLines(ctx);
      }
    }

    // 3. Draw Watermark Footer
    if (this.settings.watermarkEnabled) {
      this._drawWatermark(ctx, nativeW, nativeH, watermarkHeight);
    }

    return offscreen;
  }

  _drawWatermark(ctx, width, nativeH, barHeight) {
    ctx.save();
    // Dark elegant frosted banner
    ctx.fillStyle = '#10141a';
    ctx.fillRect(0, nativeH, width, barHeight);

    // Cyan/Blue highlight top border
    const grad = ctx.createLinearGradient(0, nativeH, width, nativeH);
    grad.addColorStop(0, '#0061a4');
    grad.addColorStop(0.5, '#00a0dc');
    grad.addColorStop(1, '#7d5260');
    ctx.fillStyle = grad;
    ctx.fillRect(0, nativeH, width, Math.max(3, Math.round(barHeight * 0.06)));

    const fontSize = Math.max(14, Math.round(barHeight * 0.36));
    const smallFontSize = Math.max(11, Math.round(barHeight * 0.23));

    // Left Website Address
    ctx.fillStyle = '#ffffff';
    ctx.font = `600 ${fontSize}px system-ui, -apple-system, sans-serif`;
    ctx.textAlign = 'left';
    ctx.textBaseline = 'middle';
    const siteText = this.settings.watermarkSite || 'bingo.zgqinc.gq';
    const paddingX = Math.max(18, width * 0.035);
    ctx.fillText(`🌐 ${siteText}`, paddingX, nativeH + barHeight * 0.44);

    // Subtitle
    ctx.fillStyle = '#9ca3af';
    ctx.font = `normal ${smallFontSize}px system-ui, -apple-system, sans-serif`;
    const subText = this.settings.watermarkSub || '互联网宾果游戏个人收集 · 打卡记录';
    ctx.fillText(subText, paddingX, nativeH + barHeight * 0.78);

    // Right Stats
    ctx.textAlign = 'right';
    let statText = '';
    if (this.card.type === 'bottle') {
      const filled = Object.values(this.bottleLevels).filter(v => v > 0).length;
      statText = `🧪 已填满 ${filled} / ${this.card.cellCount} 个罐子`;
    } else {
      const bingoCount = this.winningLines.length;
      statText = bingoCount > 0 ? `🎉 ${bingoCount} BINGO 连线!` : `已打卡 ${this.checkedIndices.size} 项`;
    }

    ctx.fillStyle = '#ffb74d';
    ctx.font = `bold ${fontSize}px system-ui, -apple-system, sans-serif`;
    ctx.fillText(statText, width - paddingX, nativeH + barHeight * 0.44);

    const now = new Date();
    const dateStr = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`;
    ctx.fillStyle = '#9ca3af';
    ctx.font = `normal ${smallFontSize}px system-ui, -apple-system, sans-serif`;
    ctx.fillText(dateStr, width - paddingX, nativeH + barHeight * 0.78);

    ctx.restore();
  }
}

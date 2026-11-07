/**
 * Bingo Logic: Computes completed rows, columns, diagonals and winning lines
 */
export function checkBingo(rows, cols, checkedIndices) {
  const checkedSet = new Set(checkedIndices);
  const lines = [];

  // 1. Check Rows
  for (let r = 0; r < rows; r++) {
    let rowComplete = true;
    const rowCells = [];
    for (let c = 0; c < cols; c++) {
      const idx = r * cols + c;
      rowCells.push(idx);
      if (!checkedSet.has(idx)) {
        rowComplete = false;
      }
    }
    if (rowComplete) {
      lines.push({
        type: 'row',
        index: r,
        cells: rowCells
      });
    }
  }

  // 2. Check Columns
  for (let c = 0; c < cols; c++) {
    let colComplete = true;
    const colCells = [];
    for (let r = 0; r < rows; r++) {
      const idx = r * cols + c;
      colCells.push(idx);
      if (!checkedSet.has(idx)) {
        colComplete = false;
      }
    }
    if (colComplete) {
      lines.push({
        type: 'col',
        index: c,
        cells: colCells
      });
    }
  }

  // 3. Check Diagonals (only if square grid)
  if (rows === cols) {
    // Main diagonal (\)
    let diag1Complete = true;
    const diag1Cells = [];
    for (let i = 0; i < rows; i++) {
      const idx = i * cols + i;
      diag1Cells.push(idx);
      if (!checkedSet.has(idx)) {
        diag1Complete = false;
      }
    }
    if (diag1Complete) {
      lines.push({
        type: 'diag_main',
        cells: diag1Cells
      });
    }

    // Anti-diagonal (/)
    let diag2Complete = true;
    const diag2Cells = [];
    for (let i = 0; i < rows; i++) {
      const idx = i * cols + (cols - 1 - i);
      diag2Cells.push(idx);
      if (!checkedSet.has(idx)) {
        diag2Complete = false;
      }
    }
    if (diag2Complete) {
      lines.push({
        type: 'diag_anti',
        cells: diag2Cells
      });
    }
  }

  return {
    lineCount: lines.length,
    lines,
    isBingo: lines.length > 0
  };
}

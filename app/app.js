(function () {
  'use strict';

  const state = {
    mergeFiles: [],
    selectedMergeIndex: -1,
    splitFile: null,
  };

  const elements = {};

  function parsePageRanges(rangeText, pageCount) {
    const ranges = [];
    for (const rawPart of rangeText.split(',')) {
      const part = rawPart.trim();
      if (!part) continue;
      let start;
      let end;
      if (part.includes('-')) {
        const pieces = part.split('-');
        if (pieces.length !== 2) throw new Error(`ページ範囲が不正です: ${part}`);
        start = Number.parseInt(pieces[0].trim(), 10);
        end = Number.parseInt(pieces[1].trim(), 10);
      } else {
        start = Number.parseInt(part, 10);
        end = start;
      }
      if (!Number.isInteger(start) || !Number.isInteger(end) || start < 1 || end < start || end > pageCount) {
        throw new Error(`ページ範囲が不正です: ${part}`);
      }
      ranges.push([start, end]);
    }
    if (ranges.length === 0) throw new Error('ページ範囲を入力してください。');
    return ranges;
  }

  function log(message) {
    if (elements.log) elements.log.textContent = message;
  }

  function setStatus() {
    const ready = Boolean(window.PDFLib);
    elements.libraryStatus.textContent = ready
      ? 'PDF 処理ライブラリ: 使用可能'
      : 'PDF 処理ライブラリを読み込めません。インターネット接続、または社内配布版の同梱ライブラリを確認してください。';
    elements.libraryStatus.className = `status ${ready ? 'status-ok' : 'status-warn'}`;
    elements.mergeButton.disabled = !ready;
    elements.splitButton.disabled = !ready;
    log(ready ? '準備完了。PDF を選択してください。' : elements.libraryStatus.textContent);
  }

  function fileBaseName(file) {
    return file.name.replace(/\.pdf$/i, '');
  }

  function downloadBytes(bytes, fileName) {
    const blob = new Blob([bytes], { type: 'application/pdf' });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = fileName;
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    URL.revokeObjectURL(url);
  }

  function renderMergeList() {
    elements.mergeList.innerHTML = '';
    state.mergeFiles.forEach((file, index) => {
      const item = document.createElement('li');
      item.textContent = `${index + 1}. ${file.name}`;
      if (index === state.selectedMergeIndex) item.classList.add('selected');
      item.addEventListener('click', () => {
        state.selectedMergeIndex = index;
        renderMergeList();
      });
      elements.mergeList.appendChild(item);
    });
  }

  function moveSelectedMergeFile(direction) {
    const index = state.selectedMergeIndex;
    const nextIndex = index + direction;
    if (index < 0 || nextIndex < 0 || nextIndex >= state.mergeFiles.length) return;
    [state.mergeFiles[index], state.mergeFiles[nextIndex]] = [state.mergeFiles[nextIndex], state.mergeFiles[index]];
    state.selectedMergeIndex = nextIndex;
    renderMergeList();
  }

  async function mergePdfs() {
    if (state.mergeFiles.length < 2) {
      log('2つ以上の PDF を選択してください。');
      return;
    }
    try {
      const { PDFDocument } = window.PDFLib;
      const mergedPdf = await PDFDocument.create();
      for (const file of state.mergeFiles) {
        const sourcePdf = await PDFDocument.load(await file.arrayBuffer());
        const copiedPages = await mergedPdf.copyPages(sourcePdf, sourcePdf.getPageIndices());
        copiedPages.forEach((page) => mergedPdf.addPage(page));
      }
      const bytes = await mergedPdf.save();
      downloadBytes(bytes, 'merged.pdf');
      log(`統合が完了しました: ${state.mergeFiles.length} ファイル`);
    } catch (error) {
      log(`PDF の統合に失敗しました: ${error.message}`);
    }
  }

  async function splitPdf() {
    if (!state.splitFile) {
      log('分割する PDF を選択してください。');
      return;
    }
    try {
      const { PDFDocument } = window.PDFLib;
      const sourcePdf = await PDFDocument.load(await state.splitFile.arrayBuffer());
      const pageCount = sourcePdf.getPageCount();
      const mode = document.querySelector('input[name="splitMode"]:checked').value;
      const ranges = mode === 'pages'
        ? Array.from({ length: pageCount }, (_, index) => [index + 1, index + 1])
        : parsePageRanges(elements.rangeText.value, pageCount);

      for (const [start, end] of ranges) {
        const splitPdfDocument = await PDFDocument.create();
        const pageIndexes = Array.from({ length: end - start + 1 }, (_, index) => start - 1 + index);
        const copiedPages = await splitPdfDocument.copyPages(sourcePdf, pageIndexes);
        copiedPages.forEach((page) => splitPdfDocument.addPage(page));
        const bytes = await splitPdfDocument.save();
        downloadBytes(bytes, `${fileBaseName(state.splitFile)}_${start}-${end}.pdf`);
      }
      log(`分割が完了しました: ${ranges.length} ファイル`);
    } catch (error) {
      log(`PDF の分割に失敗しました: ${error.message}`);
    }
  }

  function bindDom() {
    for (const id of ['libraryStatus', 'mergeFiles', 'mergeList', 'moveUp', 'moveDown', 'clearMerge', 'mergeButton', 'splitFile', 'splitFileName', 'rangeText', 'splitButton', 'log']) {
      elements[id] = document.getElementById(id);
    }

    elements.mergeFiles.addEventListener('change', (event) => {
      state.mergeFiles.push(...Array.from(event.target.files));
      state.selectedMergeIndex = state.mergeFiles.length ? state.mergeFiles.length - 1 : -1;
      event.target.value = '';
      renderMergeList();
      log(`${state.mergeFiles.length} 個の PDF が統合リストにあります。`);
    });
    elements.moveUp.addEventListener('click', () => moveSelectedMergeFile(-1));
    elements.moveDown.addEventListener('click', () => moveSelectedMergeFile(1));
    elements.clearMerge.addEventListener('click', () => {
      state.mergeFiles = [];
      state.selectedMergeIndex = -1;
      renderMergeList();
      log('統合リストをクリアしました。');
    });
    elements.mergeButton.addEventListener('click', mergePdfs);
    elements.splitFile.addEventListener('change', (event) => {
      state.splitFile = event.target.files[0] || null;
      elements.splitFileName.textContent = state.splitFile ? state.splitFile.name : '未選択';
      log(state.splitFile ? `${state.splitFile.name} を選択しました。` : '分割する PDF が未選択です。');
    });
    elements.splitButton.addEventListener('click', splitPdf);

    setStatus();
    window.addEventListener('load', setStatus);
  }

  if (typeof module !== 'undefined') {
    module.exports = { parsePageRanges };
  }
  if (typeof window !== 'undefined') {
    window.PdfToolbox = { parsePageRanges };
    document.addEventListener('DOMContentLoaded', bindDom);
  }
}());

const assert = require('node:assert/strict');
const test = require('node:test');

const { parsePageRanges } = require('../app/app.js');

test('parsePageRanges accepts single pages and ranges', () => {
  assert.deepEqual(parsePageRanges('1-3, 5, 8-10', 10), [[1, 3], [5, 5], [8, 10]]);
});

test('parsePageRanges rejects out-of-bounds pages', () => {
  assert.throws(() => parsePageRanges('1-4', 3), /ページ範囲が不正です/);
});

test('parsePageRanges rejects empty input', () => {
  assert.throws(() => parsePageRanges(' , ', 5), /ページ範囲を入力してください/);
});

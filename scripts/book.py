#!/usr/bin/env python3
"""Locate and read the two textbook PDFs with Python stdlib + Poppler."""
import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BOOKS = json.loads((ROOT / 'references/books.json').read_text(encoding='utf-8'))['volumes']
CHAPTERS = json.loads((ROOT / 'references/chapters.json').read_text(encoding='utf-8'))


def run(tool, *args):
    if not shutil.which(tool):
        raise ValueError(f'缺少 {tool}，请安装 Poppler（见 README）。')
    p = subprocess.run([tool, *map(str, args)], capture_output=True)
    if p.returncode:
        raise ValueError(p.stderr.decode('utf-8', errors='replace').strip())
    return p.stdout.decode('utf-8', errors='replace')


def pdf_path(a):
    p = Path(a.pdf).expanduser() if a.pdf else ROOT / BOOKS[a.volume]['file']
    if not p.is_file():
        raise ValueError(f'未找到 PDF：{p}；使用 --pdf 或 fetch。')
    return p


def page_count(p):
    m = re.search(r'^Pages:\s+(\d+)', run('pdfinfo', p), re.M)
    if not m:
        raise ValueError('无法读取 PDF 页数。')
    return int(m.group(1))


def bounds(a, total):
    first = a.page if a.page is not None else a.book_page + BOOKS[a.volume]['printed_offset']
    last = first + a.count - 1
    if first < 1 or a.count < 1 or last > total:
        raise ValueError(f'页范围 {first}–{last} 超出 PDF 的 1–{total} 页。')
    return first, last


def extract(p, first, last):
    pages = run('pdftotext', '-f', first, '-l', last, '-layout', p, '-').split('\f')
    # Poppler terminates the last real page with a form feed.
    if pages and not pages[-1].strip():
        pages.pop()
    return pages


def digest(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda: f.read(4 * 1024 * 1024), b''):
            h.update(b)
    return h.hexdigest()


def fetch(volume):
    for v in (BOOKS if volume == 'all' else [volume]):
        b = BOOKS[v]
        dest = ROOT / b['file']
        if dest.exists():
            if dest.stat().st_size == b['bytes'] and digest(dest) == b['sha256']:
                print(f'{v}: 已存在且校验通过')
                continue
            raise ValueError(f'{dest} 已存在但校验不符；保留原文件，请移开后重试。')
        dest.parent.mkdir(parents=True, exist_ok=True)
        temp = None
        try:
            with tempfile.NamedTemporaryFile(dir=dest.parent, suffix='.part', delete=False) as out:
                temp = Path(out.name)
                req = urllib.request.Request(b['download_url'], headers={'User-Agent': 'study-biochemistry/1.0'})
                with urllib.request.urlopen(req, timeout=60) as response:
                    shutil.copyfileobj(response, out, 1024 * 1024)
            if temp.stat().st_size != b['bytes'] or digest(temp) != b['sha256']:
                raise ValueError(f'{v}: 下载文件大小或 SHA-256 不匹配。')
            temp.replace(dest)
            print(f'{v}: 下载并校验通过，{dest}')
        finally:
            if temp is not None:
                temp.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subs = parser.add_subparsers(dest='command', required=True)
    for command in ['inspect', 'toc', 'read', 'search', 'render', 'fetch']:
        sub = subs.add_parser(command)
        sub.add_argument('--volume', choices=['upper', 'lower'] + (['all'] if command == 'fetch' else []), default='upper')
        if command not in ['fetch', 'toc']:
            sub.add_argument('--pdf', help='本地 PDF 路径；覆盖默认 books/ 路径')
        if command in ['read', 'render']:
            pages = sub.add_mutually_exclusive_group(required=True)
            pages.add_argument('--page', type=int, help='PDF 物理页，从 1 开始')
            pages.add_argument('--book-page', type=int, help='书内阿拉伯页码；仅适用于本版本正文')
            sub.add_argument('--count', type=int, default=1)
        if command == 'render':
            sub.add_argument('--out', required=True, help='PNG 文件前缀，例如 work/page')
        if command == 'search':
            sub.add_argument('--term', action='append', required=True, help='字面关键词，可重复；按“或”匹配')
            sub.add_argument('--chapter', type=int)
            sub.add_argument('--limit', type=int, default=8, help='最多返回命中页数')
        if command == 'inspect':
            sub.add_argument('--verify', action='store_true', help='另核对大小与 SHA-256')
    a = parser.parse_args()
    if a.command == 'fetch':
        fetch(a.volume)
        return
    chapters = [c for c in CHAPTERS if c['volume'] == a.volume]
    if a.command == 'toc':
        for c in chapters:
            print(f"{c['chapter']:>2} {c['title']} | 书内 {c['printed_start']}–{c['printed_end']} | PDF {c['pdf_start']}–{c['pdf_end']}")
        return
    p = pdf_path(a)
    total = page_count(p)
    if a.command == 'inspect':
        b = BOOKS[a.volume]
        print(f'{b["title"]}: PDF {total} 页；参考文件 {b["pages"]} 页')
        if total != b['pages']:
            print('注意：页数不同，不应直接套用本版本页码索引。')
        text = extract(p, min(20, total), min(20, total))[0]
        print(f'抽样 PDF 第 {min(20, total)} 页可提取非空白字符数：{len("".join(text.split()))}（不代表识别准确率）')
        if a.verify:
            valid = p.stat().st_size == b['bytes'] and digest(p) == b['sha256']
            print('文件校验：' + ('通过' if valid else '不匹配'))
            if not valid:
                raise ValueError('文件与参考版本不一致，请重新核对页码。')
        return
    if a.command in ['read', 'render']:
        if a.book_page is not None and total != BOOKS[a.volume]['pages']:
            raise ValueError('文件页数与参考版本不同，请核对后使用 --page。')
        first, last = bounds(a, total)
        if a.command == 'read':
            for n, text in enumerate(extract(p, first, last), first):
                print(f'\n--- {a.volume} PDF 第 {n} 页（文字层，引用前核对原图）---\n{text}')
        else:
            out = Path(a.out)
            out.parent.mkdir(parents=True, exist_ok=True)
            run('pdftoppm', '-f', first, '-l', last, '-scale-to', 2000, '-png', p, out)
            print(f'已渲染 PDF 第 {first}–{last} 页，文件前缀：{out}')
        return
    if a.limit < 1 or any(not t.strip() for t in a.term):
        raise ValueError('--limit 必须大于 0，关键词不能为空。')
    first, last = 1, total
    if a.chapter is not None:
        c = next((c for c in chapters if c['chapter'] == a.chapter), None)
        if c is None:
            raise ValueError('所选册次没有此章。')
        if total != BOOKS[a.volume]['pages']:
            raise ValueError('文件页数不同，无法安全使用章节索引。')
        first, last = c['pdf_start'], c['pdf_end']
    found = 0
    terms = [t.casefold() for t in a.term]
    for n, text in enumerate(extract(p, first, last), first):
        flat = ''.join(text.split())
        folded = flat.casefold()
        positions = [folded.find(''.join(t.split())) for t in terms]
        positions = [x for x in positions if x >= 0]
        if not positions:
            continue
        pos = min(positions)
        print(f'{a.volume} PDF 第 {n} 页 | …{flat[max(0, pos-70):pos+180]}…')
        found += 1
        if found >= a.limit:
            break
    if not found:
        print('未命中；尝试同义词、英文缩写或直接读取候选章节，文字层可能漏字。')


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError) as error:
        print(f'错误：{error}', file=sys.stderr)
        sys.exit(1)

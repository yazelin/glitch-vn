#!/usr/bin/env python3
"""確認 design/讀音替身表.md 跟 larch/voice.py 的 SUB 沒有走鐘。

文件會落後於程式,而且落後的時候沒有人會發現(2026-08-28 實際發生:
文件寫 38 條、程式已經 66 條)。這支放進去讓它出聲。

跑法:python3 tools/check_subs.py     不一致回非 0
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def code_subs() -> dict:
    body = re.search(r'SUB\s*=\s*\{(.*?)\n\}', (ROOT / 'larch/voice.py').read_text('utf-8'), re.S).group(1)
    return dict(re.findall(r'["\']([^"\']+)["\']\s*:\s*["\']([^"\']+)["\']', body))


def doc_subs() -> dict:
    out = {}
    for line in (ROOT / 'design/讀音替身表.md').read_text('utf-8').splitlines():
        m = re.match(r'\|\s*`([^`]+)`\s*\|\s*`([^`]+)`\s*\|', line)
        if m:
            out[m.group(1)] = m.group(2)
    return out


def main() -> int:
    code, doc = code_subs(), doc_subs()
    missing = [k for k in code if k not in doc]
    extra = [k for k in doc if k not in code]
    diff = [(k, doc[k], code[k]) for k in doc if k in code and doc[k] != code[k]]

    print(f'程式 {len(code)} 條 / 文件 {len(doc)} 列')
    for k in missing:
        print(f'  文件缺: {k} -> {code[k]}')
    for k in extra:
        print(f'  文件多(程式已拿掉): {k}')
    for k, d, c in diff:
        print(f'  對應值不同: {k} 文件={d} 程式={c}')

    bad = len(missing) + len(extra) + len(diff)
    print('一致' if not bad else f'{bad} 處不一致,請更新 design/讀音替身表.md')
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())

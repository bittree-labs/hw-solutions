#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""京东价格探测：搜索 -> 提取 skuId -> p.3.cn 批量取价。临时探测脚本。"""
from curl_cffi import requests as cffi_requests

HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"),
    "Referer": "https://www.jd.com/",
    "Accept": "application/json, text/plain, */*",
}

def jd_search(keyword, n=20):
    url = "https://search.jd.com/Search"
    params = {"keyword": keyword, "enc": "utf-8", "pvid": "", "wq": keyword}
    r = cffi_requests.get(url, params=params, headers=HEADERS,
                          impersonate="chrome124", timeout=30)
    print("search status:", r.status_code, "len:", len(r.text))
    import re
    skus = re.findall(r'data-sku="(\d+)"', r.text)
    # 去重保持顺序
    seen, out = set(), []
    for s in skus:
        if s not in seen:
            seen.add(s); out.append(s)
    return out[:n]

def jd_prices(skus):
    if not skus:
        return []
    url = "https://p.3.cn/prices/mgets"
    params = {"skuIds": ",".join("J_" + s for s in skus)}
    r = cffi_requests.get(url, params=params, headers=HEADERS,
                          impersonate="chrome124", timeout=30)
    print("price status:", r.status_code, "len:", len(r.text))
    try:
        return r.json()
    except Exception as e:
        print("json err:", e, "raw:", r.text[:500])
        return []

if __name__ == "__main__":
    import sys
    kw = sys.argv[1] if len(sys.argv) > 1 else "RTX 4070 显卡"
    skus = jd_search(kw)
    print("skus:", skus)
    prices = jd_prices(skus)
    print("prices:")
    for p in prices[:20]:
        print("  ", p)

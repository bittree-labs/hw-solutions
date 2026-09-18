#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""价格库工具模块：建库、加载清单、写入/查询价格。"""
import json
import os
import sqlite3
import sys
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(ROOT, "db", "prices.db")
SCHEMA_PATH = os.path.join(ROOT, "schema.sql")
WATCHLIST_PATH = os.path.join(ROOT, "config", "watchlist.json")

CHANNELS = ("jd_new", "xianyu_used")


def now_iso():
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def get_conn(db_path=DB_PATH):
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path=DB_PATH):
    conn = get_conn(db_path)
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        conn.executescript(f.read())
    conn.commit()
    return conn


def load_watchlist(path=WATCHLIST_PATH):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["items"]


def sync_watchlist(conn, items):
    """把清单同步进 watchlist 表，返回 name->id 映射。"""
    cur = conn.cursor()
    for it in items:
        cur.execute(
            """INSERT INTO watchlist(name, category, jd_keyword, xianyu_keyword, enabled)
               VALUES(?,?,?,?,1)
               ON CONFLICT(name) DO UPDATE SET
                 category=excluded.category,
                 jd_keyword=excluded.jd_keyword,
                 xianyu_keyword=excluded.xianyu_keyword""",
            (it["name"], it["category"], it.get("jd"), it.get("xianyu")),
        )
    conn.commit()
    rows = conn.execute("SELECT id, name FROM watchlist").fetchall()
    return {r["name"]: r["id"] for r in rows}


def insert_price(conn, item_id, channel, price, price_min=None,
                 price_median=None, price_max=None, sample_count=0,
                 title=None, source_url=None, collected_at=None):
    collected_at = collected_at or now_iso()
    conn.execute(
        """INSERT INTO price_history
           (item_id, channel, price, price_min, price_median, price_max,
            sample_count, title, source_url, collected_at)
           VALUES(?,?,?,?,?,?,?,?,?,?)""",
        (item_id, channel, price, price_min, price_median, price_max,
         sample_count, title, source_url, collected_at),
    )
    conn.commit()


def latest_prices(conn):
    """每个 item × channel 的最新一条价格记录。"""
    return conn.execute(
        """
        SELECT w.name, w.category, w.id AS item_id, p.channel,
               p.price, p.price_min, p.price_median, p.price_max,
               p.sample_count, p.title, p.source_url, p.collected_at
        FROM watchlist w
        JOIN price_history p ON p.item_id = w.id
        JOIN (
            SELECT item_id, channel, MAX(collected_at) AS mx
            FROM price_history GROUP BY item_id, channel
        ) t ON t.item_id = p.item_id AND t.channel = p.channel AND t.collected_at = p.mx
        WHERE w.enabled = 1
        ORDER BY w.category, w.name, p.channel
        """
    ).fetchall()


if __name__ == "__main__":
    conn = init_db()
    items = load_watchlist()
    mapping = sync_watchlist(conn, items)
    print(f"init ok: {len(mapping)} items in watchlist")
    for name, iid in sorted(mapping.items(), key=lambda x: x[1]):
        print(f"  [{iid:2d}] {name}")

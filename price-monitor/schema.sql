-- 硬件行情监控库表
PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS watchlist (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT NOT NULL UNIQUE,
    category        TEXT NOT NULL,
    jd_keyword      TEXT,
    xianyu_keyword  TEXT,
    enabled         INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS price_history (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id       INTEGER NOT NULL,
    channel       TEXT NOT NULL,              -- 'jd_new' | 'xianyu_used'
    price         REAL,                       -- 代表价(元), 默认取中位
    price_min     REAL,
    price_median  REAL,
    price_max     REAL,
    sample_count  INTEGER DEFAULT 0,
    title         TEXT,                       -- 代表商品标题/型号
    source_url    TEXT,
    collected_at  TEXT NOT NULL,              -- ISO8601
    FOREIGN KEY(item_id) REFERENCES watchlist(id)
);

CREATE INDEX IF NOT EXISTS idx_hist_item ON price_history(item_id, channel, collected_at);
CREATE INDEX IF NOT EXISTS idx_hist_time ON price_history(collected_at);

"""
毎日の株価取得スクリプト。
- config/stocks.json の各銘柄について、Yahoo!ファイナンスから日足（終値・出来高）を取得
- data/<コード>.csv に「日付・終値・出来高」で保存（既存分とマージして重複なく追記）

yfinance が取得する日足履歴そのものが「一日ごとに刻まれたデータ」なので、
毎回まとめて取り直し → 既存CSVに統合、という形にしている（欠損・重複に強い）。
GitHub Actions 上で実行される想定。ローカルでも `python scripts/fetch.py` で動く。
"""

import json
import os
import sys

import pandas as pd
import yfinance as yf

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(BASE, "config", "stocks.json")
DATA_DIR = os.path.join(BASE, "data")


def load_config():
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return json.load(f)


def fetch_one(ticker: str, period: str) -> pd.DataFrame:
    """1銘柄の日足を取得して date/close/volume の DataFrame で返す。"""
    df = yf.Ticker(ticker).history(period=period, auto_adjust=False)
    if df is None or df.empty:
        raise RuntimeError(f"{ticker}: データを取得できませんでした")
    out = pd.DataFrame(
        {
            "date": df.index.tz_localize(None).normalize(),
            "close": df["Close"].round(1).values,
            "volume": df["Volume"].astype("int64").values,
        }
    )
    out["date"] = pd.to_datetime(out["date"]).dt.strftime("%Y-%m-%d")
    return out


def merge_save(code: str, fresh: pd.DataFrame) -> int:
    """既存CSVと統合して保存。追加された行数を返す。"""
    path = os.path.join(DATA_DIR, f"{code}.csv")
    if os.path.exists(path):
        old = pd.read_csv(path, dtype={"date": str})
        before = len(old)
        merged = pd.concat([old, fresh], ignore_index=True)
    else:
        before = 0
        merged = fresh
    # 同じ日付は新しい方（fresh）を残す
    merged = merged.drop_duplicates(subset="date", keep="last")
    merged = merged.sort_values("date").reset_index(drop=True)
    os.makedirs(DATA_DIR, exist_ok=True)
    merged.to_csv(path, index=False)
    return len(merged) - before


def main():
    cfg = load_config()
    period = cfg.get("settings", {}).get("history_period", "2y")
    errors = []
    for s in cfg["stocks"]:
        try:
            fresh = fetch_one(s["ticker"], period)
            added = merge_save(s["code"], fresh)
            latest = fresh.iloc[-1]
            print(f"[OK] {s['code']} {s['name']}: "
                  f"最新 {latest['date']} 終値 {latest['close']} / 新規{added}行")
        except Exception as e:  # 1銘柄失敗しても他は続行
            errors.append((s["code"], str(e)))
            print(f"[NG] {s['code']} {s['name']}: {e}", file=sys.stderr)
    if errors:
        # 全滅のときだけ異常終了（一部失敗は許容）
        if len(errors) == len(cfg["stocks"]):
            sys.exit("すべての銘柄で取得に失敗しました")


if __name__ == "__main__":
    main()

"""
グラフ生成スクリプト。
data/<コード>.csv と config/stocks.json を読み、docs/ に成果物を出力する。

出力：
- docs/compare.png        … 3社の値動き比較（基準日=100 に揃えた指数化・note貼付用）
- docs/<コード>.png       … 銘柄ごとの株価＋①様子見／②撤退ライン（note貼付用）
- docs/index.html         … インタラクティブ版ダッシュボード（GitHub Pages公開用）

matplotlib は日本語フォントが無いと文字化けするため、CJKフォントを探して設定する。
GitHub Actions 側で fonts-noto-cjk を入れておくこと（README参照）。
"""

import json
import os
from datetime import datetime, timezone, timedelta

import pandas as pd

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

import plotly.graph_objects as go

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(BASE, "config", "stocks.json")
DATA_DIR = os.path.join(BASE, "data")
DOCS_DIR = os.path.join(BASE, "docs")

COLORS = ["#2563eb", "#dc2626", "#16a34a", "#9333ea", "#ea580c"]
JST = timezone(timedelta(hours=9))


def set_jp_font():
    for name in ["Noto Sans CJK JP", "Noto Sans JP", "IPAexGothic",
                 "TakaoPGothic", "VL PGothic", "Hiragino Sans"]:
        if any(name in f.name for f in fm.fontManager.ttflist):
            plt.rcParams["font.family"] = name
            break
    plt.rcParams["axes.unicode_minus"] = False


def load_config():
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return json.load(f)


def load_series(code):
    path = os.path.join(DATA_DIR, f"{code}.csv")
    if not os.path.exists(path):
        return None
    df = pd.read_csv(path, dtype={"date": str})
    df["date"] = pd.to_datetime(df["date"])
    return df.sort_values("date").reset_index(drop=True)


def today_str():
    return datetime.now(JST).strftime("%Y-%m-%d %H:%M")


# ---------- 比較チャート（指数化・PNG） ----------
def build_compare_png(cfg, series_map, days):
    plt.figure(figsize=(10, 5.5))
    cutoff = pd.Timestamp.now() - pd.Timedelta(days=days)
    for i, s in enumerate(cfg["stocks"]):
        df = series_map.get(s["code"])
        if df is None or df.empty:
            continue
        d = df[df["date"] >= cutoff].copy()
        if d.empty:
            d = df.copy()
        base = d["close"].iloc[0]
        d["idx"] = d["close"] / base * 100
        plt.plot(d["date"], d["idx"], label=f"{s['name']}（{s['code']}）",
                 color=COLORS[i % len(COLORS)], linewidth=2)
    plt.axhline(100, color="#9ca3af", linewidth=1, linestyle="--")
    plt.title(f"半導体3社の値動き比較（基準日=100）  更新 {today_str()}")
    plt.ylabel("指数（基準日を100とした相対値）")
    plt.legend(loc="best")
    plt.grid(alpha=0.3)
    plt.tight_layout()
    out = os.path.join(DOCS_DIR, "compare.png")
    plt.savefig(out, dpi=130)
    plt.close()
    print(f"[OK] {out}")


# ---------- 銘柄別チャート（実価格＋①②ライン・PNG） ----------
def build_stock_png(s, df, days):
    if df is None or df.empty:
        return
    cutoff = pd.Timestamp.now() - pd.Timedelta(days=days)
    d = df[df["date"] >= cutoff].copy()
    if d.empty:
        d = df.copy()
    plt.figure(figsize=(10, 5.0))
    plt.plot(d["date"], d["close"], color="#111827", linewidth=1.8, label="終値")
    watch, exit_ = s.get("watch"), s.get("exit")
    if watch:
        plt.axhline(watch, color="#f59e0b", linewidth=1.6, linestyle="--",
                    label=f"①様子見 {watch:,}円")
    if exit_:
        plt.axhline(exit_, color="#dc2626", linewidth=1.6, linestyle="--",
                    label=f"②撤退 {exit_:,}円")
    last = d.iloc[-1]
    plt.scatter([last["date"]], [last["close"]], color="#111827", zorder=5)
    plt.annotate(f"{last['close']:,.0f}円",
                 (last["date"], last["close"]),
                 textcoords="offset points", xytext=(6, 6), fontsize=9)
    plt.title(f"{s['name']}（{s['code']}）  更新 {today_str()}")
    plt.ylabel("株価（円）")
    plt.legend(loc="best")
    plt.grid(alpha=0.3)
    plt.tight_layout()
    out = os.path.join(DOCS_DIR, f"{s['code']}.png")
    plt.savefig(out, dpi=130)
    plt.close()
    print(f"[OK] {out}")


# ---------- インタラクティブ版（HTML／GitHub Pages） ----------
def fig_compare(cfg, series_map, days):
    fig = go.Figure()
    cutoff = pd.Timestamp.now() - pd.Timedelta(days=days)
    for i, s in enumerate(cfg["stocks"]):
        df = series_map.get(s["code"])
        if df is None or df.empty:
            continue
        d = df[df["date"] >= cutoff].copy()
        if d.empty:
            d = df.copy()
        base = d["close"].iloc[0]
        fig.add_trace(go.Scatter(
            x=d["date"], y=(d["close"] / base * 100).round(2),
            mode="lines", name=f"{s['name']}（{s['code']}）",
            line=dict(color=COLORS[i % len(COLORS)], width=2)))
    fig.add_hline(y=100, line_dash="dash", line_color="#9ca3af")
    fig.update_layout(title="半導体3社の値動き比較（基準日=100）",
                      yaxis_title="指数", template="plotly_white",
                      height=460, legend=dict(orientation="h"))
    return fig


def fig_stock(s, df, days):
    fig = go.Figure()
    cutoff = pd.Timestamp.now() - pd.Timedelta(days=days)
    d = df[df["date"] >= cutoff].copy()
    if d.empty:
        d = df.copy()
    fig.add_trace(go.Scatter(x=d["date"], y=d["close"], mode="lines",
                             name="終値", line=dict(color="#111827", width=2)))
    if s.get("watch"):
        fig.add_hline(y=s["watch"], line_dash="dash", line_color="#f59e0b",
                      annotation_text=f"①様子見 {s['watch']:,}円",
                      annotation_position="right")
    if s.get("exit"):
        fig.add_hline(y=s["exit"], line_dash="dash", line_color="#dc2626",
                      annotation_text=f"②撤退 {s['exit']:,}円",
                      annotation_position="right")
    fig.update_layout(title=f"{s['name']}（{s['code']}）",
                      yaxis_title="株価（円）", template="plotly_white",
                      height=420)
    return fig


def build_html(cfg, series_map, days_compare, days_stock):
    figs = [fig_compare(cfg, series_map, days_compare)]
    for s in cfg["stocks"]:
        df = series_map.get(s["code"])
        if df is not None and not df.empty:
            figs.append(fig_stock(s, df, days_stock))

    divs = []
    for k, fig in enumerate(figs):
        divs.append(fig.to_html(full_html=False,
                                include_plotlyjs=("cdn" if k == 0 else False)))
    charts_html = "\n".join(f'<div class="card">{d}</div>' for d in divs)

    html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>個別株診断ボード ダッシュボード</title>
<style>
  body {{ font-family: system-ui, -apple-system, "Hiragino Sans", "Noto Sans JP", sans-serif;
         margin: 0; background: #f8fafc; color: #111827; }}
  header {{ background: #0f172a; color: #fff; padding: 20px 16px; }}
  header h1 {{ margin: 0; font-size: 20px; }}
  header p {{ margin: 6px 0 0; font-size: 13px; color: #cbd5e1; }}
  main {{ max-width: 900px; margin: 0 auto; padding: 16px; }}
  .card {{ background: #fff; border: 1px solid #e5e7eb; border-radius: 12px;
          padding: 8px; margin: 16px 0; box-shadow: 0 1px 2px rgba(0,0,0,.04); }}
  .note {{ font-size: 12px; color: #6b7280; line-height: 1.7; margin-top: 24px; }}
</style>
</head>
<body>
<header>
  <h1>個別株診断ボード ダッシュボード</h1>
  <p>半導体3社の値動きと①様子見／②撤退ライン ／ 最終更新：{today_str()}（JST）</p>
</header>
<main>
{charts_html}
  <p class="note">
    ※本ダッシュボードはAIの検索および推論に基づく学習用の情報提供であり、投資助言ではありません。
    ①様子見／②撤退ラインは学習用の目安です。投資判断はご自身の責任で行ってください。<br>
    データ提供：Yahoo!ファイナンス（yfinance経由）。表示は終値ベースです。
  </p>
</main>
</body>
</html>"""
    out = os.path.join(DOCS_DIR, "index.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[OK] {out}")


def main():
    set_jp_font()
    os.makedirs(DOCS_DIR, exist_ok=True)
    cfg = load_config()
    days_compare = cfg.get("settings", {}).get("note_compare_days", 180)
    days_stock = max(days_compare, 250)
    series_map = {s["code"]: load_series(s["code"]) for s in cfg["stocks"]}

    build_compare_png(cfg, series_map, days_compare)
    for s in cfg["stocks"]:
        build_stock_png(s, series_map.get(s["code"]), days_stock)
    build_html(cfg, series_map, days_compare, days_stock)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
四半期コスメニュース結合スクリプト
------------------------------------
Claude Codeのルーチンに追加する想定。
毎週末に実行し、四半期末（3/31・6/30・9/30・12/31）に
結合ファイルを ~/cosme_news/quarterly/ に自動保存する。

使い方:
  python3 quarterly_summary.py          # 通常実行（四半期末のみ保存）
  python3 quarterly_summary.py --force  # 強制的に今すぐ結合ファイルを生成
"""

import os
import sys
import glob
from datetime import date, timedelta
from pathlib import Path

NEWS_DIR   = Path.home() / "cosme_news"
OUTPUT_DIR = NEWS_DIR / "quarterly"

# 四半期の定義
QUARTERS = {
    1: ("01-01", "03-31", "Q1"),
    2: ("04-01", "06-30", "Q2"),
    3: ("07-01", "09-30", "Q3"),
    4: ("10-01", "12-31", "Q4"),
}

def get_current_quarter(d: date):
    """日付から四半期番号を返す"""
    month = d.month
    if month <= 3:   return 1
    if month <= 6:   return 2
    if month <= 9:   return 3
    return 4

def is_quarter_end(d: date) -> bool:
    """今日が四半期末かどうか判定"""
    return d in [
        date(d.year, 3, 31),
        date(d.year, 6, 30),
        date(d.year, 9, 30),
        date(d.year, 12, 31),
    ]

def get_quarter_files(year: int, quarter: int) -> list:
    """指定四半期のMarkdownファイル一覧を取得"""
    start_str, end_str, _ = QUARTERS[quarter]
    start = date.fromisoformat(f"{year}-{start_str}")
    end   = date.fromisoformat(f"{year}-{end_str}")

    files = []
    for filepath in sorted(NEWS_DIR.glob("*.md")):
        stem = filepath.stem  # YYYY-MM-DD
        try:
            file_date = date.fromisoformat(stem)
            if start <= file_date <= end:
                files.append(filepath)
        except ValueError:
            continue
    return files

def build_quarterly_file(year: int, quarter: int) -> Path:
    """四半期結合ファイルを生成して返す"""
    _, _, q_label = QUARTERS[quarter]
    files = get_quarter_files(year, quarter)

    if not files:
        print(f"⚠️  {year}-{q_label}: 対象ファイルが見つかりませんでした")
        return None

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / f"{year}-{q_label}.md"

    lines = []
    lines.append(f"# {year}年 {q_label} コスメ・スキンケアニュース 四半期まとめ\n")
    lines.append(f"> 対象期間：{year}-{QUARTERS[quarter][0]} 〜 {year}-{QUARTERS[quarter][1]}\n")
    lines.append(f"> 収録週次レポート数：{len(files)}件\n")
    lines.append("\n---\n")

    for filepath in files:
        lines.append(f"\n## 📅 {filepath.stem}\n")
        lines.append(filepath.read_text(encoding="utf-8"))
        lines.append("\n---\n")

    output_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"✅ 四半期ファイル生成: {output_path}")
    print(f"   収録レポート: {len(files)}件 ({files[0].stem} 〜 {files[-1].stem})")
    return output_path

def push_to_github(filepath: Path):
    """GitHubに四半期ファイルをプッシュ"""
    import subprocess

    github_token = os.environ.get("GITHUB_TOKEN", "")
    github_repo  = os.environ.get("GITHUB_REPO", "https://github.com/AyumiYoda/cosme-news.git")

    if not github_token:
        print("⚠️  GITHUB_TOKEN が未設定のためGitHubへのプッシュをスキップ")
        return

    commands = [
        ["git", "-C", str(NEWS_DIR), "add", str(filepath)],
        ["git", "-C", str(NEWS_DIR), "commit", "-m",
         f"Add quarterly summary: {filepath.name}"],
        ["git", "-C", str(NEWS_DIR), "push", "-u", "origin", "main"],
    ]

    for cmd in commands:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0 and "nothing to commit" not in result.stdout:
            print(f"⚠️  Git コマンド失敗: {' '.join(cmd)}")
            print(result.stderr[:200])
        else:
            print(f"✅ {' '.join(cmd[:3])}")

def main():
    force = "--force" in sys.argv
    today = date.today()
    quarter = get_current_quarter(today)
    year = today.year

    print(f"📅 今日: {today}  ({year}-Q{quarter})")

    if force:
        print("🔧 強制実行モード")
        filepath = build_quarterly_file(year, quarter)
        if filepath:
            push_to_github(filepath)
    elif is_quarter_end(today):
        print(f"📊 四半期末のため結合ファイルを生成します")
        filepath = build_quarterly_file(year, quarter)
        if filepath:
            push_to_github(filepath)
    else:
        # 四半期末でない場合は件数だけ表示
        files = get_quarter_files(year, quarter)
        next_end = date.fromisoformat(f"{year}-{QUARTERS[quarter][1]}")
        days_left = (next_end - today).days
        print(f"📁 今期収録済み: {len(files)}件 / 四半期末まであと{days_left}日")
        print("   （四半期末に自動で結合ファイルを生成します）")
        print("   今すぐ生成したい場合は --force オプションをつけてください")

if __name__ == "__main__":
    main()

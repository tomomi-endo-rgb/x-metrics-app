import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import httpx
import re
import json
from datetime import date
import pandas as pd

# ─── ページ設定 ────────────────────────────────────────────
st.set_page_config(
    page_title="X Metrics",
    page_icon="𝕏",
    layout="wide",
)

st.markdown("""
<style>
[data-testid="stAppViewContainer"] { background: #fafafa; }
.stButton>button { border-radius: 8px; }
</style>
""", unsafe_allow_html=True)

# ─── 認証（簡易パスワード） ────────────────────────────────
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        st.title("𝕏 Metrics")
        st.markdown("スプレッドシートのXポスト数値を自動取得します")
        st.markdown("<br>", unsafe_allow_html=True)
        pw = st.text_input("パスワード", type="password")
        if st.button("ログイン", use_container_width=True, type="primary"):
            if pw == st.secrets.get("APP_PASSWORD", "xmetrics2024"):
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("パスワードが違います")
    st.stop()

# ─── サイドバー ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 𝕏 Metrics")
    st.divider()
    if st.button("🚪 ログアウト", use_container_width=True):
        st.session_state.authenticated = False
        st.rerun()


# ─── ユーティリティ ─────────────────────────────────────────
def col_letter(n: int) -> str:
    s = ""
    while n > 0:
        n, r = divmod(n - 1, 26)
        s = chr(65 + r) + s
    return s


def find_col(headers: list, candidates: list):
    for name in candidates:
        for i, h in enumerate(headers):
            if h.strip() == name:
                return i + 1
    return None


def fetch_x(url: str) -> dict:
    try:
        token = st.secrets.get("TWITTER_BEARER_TOKEN", "")
        if not token:
            return {"再生数": "Token未設定", "いいね": "-", "保存": "-"}
        m = re.search(r"/status/(\d+)", url)
        if not m:
            return {"再生数": "URL不正", "いいね": "-", "保存": "-"}
        resp = httpx.get(
            f"https://api.twitter.com/2/tweets/{m.group(1)}",
            headers={"Authorization": f"Bearer {token}"},
            params={"tweet.fields": "public_metrics"},
            timeout=15,
        )
        if resp.status_code == 200:
            pm = resp.json()["data"]["public_metrics"]
            return {
                "再生数": pm.get("impression_count", "-"),
                "いいね": pm.get("like_count", "-"),
                "保存": pm.get("bookmark_count", "-"),
            }
        return {"再生数": f"API Error {resp.status_code}", "いいね": "-", "保存": "-"}
    except Exception as e:
        return {"再生数": "エラー", "いいね": "エラー", "保存": str(e)[:40]}


# ─── メイン画面 ─────────────────────────────────────────────
st.title("𝕏 Metrics Collector")
st.markdown("スプレッドシートの **XURL** 列を読み取り、数値を取得して書き戻します")
st.divider()

st.subheader("スプレッドシートを入力")
sheet_input = st.text_input(
    "スプレッドシートのURLまたはID",
    placeholder="https://docs.google.com/spreadsheets/d/xxxxxxxx/edit",
)
sheet_index = st.number_input("シート番号（1枚目=1）", min_value=1, value=1) - 1

sheet_id = ""
if sheet_input:
    m = re.search(r"/spreadsheets/d/([a-zA-Z0-9-_]+)", sheet_input)
    sheet_id = m.group(1) if m else sheet_input.strip()

st.markdown("<br>", unsafe_allow_html=True)
run = st.button("▶ 取得開始", disabled=not sheet_id, type="primary")

if run:
    try:
        with st.spinner("シートに接続中..."):
            creds_raw = st.secrets["GCP_SERVICE_ACCOUNT"]
            creds_info = json.loads(creds_raw) if isinstance(creds_raw, str) else dict(creds_raw)
            creds = Credentials.from_service_account_info(
                creds_info,
                scopes=["https://www.googleapis.com/auth/spreadsheets",
                        "https://www.googleapis.com/auth/drive.readonly"],
            )
            gc = gspread.authorize(creds)
            ws = gc.open_by_key(sheet_id).get_worksheet(sheet_index)

        # ヘッダー行を自動検出（最初の10行からXURLを探す）
        all_rows = ws.get_all_values()
        header_row_idx = None
        headers = []
        for i, row in enumerate(all_rows[:10]):
            if any("XURL" in str(cell) or "xurl" in str(cell).lower() for cell in row):
                header_row_idx = i
                headers = row
                break

        if header_row_idx is None:
            st.error("❌ 「XURL」列が見つかりません。ヘッダー行に「XURL」が含まれているか確認してください")
            st.stop()

        url_col  = find_col(headers, ["XURL", "X URL", "xurl"])
        imp_col  = find_col(headers, ["XImp", "X Imp", "Ximp", "X再生数", "Xlmp"])
        like_col = find_col(headers, ["Xいいね", "X いいね", "xlike"])
        save_col = find_col(headers, ["X保存", "X 保存", "xbookmark", "XBM", "xbm"])

        if not url_col:
            st.error("❌ 「XURL」列が見つかりません")
            st.write("検出されたヘッダー:", headers)
            st.stop()

        col_map = {
            "XURL": col_letter(url_col),
            "XImp": col_letter(imp_col) if imp_col else "（なし）",
            "Xいいね": col_letter(like_col) if like_col else "（なし）",
            "X保存": col_letter(save_col) if save_col else "（なし）",
        }
        st.success("✅ シート接続完了")
        st.info("  |  ".join(f"**{k}** → {v}列" for k, v in col_map.items()))

        url_rows = [
            (header_row_idx + i + 2, row[url_col - 1].strip())
            for i, row in enumerate(all_rows[header_row_idx + 1:])
            if len(row) >= url_col and row[url_col - 1].strip()
        ]

        if not url_rows:
            st.warning("URLが見つかりませんでした")
            st.stop()

        st.info(f"📋 {len(url_rows)} 件のURLを検出")
        progress = st.progress(0)
        status = st.empty()
        results = []

        for idx, (row_num, url) in enumerate(url_rows):
            status.markdown(f"⏳ `{idx + 1}/{len(url_rows)}` 取得中…  `{url[:70]}`")
            metrics = fetch_x(url)
            results.append({"行": row_num, "URL": url, **metrics})

            updates = []
            if imp_col:
                updates.append({"range": f"{col_letter(imp_col)}{row_num}", "values": [[metrics["再生数"]]]})
            if like_col:
                updates.append({"range": f"{col_letter(like_col)}{row_num}", "values": [[metrics["いいね"]]]})
            if save_col:
                updates.append({"range": f"{col_letter(save_col)}{row_num}", "values": [[metrics["保存"]]]})
            if updates:
                ws.batch_update(updates)

            progress.progress((idx + 1) / len(url_rows))

        status.empty()
        st.balloons()
        st.success(f"🎉 完了！ {len(url_rows)} 件をシートに書き込みました（{date.today()}）")
        df = pd.DataFrame(results)
        st.dataframe(df, use_container_width=True, hide_index=True)

    except gspread.exceptions.SpreadsheetNotFound:
        st.error("スプレッドシートが見つかりません。フォルダの共有設定を確認してください")
    except KeyError as e:
        st.error(f"シークレット設定エラー: {e}")
    except Exception as e:
        st.error(f"エラー: {e}")

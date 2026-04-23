import streamlit as st
import gspread
from google.oauth2.credentials import Credentials
import httpx
import re
import json
from datetime import date
import pandas as pd
from urllib.parse import urlencode

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

# ─── OAuth設定 ─────────────────────────────────────────────
REDIRECT_URI = "https://x-metrics-app.streamlit.app/"
SCOPES = " ".join([
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/spreadsheets",
])


def get_auth_url() -> str:
    params = {
        "client_id": st.secrets["GOOGLE_CLIENT_ID"],
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": SCOPES,
        "access_type": "offline",
        "prompt": "select_account",
    }
    return f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"


def exchange_code(code: str) -> dict:
    resp = httpx.post(
        "https://oauth2.googleapis.com/token",
        data={
            "code": code,
            "client_id": st.secrets["GOOGLE_CLIENT_ID"],
            "client_secret": st.secrets["GOOGLE_CLIENT_SECRET"],
            "redirect_uri": REDIRECT_URI,
            "grant_type": "authorization_code",
        },
        timeout=15,
    )
    return resp.json()


def get_user_info(access_token: str) -> dict:
    resp = httpx.get(
        "https://www.googleapis.com/oauth2/v3/userinfo",
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=10,
    )
    return resp.json()


# ─── OAuthコールバック処理 ─────────────────────────────────
params = st.query_params
if "code" in params and "oauth_token" not in st.session_state:
    with st.spinner("ログイン処理中..."):
        token_data = exchange_code(params["code"])
        if "access_token" in token_data:
            user_info = get_user_info(token_data["access_token"])
            st.session_state.oauth_token = token_data
            st.session_state.user_info = user_info
            st.query_params.clear()
            st.rerun()
        else:
            st.error(f"ログインエラー: {token_data.get('error_description', token_data)}")
            st.stop()

# ─── 認証チェック ──────────────────────────────────────────
if "oauth_token" not in st.session_state:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        st.title("𝕏 Metrics")
        st.markdown("スプレッドシートのXポスト数値を自動取得します")
        st.markdown("<br>", unsafe_allow_html=True)
        auth_url = get_auth_url()
        st.markdown(
            f'<a href="{auth_url}" target="_self">'
            f'<button style="background:#000;color:#fff;border:none;padding:12px 24px;'
            f'border-radius:8px;font-size:16px;cursor:pointer;width:100%">'
            f'🔑 Googleでログイン</button></a>',
            unsafe_allow_html=True,
        )
    st.stop()

# ─── ログイン済み ──────────────────────────────────────────
user_info = st.session_state.user_info
token_data = st.session_state.oauth_token

# ─── サイドバー ─────────────────────────────────────────────
with st.sidebar:
    pic = user_info.get("picture", "")
    if pic:
        st.image(pic, width=48)
    st.markdown(f"**{user_info.get('name', '')}**")
    st.caption(user_info.get("email", ""))
    st.divider()
    if st.button("🚪 ログアウト", use_container_width=True):
        del st.session_state.oauth_token
        del st.session_state.user_info
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
            creds = Credentials(
                token=token_data["access_token"],
                refresh_token=token_data.get("refresh_token"),
                token_uri="https://oauth2.googleapis.com/token",
                client_id=st.secrets["GOOGLE_CLIENT_ID"],
                client_secret=st.secrets["GOOGLE_CLIENT_SECRET"],
                scopes=["https://www.googleapis.com/auth/spreadsheets"],
            )
            gc = gspread.authorize(creds)
            ws = gc.open_by_key(sheet_id).get_worksheet(sheet_index)
            headers = ws.row_values(1)

        url_col  = find_col(headers, ["XURL", "X URL", "xurl"])
        imp_col  = find_col(headers, ["XImp", "X Imp", "Ximp", "X再生数"])
        like_col = find_col(headers, ["Xいいね", "X いいね", "xlike"])
        save_col = find_col(headers, ["X保存", "X 保存", "xbookmark"])

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

        all_rows = ws.get_all_values()
        url_rows = [
            (i + 2, row[url_col - 1].strip())
            for i, row in enumerate(all_rows[1:])
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
        st.error("スプレッドシートが見つかりません。URLを確認してください")
    except Exception as e:
        st.error(f"エラー: {e}")

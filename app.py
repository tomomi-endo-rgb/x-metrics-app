import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import httpx
import re
import json
import math
import time
import traceback
from datetime import date, datetime
import pandas as pd

# ─── ページ設定 ────────────────────────────────────────────
st.set_page_config(
    page_title="X Metrics",
    page_icon="𝕏",
    layout="wide",
    menu_items={"Get Help": None, "Report a bug": None, "About": None},
)

# ─── グローバルCSS ─────────────────────────────────────────
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@20..24,300..500,0..1,-25..0&display=swap" rel="stylesheet">
<style>
/* Material Symbols スタイル */
.material-symbols-rounded {
    font-family: 'Material Symbols Rounded';
    font-weight: normal;
    font-style: normal;
    font-size: inherit;
    line-height: 1;
    letter-spacing: normal;
    text-transform: none;
    display: inline-block;
    white-space: nowrap;
    word-wrap: normal;
    direction: ltr;
    -webkit-font-feature-settings: 'liga';
    -webkit-font-smoothing: antialiased;
    vertical-align: -0.15em;
    font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24;
}

/* 上部の右側ボタン群だけ非表示（サイドバー開閉ボタンは残す） */
[data-testid="stToolbarActions"] { display: none !important; }
[data-testid="stMainMenu"] { display: none !important; }
[data-testid="stStatusWidget"] { display: none !important; }
[data-testid="stDeployButton"] { display: none !important; }
[data-testid="stDecoration"] { display: none !important; }
.stDeployButton, .stAppDeployButton { display: none !important; }
header[data-testid="stHeader"] { background: transparent !important; }
#MainMenu { visibility: hidden !important; }
footer { visibility: hidden !important; }

/* サイドバー閉じてる時の開くボタンを必ず表示 */
[data-testid="collapsedControl"], [data-testid="stSidebarCollapsedControl"] {
    display: block !important;
    visibility: visible !important;
}

/* 全体背景 */
[data-testid="stAppViewContainer"] {
    background: #f7f7f7;
}

/* サイドバー背景 */
section[data-testid="stSidebar"] {
    background: #111111 !important;
    min-width: 230px !important;
    max-width: 230px !important;
}
section[data-testid="stSidebar"] > div {
    background: #111111 !important;
    padding-top: 1.5rem;
}

/* サイドバー内の通常テキスト（ボタン以外） */
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] div,
section[data-testid="stSidebar"] label {
    color: #ffffff !important;
}

/* サイドバーのボタンコンテナ */
section[data-testid="stSidebar"] div[data-testid="stButton"] > button,
section[data-testid="stSidebar"] button[data-testid="baseButton-secondary"],
section[data-testid="stSidebar"] button[data-testid="baseButton-primary"],
section[data-testid="stSidebar"] .stButton > button {
    width: 100% !important;
    text-align: left !important;
    background-color: transparent !important;
    background: transparent !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 0.55rem 0.9rem !important;
    font-size: 0.88rem !important;
    color: #cccccc !important;
    font-weight: 400 !important;
    box-shadow: none !important;
    justify-content: flex-start !important;
    display: flex !important;
    align-items: center !important;
    gap: 0.6rem !important;
    letter-spacing: 0.02em !important;
}

/* サイドバーのボタン内のテキスト */
section[data-testid="stSidebar"] .stButton > button p,
section[data-testid="stSidebar"] .stButton > button span,
section[data-testid="stSidebar"] .stButton > button div {
    color: #cccccc !important;
    text-align: left !important;
    width: 100% !important;
}

/* Material アイコンのスタイル */
section[data-testid="stSidebar"] .stButton > button .material-symbols-rounded,
section[data-testid="stSidebar"] .stButton > button [class*="material-symbols"] {
    font-size: 1.1rem !important;
    color: inherit !important;
    margin-right: 0.2rem !important;
}

/* hover状態 */
section[data-testid="stSidebar"] .stButton > button:hover {
    background-color: rgba(255,255,255,0.08) !important;
    background: rgba(255,255,255,0.08) !important;
    color: #ffffff !important;
    border: none !important;
}
section[data-testid="stSidebar"] .stButton > button:hover p,
section[data-testid="stSidebar"] .stButton > button:hover span,
section[data-testid="stSidebar"] .stButton > button:hover div {
    color: #ffffff !important;
}

/* アクティブ（primary）状態 */
section[data-testid="stSidebar"] .stButton > button[kind="primary"] {
    background-color: rgba(255,255,255,0.15) !important;
    background: rgba(255,255,255,0.15) !important;
    color: #ffffff !important;
    font-weight: 600 !important;
    border: none !important;
}
section[data-testid="stSidebar"] .stButton > button[kind="primary"] p,
section[data-testid="stSidebar"] .stButton > button[kind="primary"] span,
section[data-testid="stSidebar"] .stButton > button[kind="primary"] div {
    color: #ffffff !important;
    font-weight: 600 !important;
}

/* focus時のアウトラインを消す */
section[data-testid="stSidebar"] .stButton > button:focus,
section[data-testid="stSidebar"] .stButton > button:active {
    outline: none !important;
    box-shadow: none !important;
    border: none !important;
}

/* メインエリアのカード */
.metric-card {
    background: white;
    border-radius: 12px;
    padding: 1.5rem;
    box-shadow: 0 1px 4px rgba(0,0,0,0.08);
    margin-bottom: 1rem;
}

/* ページタイトル */
.page-title {
    font-size: 1.5rem;
    font-weight: 700;
    color: #111111;
    margin-bottom: 0.3rem;
}
.page-subtitle {
    font-size: 0.9rem;
    color: #888888;
    margin-bottom: 1.5rem;
}

/* プライマリボタン */
.stButton > button[kind="primary"] {
    background: #111111 !important;
    color: white !important;
    border-radius: 8px !important;
    border: none !important;
}
.stButton > button[kind="primary"]:hover {
    background: #333333 !important;
}

/* テキストインプット */
.stTextInput > div > div > input {
    border-radius: 8px !important;
    border: 1.5px solid #e0e0e0 !important;
}

/* ステップバッジ */
.step-badge {
    display: inline-block;
    background: #111111;
    color: white;
    border-radius: 50%;
    width: 24px;
    height: 24px;
    text-align: center;
    line-height: 24px;
    font-size: 0.75rem;
    font-weight: 700;
    margin-right: 8px;
}

/* 区切り線 */
hr { border: none; border-top: 1px solid #eeeeee; margin: 1rem 0; }

/* ログイン画面 */
.login-box {
    background: white;
    border-radius: 16px;
    padding: 2.5rem;
    box-shadow: 0 2px 16px rgba(0,0,0,0.08);
    max-width: 420px;
    margin: 0 auto;
}
</style>
""", unsafe_allow_html=True)


# ─── 認証（簡易パスワード） ────────────────────────────────
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.markdown("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("""
        <div class="login-box">
            <div style="text-align:center; margin-bottom:1.5rem;">
                <div style="font-size:2.5rem;">𝕏</div>
                <div style="font-size:1.4rem; font-weight:700; color:#111;">X Metrics</div>
                <div style="font-size:0.85rem; color:#888; margin-top:0.3rem;">Xポスト数値 自動取得ツール</div>
            </div>
        """, unsafe_allow_html=True)
        pw = st.text_input("パスワード", type="password", placeholder="パスワードを入力")
        if st.button("ログイン", use_container_width=True, type="primary"):
            if pw == st.secrets.get("APP_PASSWORD", "xmetrics2024"):
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("パスワードが違います")
        st.markdown("</div>", unsafe_allow_html=True)
    st.stop()


# ─── セッション（ページ管理） ──────────────────────────────
if "page" not in st.session_state:
    st.session_state.page = "fetch"


# ─── サイドバーナビゲーション ───────────────────────────────
with st.sidebar:
    # ロゴ
    st.markdown("""
    <div style="padding: 0 1rem 1.5rem 1rem;">
        <div style="font-size:1.5rem; font-weight:800; letter-spacing:-0.5px;">𝕏 Metrics</div>
        <div style="font-size:0.72rem; color:#666; margin-top:2px;">Xポスト数値 自動取得ツール</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='border-top:1px solid #333; margin:0 -1rem 1rem -1rem;'></div>", unsafe_allow_html=True)

    # ナビゲーション定義（Material Icons）
    nav_items = [
        ("fetch",    ":material/query_stats:", "数値を取得する"),
        ("sheets",   ":material/folder:",      "対象シート管理"),
        ("logs",     ":material/history:",     "実行ログ"),
        ("howto",    ":material/help_outline:","使い方"),
        ("settings", ":material/settings:",    "設定・シート共有"),
    ]

    for key, icon, label in nav_items:
        btn_type = "primary" if st.session_state.page == key else "secondary"
        if st.button(
            f"{icon} {label}",
            key=f"nav_{key}",
            use_container_width=True,
            type=btn_type,
        ):
            st.session_state.page = key
            st.rerun()

    # 下部：ログアウト
    st.markdown("<div style='position:fixed; bottom:2rem; width:186px;'>", unsafe_allow_html=True)
    st.markdown("<div style='border-top:1px solid #333; margin-bottom:0.8rem;'></div>", unsafe_allow_html=True)
    if st.button(":material/logout: ログアウト", use_container_width=True):
        st.session_state.authenticated = False
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)


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


SHEETS_TAB = "_登録シート"
LOGS_TAB = "_実行ログ"
SHEETS_HEADERS = ["シートID", "表示名", "登録日"]
LOGS_HEADERS = ["ID", "実行時刻", "シート名", "シートID", "種別", "件数", "成功", "失敗", "所要時間", "ステータス", "URL一覧"]
MANAGER_SHEET_NAME = "X Metrics Manager (Auto)"


def get_gspread_client():
    """gspreadクライアントを取得"""
    creds_raw = st.secrets["GCP_SERVICE_ACCOUNT"]
    creds_info = json.loads(creds_raw) if isinstance(creds_raw, str) else dict(creds_raw)
    creds = Credentials.from_service_account_info(
        creds_info,
        scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive.file",
        ],
    )
    return gspread.authorize(creds)


def get_manager_workbook():
    """管理用スプレッドシートを取得（自動作成済み or 設定済み）"""
    # 1. Secretsで指定されていればそれを使う（フォールバック手動設定）
    sheet_id = st.secrets.get("MANAGER_SHEET_ID", "")
    if sheet_id:
        try:
            gc = get_gspread_client()
            return gc.open_by_key(sheet_id)
        except Exception as e:
            st.session_state["_manager_error"] = f"指定IDでのオープン失敗: {type(e).__name__}: {str(e)[:200]}"
            return None

    # 2. 自動取得を試みる
    try:
        gc = get_gspread_client()
        try:
            wb = gc.open(MANAGER_SHEET_NAME)
            st.session_state.pop("_manager_error", None)
            return wb
        except gspread.exceptions.SpreadsheetNotFound:
            try:
                wb = gc.create(MANAGER_SHEET_NAME)
                st.session_state.pop("_manager_error", None)
                return wb
            except Exception as e:
                st.session_state["_manager_error"] = f"作成失敗: {type(e).__name__}: {str(e)[:300]}"
                return None
    except Exception as e:
        st.session_state["_manager_error"] = f"接続失敗: {type(e).__name__}: {str(e)[:300]}"
        return None


def ensure_manager_tabs(workbook):
    """管理用シートに必要なタブを確保"""
    sheets_ws = None
    logs_ws = None
    try:
        sheets_ws = workbook.worksheet(SHEETS_TAB)
    except gspread.exceptions.WorksheetNotFound:
        sheets_ws = workbook.add_worksheet(title=SHEETS_TAB, rows=200, cols=5)
        sheets_ws.append_row(SHEETS_HEADERS)
        try:
            sheets_ws.format("A1:C1", {"textFormat": {"bold": True}})
        except Exception:
            pass

    try:
        logs_ws = workbook.worksheet(LOGS_TAB)
    except gspread.exceptions.WorksheetNotFound:
        logs_ws = workbook.add_worksheet(title=LOGS_TAB, rows=2000, cols=15)
        logs_ws.append_row(LOGS_HEADERS)
        try:
            logs_ws.format("A1:K1", {"textFormat": {"bold": True}})
        except Exception:
            pass

    return sheets_ws, logs_ws


def get_registered_sheets():
    """登録済みシート一覧を取得"""
    wb = get_manager_workbook()
    if not wb:
        return []
    try:
        sheets_ws, _ = ensure_manager_tabs(wb)
        return sheets_ws.get_all_records()
    except Exception:
        return []


def add_registered_sheet(sheet_id: str, display_name: str) -> bool:
    """シートを登録"""
    wb = get_manager_workbook()
    if not wb:
        return False
    try:
        sheets_ws, _ = ensure_manager_tabs(wb)
        # 重複チェック
        existing = sheets_ws.get_all_records()
        for r in existing:
            if r.get("シートID") == sheet_id:
                return False
        sheets_ws.append_row([sheet_id, display_name, datetime.now().strftime("%Y/%m/%d")])
        return True
    except Exception:
        return False


def remove_registered_sheet(sheet_id: str) -> bool:
    """シートを登録解除"""
    wb = get_manager_workbook()
    if not wb:
        return False
    try:
        sheets_ws, _ = ensure_manager_tabs(wb)
        records = sheets_ws.get_all_records()
        for i, r in enumerate(records, start=2):
            if r.get("シートID") == sheet_id:
                sheets_ws.delete_rows(i)
                return True
        return False
    except Exception:
        return False


def append_log_to_manager(log_data: dict):
    """実行ログを管理シートに追記"""
    wb = get_manager_workbook()
    if not wb:
        return
    try:
        _, logs_ws = ensure_manager_tabs(wb)
        logs_ws.append_row([
            log_data.get("id", ""),
            log_data.get("timestamp", ""),
            log_data.get("sheet_name", ""),
            log_data.get("sheet_id", ""),
            log_data.get("type", "手動"),
            log_data.get("total", 0),
            log_data.get("success", 0),
            log_data.get("fail", 0),
            log_data.get("duration", ""),
            log_data.get("status", ""),
            log_data.get("urls", ""),
        ])
    except Exception as e:
        print(f"Log append failed: {e}")


def get_all_logs():
    """全実行ログを取得"""
    wb = get_manager_workbook()
    if not wb:
        return []
    try:
        _, logs_ws = ensure_manager_tabs(wb)
        return logs_ws.get_all_records()
    except Exception:
        return []


def format_duration(seconds: float) -> str:
    """秒数を「1分23秒」のような形式に"""
    seconds = int(seconds)
    if seconds < 60:
        return f"{seconds}秒"
    m, s = divmod(seconds, 60)
    if m < 60:
        return f"{m}分{s}秒"
    h, m = divmod(m, 60)
    return f"{h}時間{m}分{s}秒"


def is_success_value(val) -> bool:
    """取得結果が成功値かどうか判定"""
    if val is None:
        return False
    s = str(val).strip()
    if s in ("-", "", "0"):
        return False
    error_keywords = ["エラー", "取得失敗", "削除済み", "URL不正", "Token未設定", "API Error"]
    return not any(k in s for k in error_keywords)


# X (Twitter) Web Clientが内部で使う公開Bearer Token
PUBLIC_BEARER = (
    "AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs"
    "%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA"
)

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)


@st.cache_data(ttl=600, show_spinner=False)
def _get_guest_token() -> str:
    """ゲストトークンを取得（10分キャッシュ）"""
    try:
        resp = httpx.post(
            "https://api.x.com/1.1/guest/activate.json",
            headers={
                "Authorization": f"Bearer {PUBLIC_BEARER}",
                "User-Agent": UA,
            },
            timeout=10,
        )
        if resp.status_code == 200:
            return resp.json().get("guest_token", "")
    except Exception:
        pass
    return ""


def _syndication_token(tweet_id: str) -> str:
    """Syndication API用のtokenを生成（フォールバック用）"""
    n = (int(tweet_id) / 1e15) * math.pi
    chars = "0123456789abcdefghijklmnopqrstuvwxyz"
    int_part = int(n)
    int_str = ""
    if int_part == 0:
        int_str = "0"
    else:
        while int_part > 0:
            int_part, r = divmod(int_part, 36)
            int_str = chars[r] + int_str
    frac = n - int(n)
    frac_str = ""
    for _ in range(15):
        frac *= 36
        digit = int(frac)
        frac_str += chars[digit]
        frac -= digit
        if frac == 0:
            break
    full = int_str + ("." + frac_str if frac_str else "")
    return re.sub(r"(0+|\.)", "", full)


def _fetch_via_graphql(tweet_id: str):
    """GraphQL APIで取得（再生数・いいね・保存すべて取れる可能性）"""
    guest_token = _get_guest_token()
    if not guest_token:
        return None, None

    variables = {
        "tweetId": tweet_id,
        "withCommunity": False,
        "includePromotedContent": False,
        "withVoice": False,
    }
    features = {
        "creator_subscriptions_tweet_preview_api_enabled": True,
        "communities_web_enable_tweet_community_results_fetch": True,
        "c9s_tweet_anatomy_moderator_badge_enabled": True,
        "articles_preview_enabled": True,
        "tweetypie_unmention_optimization_enabled": True,
        "responsive_web_edit_tweet_api_enabled": True,
        "graphql_is_translatable_rweb_tweet_is_translatable_enabled": True,
        "view_counts_everywhere_api_enabled": True,
        "longform_notetweets_consumption_enabled": True,
        "responsive_web_twitter_article_tweet_consumption_enabled": True,
        "tweet_awards_web_tipping_enabled": False,
        "creator_subscriptions_quote_tweet_preview_enabled": False,
        "freedom_of_speech_not_reach_fetch_enabled": True,
        "standardized_nudges_misinfo": True,
        "tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled": True,
        "rweb_video_timestamps_enabled": True,
        "longform_notetweets_rich_text_read_enabled": True,
        "longform_notetweets_inline_media_enabled": True,
        "responsive_web_graphql_exclude_directive_enabled": True,
        "verified_phone_label_enabled": False,
        "responsive_web_graphql_skip_user_profile_image_extensions_enabled": False,
        "responsive_web_graphql_timeline_navigation_enabled": True,
        "responsive_web_enhance_cards_enabled": False,
        "rweb_tipjar_consumption_enabled": True,
        "profile_label_improvements_pcf_label_in_post_enabled": False,
    }
    field_toggles = {"withArticleRichContentState": False, "withAuxiliaryUserLabels": False}

    # 複数のクエリIDを試す（X側で変わるため）
    query_ids = [
        "0hWvDhmW8YQ-S_ib3azIrw",
        "2ICDjqPd81tulZcYrtpTuQ",
        "8mPfHBetXXg2bDIDUjWAGw",
        "yV3UMNEaezEcVGGJ4DuYAA",
    ]

    for qid in query_ids:
        try:
            resp = httpx.get(
                f"https://api.x.com/graphql/{qid}/TweetResultByRestId",
                params={
                    "variables": json.dumps(variables),
                    "features": json.dumps(features),
                    "fieldToggles": json.dumps(field_toggles),
                },
                headers={
                    "Authorization": f"Bearer {PUBLIC_BEARER}",
                    "x-guest-token": guest_token,
                    "User-Agent": UA,
                    "Referer": "https://x.com/",
                    "Origin": "https://x.com",
                    "x-twitter-active-user": "yes",
                    "x-twitter-client-language": "ja",
                    "Accept": "*/*",
                    "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
                },
                timeout=15,
                follow_redirects=True,
            )

            if resp.status_code == 200:
                data = resp.json()
                tweet_result = data.get("data", {}).get("tweetResult", {})
                tweet = tweet_result.get("result", {}) if isinstance(tweet_result, dict) else {}

                # __typename が TweetTombstone の場合はNG
                if tweet.get("__typename") == "TweetTombstone":
                    return None, data

                legacy = tweet.get("legacy", {})
                views = tweet.get("views", {})

                view_count = "-"
                if isinstance(views, dict):
                    view_count = views.get("count", "-") or "-"

                result = {
                    "再生数": view_count,
                    "いいね": legacy.get("favorite_count", "-"),
                    "保存": legacy.get("bookmark_count", "-"),
                }
                return result, data
        except Exception:
            continue

    return None, None


def _fetch_via_syndication(tweet_id: str):
    """Syndication API（フォールバック）"""
    try:
        token = _syndication_token(tweet_id)
        resp = httpx.get(
            "https://cdn.syndication.twimg.com/tweet-result",
            params={"id": tweet_id, "token": token, "lang": "ja"},
            headers={
                "User-Agent": UA,
                "Accept": "application/json",
                "Referer": "https://platform.twitter.com/",
            },
            timeout=15,
            follow_redirects=True,
        )
        if resp.status_code == 200:
            data = resp.json()
            return {
                "再生数": "-",
                "いいね": data.get("favorite_count", "-"),
                "保存": "-",
            }, data
        elif resp.status_code == 404:
            return {"再生数": "削除済み", "いいね": "-", "保存": "-"}, None
    except Exception:
        pass
    return None, None


def fetch_x(url: str, return_raw: bool = False):
    """X(Twitter)の数値を取得（裏API → Syndicationの順にフォールバック）"""
    try:
        m = re.search(r"/status/(\d+)", url)
        if not m:
            result = {"再生数": "URL不正", "いいね": "-", "保存": "-"}
            return (result, None) if return_raw else result
        tweet_id = m.group(1)

        # 1. GraphQL API（裏API）で取得を試みる
        result, raw = _fetch_via_graphql(tweet_id)
        if result and result.get("いいね") not in ("-", None):
            return (result, raw) if return_raw else result

        # 2. フォールバック: Syndication API（いいねだけ取れる）
        result2, raw2 = _fetch_via_syndication(tweet_id)
        if result2:
            return (result2, raw2) if return_raw else result2

        result = {"再生数": "取得失敗", "いいね": "-", "保存": "-"}
        return (result, None) if return_raw else result
    except Exception as e:
        result = {"再生数": "エラー", "いいね": "-", "保存": str(e)[:40]}
        return (result, None) if return_raw else result


# ═══════════════════════════════════════════════════════════
# ページ：数値を取得する
# ═══════════════════════════════════════════════════════════
if st.session_state.page == "fetch":
    st.markdown('<div class="page-title"><span class="material-symbols-rounded" style="vertical-align:-4px;font-size:1.6rem;margin-right:6px;">query_stats</span>数値を取得する</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">登録済みシートを選んで、Xポストの数値を一括取得します</div>', unsafe_allow_html=True)

    with st.container(border=True):
        registered = get_registered_sheets()

        sheet_id = ""
        sheet_index = 0

        if registered:
            # 登録済みシートからドロップダウン選択
            options = ["-- シートを選択 --"] + [f"{r.get('表示名', r.get('シートID', ''))}" for r in registered]
            selected = st.selectbox("対象シート", options, key="fetch_sheet_select")
            if selected != "-- シートを選択 --":
                idx = options.index(selected) - 1
                sheet_id = registered[idx]["シートID"]

            with st.expander("➕ 新しいシートで取得（登録せず一回だけ）"):
                sheet_input = st.text_input(
                    "スプレッドシートのURLまたはID",
                    placeholder="https://docs.google.com/spreadsheets/d/xxxxxxxx/edit",
                    key="fetch_url_input",
                )
                if sheet_input:
                    m = re.search(r"/spreadsheets/d/([a-zA-Z0-9-_]+)", sheet_input)
                    sheet_id = m.group(1) if m else sheet_input.strip()
        else:
            # 登録なし → URL直接入力
            st.info("💡 「📂 対象シート管理」で登録するとドロップダウンから選べます")
            sheet_input = st.text_input(
                "スプレッドシートのURLまたはID",
                placeholder="https://docs.google.com/spreadsheets/d/xxxxxxxx/edit",
            )
            if sheet_input:
                m = re.search(r"/spreadsheets/d/([a-zA-Z0-9-_]+)", sheet_input)
                sheet_id = m.group(1) if m else sheet_input.strip()

        sheet_index = st.number_input("シート番号（1枚目=1）", min_value=1, value=1) - 1

        st.markdown("<br>", unsafe_allow_html=True)
        run = st.button("▶ 取得開始", disabled=not sheet_id, type="primary", use_container_width=False)

    if run:
        # 後でログページから参照できるよう保存
        st.session_state.last_sheet_id = sheet_id
        try:
            run_start = time.time()
            with st.spinner("シートに接続中..."):
                gc = get_gspread_client()
                workbook = gc.open_by_key(sheet_id)
                ws = workbook.get_worksheet(sheet_index)
                sheet_title = workbook.title

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

            # 列マッピング表示
            col_map = {
                "XURL": col_letter(url_col),
                "XImp": col_letter(imp_col) if imp_col else "（なし）",
                "Xいいね": col_letter(like_col) if like_col else "（なし）",
                "X保存": col_letter(save_col) if save_col else "（なし）",
            }

            with st.container(border=True):
                st.success("✅ シート接続完了")
                cols = st.columns(4)
                for i, (k, v) in enumerate(col_map.items()):
                    with cols[i]:
                        st.metric(label=k, value=f"{v}列")

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
            duration = time.time() - run_start

            # 成功/失敗カウント
            total = len(results)
            success = sum(1 for r in results if is_success_value(r.get("いいね")))
            fail = total - success
            if fail == 0:
                final_status = "成功"
            elif success == 0:
                final_status = "失敗"
            else:
                final_status = "一部失敗"

            # 実行ログを管理シートに保存
            log_id = datetime.now().strftime("#%y%m%d%H%M%S")
            urls_summary = " / ".join(r.get("URL", "") for r in results)
            append_log_to_manager({
                "id": log_id,
                "timestamp": datetime.now().strftime("%Y/%m/%d %H:%M:%S"),
                "sheet_name": sheet_title,
                "sheet_id": sheet_id,
                "type": "手動",
                "total": total,
                "success": success,
                "fail": fail,
                "duration": format_duration(duration),
                "status": final_status,
                "urls": urls_summary,
            })

            with st.container(border=True):
                msg = f"完了 ・ {success}/{total} 件成功"
                if fail > 0:
                    msg += f"（{fail} 件失敗）"
                msg += f" ・ 所要時間: {format_duration(duration)}"
                if final_status == "成功":
                    st.success(msg)
                elif final_status == "一部失敗":
                    st.warning(msg)
                else:
                    st.error(msg)

                df = pd.DataFrame(results)

                # ステータス列を追加
                def _row_status(r):
                    return "成功" if is_success_value(r.get("いいね")) else "失敗"
                df.insert(0, "状態", df.apply(_row_status, axis=1))

                # 失敗行を赤くハイライト
                def _highlight(row):
                    if row["状態"] == "失敗":
                        return ["background-color: #fff5f5; color: #c92a2a"] * len(row)
                    return [""] * len(row)

                styled = df.style.apply(_highlight, axis=1)
                st.dataframe(
                    styled,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "状態": st.column_config.TextColumn("状態", width="small"),
                        "行": st.column_config.NumberColumn("行", width="small"),
                        "URL": st.column_config.TextColumn("URL"),
                        "再生数": st.column_config.TextColumn("再生数", width="small"),
                        "いいね": st.column_config.TextColumn("いいね", width="small"),
                        "保存": st.column_config.TextColumn("保存", width="small"),
                    },
                )

                # 失敗したURLだけまとめて表示
                if fail > 0:
                    failures = df[df["状態"] == "失敗"]
                    with st.expander(f"⚠ 失敗した {fail} 件を確認", expanded=False):
                        for _, r in failures.iterrows():
                            st.markdown(
                                f"- 行 **{r['行']}**: `{r['URL']}` → "
                                f"<span style='color:#c92a2a;'>{r['再生数']}</span>",
                                unsafe_allow_html=True,
                            )

        except (gspread.exceptions.SpreadsheetNotFound, PermissionError):
            st.error(
                "❌ スプレッドシートにアクセスできません。\n\n"
                "**スプレッドシートを以下のメールアドレスに「編集者」権限で共有してください：**"
            )
            st.code("x-metrics-sheets@x-metrics-494110.iam.gserviceaccount.com", language=None)
            st.markdown(
                "👉 スプレッドシートの右上「**共有**」ボタン → メールアドレスを貼り付け → 権限を「**編集者**」にして「送信」"
            )
        except gspread.exceptions.APIError as e:
            err_text = str(e)
            if "PERMISSION_DENIED" in err_text or "403" in err_text:
                st.error(
                    "❌ スプレッドシートにアクセスできません。\n\n"
                    "**スプレッドシートを以下のメールアドレスに「編集者」権限で共有してください：**"
                )
                st.code("x-metrics-sheets@x-metrics-494110.iam.gserviceaccount.com", language=None)
                st.markdown(
                    "👉 スプレッドシートの右上「**共有**」ボタン → メールアドレスを貼り付け → 権限を「**編集者**」にして「送信」"
                )
            else:
                st.error(f"❌ Google Sheets APIエラー: {err_text}")
        except KeyError as e:
            st.error(f"❌ シークレット設定エラー（{e} が見つかりません）")
        except Exception as e:
            err_msg = str(e) or type(e).__name__
            st.error(f"❌ エラー: {err_msg}")


# ═══════════════════════════════════════════════════════════
# ページ：対象シート管理
# ═══════════════════════════════════════════════════════════
elif st.session_state.page == "sheets":
    st.markdown('<div class="page-title"><span class="material-symbols-rounded" style="vertical-align:-4px;font-size:1.6rem;margin-right:6px;">folder</span>対象シート管理</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">よく使うスプレッドシートを登録すると、すぐに選んで取得できます</div>', unsafe_allow_html=True)

    # 管理シートに接続できるか確認
    if not get_manager_workbook():
        err = st.session_state.get("_manager_error", "")
        with st.container(border=True):
            st.error("❌ 管理シートに接続できません")
            if err:
                st.code(err, language=None)

            # サービスアカウントが作成できない場合の対処（よくある制限）
            if "storageQuotaExceeded" in err or "Service Accounts" in err or "quota" in err.lower():
                st.markdown("""
**📌 原因：サービスアカウントは独自のDrive容量を持っていないため、自動でファイルを作れません。**

下記の手順で **管理用シートを1つだけ手動で作成** してください：
                """)
            else:
                st.markdown("""
#### 管理シートを手動で設定する
                """)

            st.markdown("""
<span class="step-badge">1</span> Googleドライブで新規スプレッドシートを作成（名前は任意）

<span class="step-badge">2</span> 右上「共有」→ 以下のメールに **編集者** で共有：
            """, unsafe_allow_html=True)
            st.code("x-metrics-sheets@x-metrics-494110.iam.gserviceaccount.com", language=None)
            st.markdown("""
<span class="step-badge">3</span> シートのURLから **シートID** をコピー

例: `https://docs.google.com/spreadsheets/d/`**`1AbC...XyZ`**`/edit`

<span class="step-badge">4</span> Streamlit Cloud → Settings → Secrets に以下を追加：
            """, unsafe_allow_html=True)
            st.code('MANAGER_SHEET_ID = "コピーしたシートIDを貼り付け"', language="toml")
            st.markdown("<span class=\"step-badge\">5</span> Save → Ctrl+R でリロード", unsafe_allow_html=True)
        st.stop()

    registered = get_registered_sheets()

    # 登録フォーム
    with st.container(border=True):
        st.markdown("#### ➕ 新しいシートを登録")
        col_url, col_name = st.columns([3, 2])
        with col_url:
            new_url = st.text_input("スプレッドシートのURL", placeholder="https://docs.google.com/spreadsheets/d/xxx/edit", key="reg_url")
        with col_name:
            new_name = st.text_input("表示名（任意）", placeholder="例: メガポリスト", key="reg_name")

        if st.button("登録", type="primary", key="reg_btn"):
            if not new_url:
                st.warning("URLを入力してください")
            else:
                m = re.search(r"/spreadsheets/d/([a-zA-Z0-9-_]+)", new_url)
                new_sid = m.group(1) if m else new_url.strip()
                # シート名を取得（表示名が未指定なら）
                if not new_name:
                    try:
                        gc = get_gspread_client()
                        new_name = gc.open_by_key(new_sid).title
                    except Exception:
                        new_name = new_sid[:20]
                if add_registered_sheet(new_sid, new_name):
                    st.success(f"✅ 「{new_name}」を登録しました")
                    st.rerun()
                else:
                    st.warning("登録に失敗しました（重複している可能性があります）")

    # 登録済み一覧
    with st.container(border=True):
        st.markdown("#### 📋 登録済みシート一覧")
        if not registered:
            st.info("まだ登録されていません。上のフォームから登録してください")
        else:
            for r in registered:
                sid = r.get("シートID", "")
                name = r.get("表示名", sid)
                regdate = r.get("登録日", "")
                col1, col2, col3 = st.columns([3, 2, 1])
                col1.markdown(f"**{name}**  \n<span style='color:#888;font-size:0.8rem;'>`{sid[:30]}...`</span>", unsafe_allow_html=True)
                col2.markdown(f"<span style='color:#888;font-size:0.85rem;'>登録日: {regdate}</span>", unsafe_allow_html=True)
                if col3.button("🗑️", key=f"del_{sid}"):
                    if remove_registered_sheet(sid):
                        st.success(f"「{name}」を削除しました")
                        st.rerun()


# ═══════════════════════════════════════════════════════════
# ページ：実行ログ
# ═══════════════════════════════════════════════════════════
elif st.session_state.page == "logs":
    st.markdown('<div class="page-title"><span class="material-symbols-rounded" style="vertical-align:-4px;font-size:1.6rem;margin-right:6px;">history</span>実行ログ</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">過去の実行履歴を確認できます</div>', unsafe_allow_html=True)

    if not get_manager_workbook():
        err = st.session_state.get("_manager_error", "")
        with st.container(border=True):
            st.error("❌ 管理シートに接続できません")
            if err:
                st.code(err, language=None)
            st.markdown("""
**よくある原因：**
- 管理シートが **サービスアカウントに共有されていない**
- `MANAGER_SHEET_ID` が間違っている

**解決方法：**

<span class="step-badge">1</span> Secretsの`MANAGER_SHEET_ID`に書いた**スプレッドシート**を開く

<span class="step-badge">2</span> 右上「共有」→ 以下のメールに **編集者** で共有：
            """, unsafe_allow_html=True)
            st.code("x-metrics-sheets@x-metrics-494110.iam.gserviceaccount.com", language=None)
            st.markdown("<span class=\"step-badge\">3</span> アプリを Ctrl+R でリロード", unsafe_allow_html=True)
        st.stop()

    try:
        with st.spinner("ログを読み込み中..."):
            log_records = get_all_logs()

        if not log_records:
            with st.container(border=True):
                st.info("📭 まだ実行履歴がありません。「📊 数値を取得する」から実行すると履歴が記録されます。")
        else:
            # 集計サマリー
            df = pd.DataFrame(log_records)
            df = df.iloc[::-1].reset_index(drop=True)  # 新しい順

            total_runs = len(df)
            success_runs = (df["ステータス"] == "成功").sum() if "ステータス" in df.columns else 0
            partial_runs = (df["ステータス"] == "一部失敗").sum() if "ステータス" in df.columns else 0
            failed_runs = (df["ステータス"] == "失敗").sum() if "ステータス" in df.columns else 0

            with st.container(border=True):
                cols = st.columns(4)
                cols[0].metric("実行回数", total_runs)
                cols[1].metric("✅ 成功", int(success_runs))
                cols[2].metric("⚠️ 一部失敗", int(partial_runs))
                cols[3].metric("❌ 失敗", int(failed_runs))

            with st.container(border=True):
                # 検索＆フィルタ
                col_search, col_status, col_sheet = st.columns([3, 2, 2])
                with col_search:
                    search_query = st.text_input(
                        "🔍 検索",
                        placeholder="ID・日付・URL・ユーザー名などで絞り込み",
                        label_visibility="collapsed",
                        key="log_search",
                    )
                with col_status:
                    status_filter = st.selectbox(
                        "ステータス",
                        ["すべて", "✅ 成功", "⚠️ 一部失敗", "❌ 失敗"],
                        label_visibility="collapsed",
                        key="log_filter",
                    )
                with col_sheet:
                    sheet_options = ["すべてのシート"] + sorted(df["シート名"].unique().tolist()) if "シート名" in df.columns else ["すべてのシート"]
                    sheet_filter = st.selectbox(
                        "シート",
                        sheet_options,
                        label_visibility="collapsed",
                        key="log_sheet_filter",
                    )

                # ステータスをアイコン付きで表示
                if "ステータス" in df.columns:
                    df["ステータス"] = df["ステータス"].map({
                        "成功": "✅ 成功",
                        "一部失敗": "⚠️ 一部失敗",
                        "失敗": "❌ 失敗",
                    }).fillna(df["ステータス"])

                # フィルタ適用
                filtered_df = df.copy()
                if status_filter != "すべて":
                    filtered_df = filtered_df[filtered_df["ステータス"] == status_filter]
                if sheet_filter != "すべてのシート" and "シート名" in filtered_df.columns:
                    filtered_df = filtered_df[filtered_df["シート名"] == sheet_filter]
                if search_query:
                    q = search_query.lower()
                    mask = filtered_df.apply(
                        lambda row: q in " ".join(str(v) for v in row.values).lower(),
                        axis=1,
                    )
                    filtered_df = filtered_df[mask]

                st.caption(f"{len(filtered_df)} / {len(df)} 件を表示")

                # 表示用にURL一覧は省略表示
                display_df = filtered_df.copy()
                if "URL一覧" in display_df.columns:
                    display_df["URL一覧"] = display_df["URL一覧"].apply(
                        lambda s: (s[:50] + "...") if len(str(s)) > 50 else s
                    )
                if "シートID" in display_df.columns:
                    display_df = display_df.drop(columns=["シートID"])

                st.dataframe(
                    display_df,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "ID": st.column_config.TextColumn("ID", width="small"),
                        "実行時刻": st.column_config.TextColumn("開始時刻"),
                        "シート名": st.column_config.TextColumn("シート"),
                        "種別": st.column_config.TextColumn("種別", width="small"),
                        "件数": st.column_config.NumberColumn("件数", width="small"),
                        "成功": st.column_config.NumberColumn("成功", width="small"),
                        "失敗": st.column_config.NumberColumn("失敗", width="small"),
                        "所要時間": st.column_config.TextColumn("所要時間", width="small"),
                        "ステータス": st.column_config.TextColumn("ステータス"),
                        "URL一覧": st.column_config.TextColumn("URL一覧", width="medium"),
                    },
                )
    except (gspread.exceptions.SpreadsheetNotFound, PermissionError):
        st.error("❌ 管理用スプレッドシートにアクセスできません。共有設定を確認してください")
    except Exception as e:
        st.error(f"❌ エラー: {str(e) or type(e).__name__}")


# ═══════════════════════════════════════════════════════════
# ページ：使い方
# ═══════════════════════════════════════════════════════════
elif st.session_state.page == "howto":
    st.markdown('<div class="page-title"><span class="material-symbols-rounded" style="vertical-align:-4px;font-size:1.6rem;margin-right:6px;">help_outline</span>使い方</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">初めて使う方はこちらをご確認ください</div>', unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown("#### スプレッドシートの準備")
        st.markdown("""
**ヘッダー行に以下の列名を追加してください：**

| 列名 | 内容 | 必須 |
|------|------|------|
| `XURL` | XポストのURL | ✅ 必須 |
| `XImp` | 再生数（インプレッション） | 任意 |
| `Xいいね` | いいね数 | 任意 |
| `X保存` または `XBM` | 保存（ブックマーク）数 | 任意 |

> ヘッダー行は1行目でなくても大丈夫です（最初の10行を自動検索します）
        """)

    with st.container(border=True):
        st.markdown("#### 取得手順")
        st.markdown("""
<span class="step-badge">1</span> 対象シートをサービスアカウントと共有する（⚙️設定ページ参照）

<span class="step-badge">2</span>「📂 対象シート管理」でシートを登録する

<span class="step-badge">3</span>「📊 数値を取得する」ページで登録済みシートを選ぶ

<span class="step-badge">4</span>「▶ 取得開始」をクリック

<span class="step-badge">5</span> 自動でXの数値が取得され、シートに書き込まれます ✨
        """, unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown("#### 実行ログについて")
        st.markdown("""
取得を実行すると、**管理シート**に履歴が自動で記録されます（対象スプレッドシートには書き込まれません）。

「📋 実行ログ」ページから過去の実行結果を確認できます：
- 📅 実行時刻 / 所要時間
- 📊 対象件数 / 成功・失敗件数
- ✅ ステータス（成功 / 一部失敗 / 失敗）
- 🔍 ID・日付・URL・ユーザー名などで検索可能
        """)

    with st.container(border=True):
        st.markdown("#### よくある質問")

        with st.expander("「スプレッドシートが見つかりません」エラーが出る"):
            st.markdown("""
サービスアカウント（`x-metrics-sheets@x-metrics-494110.iam.gserviceaccount.com`）にスプレッドシートが共有されていない可能性があります。
⚙️設定ページの手順で共有を設定してください。
            """)

        with st.expander("「XURL列が見つかりません」エラーが出る"):
            st.markdown("""
ヘッダー行の列名が「XURL」と完全一致しているか確認してください。
スペースや全角文字が混じっていると認識されません。
            """)

        with st.expander("数値が「-」のまま取れない"):
            st.markdown("""
- **いいね**：通常はほぼすべて取得可能
- **再生数**：動画ツイートのみ取得可能（テキストのみのツイートは取得不可）
- **保存数**：取得不可（Xの公開APIで提供されていません）
            """)

        with st.expander("「削除済み」と表示される"):
            st.markdown("""
ツイートが削除されたか、非公開アカウントの可能性があります。
URLが正しいか、ツイートが現在も公開されているか確認してください。
            """)

        with st.expander("「取得失敗 (xxx)」エラーが出る"):
            st.markdown("""
- `429`: アクセスが集中しています。しばらく待ってから再試行してください
- `403`: アクセスが拒否されました（一時的な制限の可能性）
- `404`: ツイートが見つかりません（削除/非公開の可能性）
            """)


# ═══════════════════════════════════════════════════════════
# ページ：設定・シート共有
# ═══════════════════════════════════════════════════════════
elif st.session_state.page == "settings":
    st.markdown('<div class="page-title"><span class="material-symbols-rounded" style="vertical-align:-4px;font-size:1.6rem;margin-right:6px;">settings</span>設定・シート共有</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">スプレッドシートの共有設定を行います</div>', unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown("#### スプレッドシートの共有方法")
        st.markdown("""
このツールがスプレッドシートを読み書きするには、以下のサービスアカウントに**編集者権限**で共有する必要があります。
        """)

        st.code("x-metrics-sheets@x-metrics-494110.iam.gserviceaccount.com", language=None)

        st.markdown("""
<span class="step-badge">1</span> Googleスプレッドシートを開く

<span class="step-badge">2</span> 右上の「共有」ボタンをクリック

<span class="step-badge">3</span> 上記のメールアドレスを入力

<span class="step-badge">4</span> 権限を「**編集者**」に設定して「送信」
        """, unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown("#### 接続テスト")
        st.markdown("スプレッドシートのURLを入力して、接続できるか確認できます。")

        test_input = st.text_input(
            "テスト用スプレッドシートURL",
            placeholder="https://docs.google.com/spreadsheets/d/xxxxxxxx/edit",
            key="test_sheet"
        )
        if st.button("🔌 接続テスト", type="primary"):
            if not test_input:
                st.warning("URLを入力してください")
            else:
                m = re.search(r"/spreadsheets/d/([a-zA-Z0-9-_]+)", test_input)
                test_id = m.group(1) if m else test_input.strip()
                try:
                    with st.spinner("接続確認中..."):
                        creds_raw = st.secrets["GCP_SERVICE_ACCOUNT"]
                        creds_info = json.loads(creds_raw) if isinstance(creds_raw, str) else dict(creds_raw)
                        creds = Credentials.from_service_account_info(
                            creds_info,
                            scopes=["https://www.googleapis.com/auth/spreadsheets",
                                    "https://www.googleapis.com/auth/drive.readonly"],
                        )
                        gc = gspread.authorize(creds)
                        wb = gc.open_by_key(test_id)
                        sheets = [ws.title for ws in wb.worksheets()]
                    st.success(f"✅ 接続成功！　シート一覧: {', '.join(sheets)}")
                except (gspread.exceptions.SpreadsheetNotFound, PermissionError):
                    st.error("❌ アクセスできません。サービスアカウントに「編集者」権限で共有されているか確認してください")
                except Exception as e:
                    err_msg = str(e) or type(e).__name__
                    st.error(f"❌ エラー: {err_msg}")

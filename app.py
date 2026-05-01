import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import httpx
import re
import json
import math
import traceback
from datetime import date
import pandas as pd

# ─── ページ設定 ────────────────────────────────────────────
st.set_page_config(
    page_title="X Metrics",
    page_icon="𝕏",
    layout="wide",
)

# ─── グローバルCSS ─────────────────────────────────────────
st.markdown("""
<style>
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
}

/* サイドバーのボタン内のテキスト */
section[data-testid="stSidebar"] .stButton > button p,
section[data-testid="stSidebar"] .stButton > button span,
section[data-testid="stSidebar"] .stButton > button div {
    color: #cccccc !important;
    text-align: left !important;
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

    # ナビゲーション定義
    nav_items = [
        ("fetch",    "📊  数値を取得する"),
        ("howto",    "📖  使い方"),
        ("settings", "⚙️  設定・シート共有"),
    ]

    for key, label in nav_items:
        btn_type = "primary" if st.session_state.page == key else "secondary"
        if st.button(label, key=f"nav_{key}", use_container_width=True, type=btn_type):
            st.session_state.page = key
            st.rerun()

    # 下部：ログアウト
    st.markdown("<div style='position:fixed; bottom:2rem; width:186px;'>", unsafe_allow_html=True)
    st.markdown("<div style='border-top:1px solid #333; margin-bottom:0.8rem;'></div>", unsafe_allow_html=True)
    if st.button("🚪  ログアウト", use_container_width=True):
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


def _syndication_token(tweet_id: str) -> str:
    """Twitter Syndication API用のtokenを生成
    JS: ((Number(id) / 1e15) * Math.PI).toString(36).replace(/(0+|\.)/g, '')
    """
    n = (int(tweet_id) / 1e15) * math.pi
    chars = "0123456789abcdefghijklmnopqrstuvwxyz"

    # 整数部
    int_part = int(n)
    int_str = ""
    if int_part == 0:
        int_str = "0"
    else:
        while int_part > 0:
            int_part, r = divmod(int_part, 36)
            int_str = chars[r] + int_str

    # 小数部（精度15桁）
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


def _extract_views(data: dict):
    """様々なフィールドから再生数を取得"""
    # パターン1: views.count
    if isinstance(data.get("views"), dict):
        v = data["views"].get("count")
        if v is not None:
            return v
    # パターン2: view_count_info.count
    if isinstance(data.get("view_count_info"), dict):
        v = data["view_count_info"].get("count")
        if v is not None:
            return v
    # パターン3: ext_views.count
    if isinstance(data.get("ext_views"), dict):
        v = data["ext_views"].get("count")
        if v is not None:
            return v
    # パターン4: 直接 view_count
    if data.get("view_count") is not None:
        return data["view_count"]
    # パターン5: video_view_count
    if data.get("video_view_count") is not None:
        return data["video_view_count"]
    return "-"


def fetch_x(url: str, return_raw: bool = False):
    """X(Twitter)の公開Syndication APIを使って数値を取得（Token不要）"""
    try:
        m = re.search(r"/status/(\d+)", url)
        if not m:
            result = {"再生数": "URL不正", "いいね": "-", "保存": "-"}
            return (result, None) if return_raw else result
        tweet_id = m.group(1)
        token = _syndication_token(tweet_id)

        resp = httpx.get(
            "https://cdn.syndication.twimg.com/tweet-result",
            params={
                "id": tweet_id,
                "token": token,
                "lang": "ja",
                "features": "tfw_timeline_list:;tfw_follower_count_sunset:true;"
                            "tfw_tweet_edit_backend:on;tfw_refsrc_session:on;"
                            "tfw_show_business_verified_badge:on;"
                            "tfw_duplicate_scribes_to_settings:on;"
                            "tfw_show_blue_verified_badge:on;"
                            "tfw_legacy_timeline_sunset:true;"
                            "tfw_tweet_edit_frontend:on",
            },
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                              "AppleWebKit/537.36 (KHTML, like Gecko) "
                              "Chrome/120.0.0.0 Safari/537.36",
                "Accept": "application/json",
                "Referer": "https://platform.twitter.com/",
            },
            timeout=20,
            follow_redirects=True,
        )

        if resp.status_code == 200:
            data = resp.json()
            result = {
                "再生数": _extract_views(data),
                "いいね": data.get("favorite_count", "-"),
                "保存": data.get("bookmark_count", "-"),
            }
            return (result, data) if return_raw else result
        elif resp.status_code == 404:
            result = {"再生数": "削除済み", "いいね": "-", "保存": "-"}
            return (result, None) if return_raw else result
        result = {"再生数": f"取得失敗 ({resp.status_code})", "いいね": "-", "保存": "-"}
        return (result, None) if return_raw else result
    except Exception as e:
        result = {"再生数": "エラー", "いいね": "-", "保存": str(e)[:40]}
        return (result, None) if return_raw else result


# ═══════════════════════════════════════════════════════════
# ページ：数値を取得する
# ═══════════════════════════════════════════════════════════
if st.session_state.page == "fetch":
    st.markdown('<div class="page-title">📊 数値を取得する</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">スプレッドシートの XURL 列を読み取り、数値を取得して書き戻します</div>', unsafe_allow_html=True)

    with st.container(border=True):
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
        run = st.button("▶ 取得開始", disabled=not sheet_id, type="primary", use_container_width=False)

    # デバッグ用：1件テスト
    with st.expander("🔧 1件だけテスト取得（デバッグ用）"):
        st.caption("APIが何を返してくるか確認できます。数値が取れない場合に使ってください。")
        test_url = st.text_input(
            "テスト用 XのURL",
            placeholder="https://x.com/username/status/1234567890",
            key="debug_url",
        )
        if st.button("🔍 テスト取得", key="debug_btn"):
            if test_url:
                with st.spinner("取得中..."):
                    metrics, raw = fetch_x(test_url, return_raw=True)
                st.markdown("**取得結果：**")
                st.json(metrics)
                if raw:
                    st.markdown("**APIの生レスポンス（全フィールド）：**")
                    st.json(raw, expanded=False)

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
            st.balloons()

            with st.container(border=True):
                st.success(f"🎉 完了！ {len(url_rows)} 件をシートに書き込みました（{date.today()}）")
                df = pd.DataFrame(results)
                st.dataframe(df, use_container_width=True, hide_index=True)

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
# ページ：使い方
# ═══════════════════════════════════════════════════════════
elif st.session_state.page == "howto":
    st.markdown('<div class="page-title">📖 使い方</div>', unsafe_allow_html=True)
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
<span class="step-badge">1</span> スプレッドシートをサービスアカウントと共有する（⚙️設定ページ参照）

<span class="step-badge">2</span>「📊 数値を取得する」ページを開く

<span class="step-badge">3</span> スプレッドシートのURLを貼り付ける

<span class="step-badge">4</span>「▶ 取得開始」をクリック

<span class="step-badge">5</span> 自動でXの数値が取得され、シートに書き込まれます ✨
        """, unsafe_allow_html=True)

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
    st.markdown('<div class="page-title">⚙️ 設定・シート共有</div>', unsafe_allow_html=True)
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

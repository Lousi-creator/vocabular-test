import streamlit as st
import pandas as pd
import os
import time  
import re  
import sqlite3  
import hashlib 
import json
import requests
import base64
import fitz
from openai import OpenAI

def get_secret(key, default=""):
    try:
        return st.secrets[key]
    except Exception:
        val = os.getenv(key)
        if val is not None:
            return val
        try:
            with open(".env", "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        v = v.strip().strip('"').strip("'")
                        if k.strip() == key:
                            return v
        except Exception:
            pass
        return default

def baidu_ocr(image_bytes):
    api_key = get_secret("BAIDU_OCR_API_KEY")
    secret_key = get_secret("BAIDU_OCR_SECRET_KEY")
    if not api_key or not secret_key:
        return None, "请先在 .env 或 Streamlit Secrets 中配置 BAIDU_OCR_API_KEY 和 BAIDU_OCR_SECRET_KEY"
    try:
        token_url = f"https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id={api_key}&client_secret={secret_key}"
        token_resp = requests.post(token_url).json()
        access_token = token_resp.get("access_token")
        if not access_token:
            return None, f"获取百度 Access Token 失败：{token_resp}"
        img_base64 = base64.b64encode(image_bytes).decode("utf-8")
        ocr_url = f"https://aip.baidubce.com/rest/2.0/ocr/v1/accurate_basic?access_token={access_token}"
        ocr_resp = requests.post(ocr_url, data={
            "image": img_base64,
            "language_type": "CHN_ENG",
            "detect_direction": "true",
            "paragraph": "true"
        }).json()
        if "error_code" in ocr_resp:
            return None, f"OCR 识别失败：{ocr_resp.get('error_msg', '未知错误')}"
        words = ocr_resp.get("words_result", [])
        if not words:
            return "", "未识别到文字，请确保照片清晰且包含中英文内容"
        text = "\n".join([w["words"] for w in words])
        return text, None
    except Exception as e:
        return None, f"OCR 调用异常：{str(e)}"

# ==========================================
# 0. 网页全局设置 
# ==========================================
st.set_page_config(page_title="逐梦英语 · AI智能备考", page_icon="🎯", layout="centered", initial_sidebar_state="collapsed")

# ==========================================
# 0.5 终极前端黑魔法 (UI 大重构 - 护眼暗黑毛玻璃大厅)
# ==========================================
BASE_CSS = """
<style>
/* 隐藏冗余元素 */
#MainMenu, footer {visibility: hidden;}
header {background-color: transparent !important; box-shadow: none !important;} 
[data-testid="collapsedControl"] {display: none;} /* 强制隐藏左上角的侧边栏展开箭头 */

/* 全局背景：深邃护眼的午夜深灰渐变 */
.stApp {
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%) !important;
    background-attachment: fixed !important;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif !important;
    color: #e2e8f0 !important;
} 

/* 主内容容器：加宽以适应卡片网格，增加上下边距 */
.block-container {
    max-width: 800px !important; 
    padding-top: 3rem !important;
    padding-bottom: 5rem !important;
}

/* 全局文字颜色覆写，适应暗黑模式 */
h1, h2, h3, p, span, div {
    color: #e2e8f0;
}
p, small {
    color: #94a3b8;
}

/* 🍎 核心：通用深色毛玻璃卡片 */
.glass-card {
    background: rgba(30, 41, 59, 0.6) !important;
    backdrop-filter: blur(16px) !important;
    -webkit-backdrop-filter: blur(16px) !important;
    border-radius: 24px !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2) !important;
    padding: 25px;
    margin-bottom: 20px;
}

/* Streamlit 原生组件暗黑化 */
div[data-testid="stForm"], 
div[data-testid="stExpander"],
div[data-testid="stRadio"] > div,
div[data-testid="stSelectbox"] > div {
    background: rgba(30, 41, 59, 0.6) !important;
    backdrop-filter: blur(16px) !important;
    border-radius: 16px !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    padding: 15px 20px;
}

/* 文本输入框升级：暗黑系光晕 */
.stTextInput > div > div > input {
    background: rgba(15, 23, 42, 0.6) !important;
    border: 1px solid rgba(255, 255, 255, 0.15) !important;
    border-radius: 16px !important;
    text-align: center !important; 
    font-size: 24px !important; 
    font-weight: 800 !important; 
    color: #f8fafc !important; 
    padding: 15px !important;
    transition: all 0.3s ease !important;
}
.stTextInput > div > div > input:focus { 
    border: 1px solid #3b82f6 !important; 
    box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.2) !important;
    background: rgba(15, 23, 42, 0.9) !important;
    outline: none !important;
}

/* 多行文本框 (写作区) */
.stTextArea > div > div > textarea {
    background: rgba(15, 23, 42, 0.6) !important;
    border-radius: 16px !important;
    border: 1px solid rgba(255, 255, 255, 0.15) !important;
    color: #e2e8f0 !important;
    padding: 15px !important;
    font-size: 16px !important;
    transition: all 0.3s ease !important;
}
.stTextArea > div > div > textarea:focus {
    border: 1px solid #3b82f6 !important; 
    box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.2) !important;
}

/* ✨ 核心按钮升级：质感极光边框 */
.stButton > button {
    border-radius: 100px !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    background: linear-gradient(135deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0.05) 100%) !important;
    color: #f8fafc !important;
    font-weight: 700 !important; 
    letter-spacing: 0.5px !important;
    height: 50px !important;
    box-shadow: 0 4px 15px rgba(0,0,0,0.1) !important;
    transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1) !important;
    backdrop-filter: blur(10px) !important;
}
.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 25px rgba(59, 130, 246, 0.3) !important;
    border: 1px solid rgba(59, 130, 246, 0.5) !important;
    background: rgba(59, 130, 246, 0.1) !important;
}
.stButton > button:active {
    transform: translateY(1px) !important;
}

/* 突出显示的主按钮 (例如：开始测试) */
button[kind="primary"] {
    background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%) !important;
    border: none !important;
}
button[kind="primary"]:hover {
    background: linear-gradient(135deg, #60a5fa 0%, #3b82f6 100%) !important;
    box-shadow: 0 8px 25px rgba(59, 130, 246, 0.4) !important;
    color: white !important;
}

/* 返回大厅小按钮特供 */
.back-btn > div > button {
    height: 40px !important;
    width: 140px !important;
    background: rgba(0,0,0,0.3) !important;
    border-radius: 12px !important;
    margin-bottom: 20px !important;
}

/* 进度条样式美化 */
.stProgress > div > div > div {
    background: linear-gradient(90deg, #3b82f6 0%, #06b6d4 100%) !important;
    border-radius: 100px !important;
}
.stProgress > div {
    background-color: rgba(0,0,0,0.3) !important;
    border-radius: 100px !important;
}

/* 特殊高亮颜色覆盖 */
.text-highlight { color: #60a5fa !important; }
.text-warning { color: #f59e0b !important; }
.text-danger { color: #ef4444 !important; }
.text-success { color: #10b981 !important; }

/* Dashboard 卡片交互特效 */
.dash-card {
    background: rgba(30, 41, 59, 0.4);
    border: 1px solid rgba(255,255,255,0.05);
    border-radius: 24px;
    padding: 30px;
    text-align: center;
    transition: all 0.3s ease;
    cursor: pointer;
    height: 100%;
}
.dash-card:hover {
    background: rgba(30, 41, 59, 0.8);
    border: 1px solid rgba(59, 130, 246, 0.4);
    transform: translateY(-5px);
    box-shadow: 0 15px 35px rgba(0,0,0,0.3);
}

</style>
"""
st.markdown(BASE_CSS, unsafe_allow_html=True) 

PERFECT_CSS_TEMPLATE = """
<style>
@keyframes perfectFade_UID {
    0% { transform: translate(-50%, -50%) scale(0.8); opacity: 0; }
    20% { transform: translate(-50%, -50%) scale(1.05); opacity: 1; }
    80% { transform: translate(-50%, -50%) scale(1); opacity: 1; }
    100% { transform: translate(-50%, -50%) scale(1); opacity: 0; }
}
.perfect-text-UID {
    position: fixed; top: 30%; left: 50%; z-index: 999999;
    font-family: -apple-system, BlinkMacSystemFont, sans-serif;
    font-size: 64px; font-weight: 900; color: #22c55e;
    letter-spacing: 8px;
    pointer-events: none;
    animation: perfectFade_UID 1.2s ease-out forwards;
}
</style>
<div class="perfect-text-UID">✓ 正确</div>
"""

# ==========================================
# 1. 数据库与身份验证引擎
# ==========================================
def init_db():
    conn = sqlite3.connect('users.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            credits INTEGER DEFAULT 3,
            status TEXT DEFAULT 'active'
        )
    ''')
    try:
        c.execute("ALTER TABLE users ADD COLUMN status TEXT DEFAULT 'active'")
        c.execute("UPDATE users SET status = 'active' WHERE status IS NULL")
    except sqlite3.OperationalError:
        pass
        
    c.execute('''
        CREATE TABLE IF NOT EXISTS progress (
            username TEXT,
            mode TEXT,
            tier TEXT,
            quarantine_list TEXT,
            PRIMARY KEY (username, mode, tier)
        )
    ''')
    
    # 【核心新增】：用户专属错题库表
    c.execute('''
        CREATE TABLE IF NOT EXISTS user_wrong_words (
            username TEXT,
            word TEXT,
            wrong_count INTEGER,
            PRIMARY KEY (username, word)
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS credit_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'pending'
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS learning_roadmap (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            category TEXT NOT NULL,
            item TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# --- 进度存档相关 ---
def save_progress(username, mode, tier, q_list):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    q_str = json.dumps(q_list)
    c.execute('''
        REPLACE INTO progress (username, mode, tier, quarantine_list)
        VALUES (?, ?, ?, ?)
    ''', (username, mode, tier, q_str))
    conn.commit()
    conn.close()

def load_progress(username, mode, tier):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('SELECT quarantine_list FROM progress WHERE username = ? AND mode = ? AND tier = ?', (username, mode, tier))
    row = c.fetchone()
    conn.close()
    if row:
        return json.loads(row[0])
    return []

# --- 【新增：千人千面错题引擎】 ---
def get_user_wrong_words(username):
    """获取指定用户的专属错题字典 {word: count}"""
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('SELECT word, wrong_count FROM user_wrong_words WHERE username = ? AND wrong_count > 0', (username,))
    data = c.fetchall()
    conn.close()
    return {row[0]: row[1] for row in data}

def update_user_wrong_word(username, word, is_correct, mode):
    """静默更新用户的错题次数"""
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('SELECT wrong_count FROM user_wrong_words WHERE username = ? AND word = ?', (username, word))
    row = c.fetchone()
    current_count = row[0] if row else 0

    if is_correct:
        if mode == "错题大扫除":
            new_count = 0  # 只有在错题本模式答对，才将其彻底消灭
        else:
            new_count = current_count
    else:
        new_count = current_count + 1
        
    c.execute('''
        REPLACE INTO user_wrong_words (username, word, wrong_count)
        VALUES (?, ?, ?)
    ''', (username, word, new_count))
    conn.commit()
    conn.close()

# --- 身份系统 ---
def make_hash(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_hash(password, hashed_text):
    return make_hash(password) == hashed_text

def create_user(username, password):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    try:
        status = 'active' if username == get_secret("ADMIN_USERNAME", "admin") else 'pending'
        c.execute('INSERT INTO users (username, password, credits, status) VALUES (?, ?, ?, ?)', (username, make_hash(password), 3, status))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False 
    finally:
        conn.close()

def login_user(username, password):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('SELECT password, credits, status FROM users WHERE username = ?', (username,))
    data = c.fetchone()
    conn.close()
    if data and check_hash(password, data[0]):
        return (data[1], data[2])
    return None

def deduct_credit(username):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('UPDATE users SET credits = credits - 1 WHERE username = ? AND credits > 0', (username,))
    conn.commit()
    c.execute('SELECT credits FROM users WHERE username = ?', (username,))
    new_credits = c.fetchone()[0]
    conn.close()
    return new_credits

def get_pending_users():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT username FROM users WHERE status = 'pending'")
    users = [row[0] for row in c.fetchall()]
    conn.close()
    return users

def approve_user(username):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("UPDATE users SET status = 'active' WHERE username = ? AND status = 'pending'", (username,))
    conn.commit()
    conn.close()

def reject_user(username):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("DELETE FROM users WHERE username = ? AND status = 'pending'", (username,))
    conn.commit()
    conn.close()

def has_pending_credit_request(username):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM credit_requests WHERE username = ? AND status = 'pending'", (username,))
    count = c.fetchone()[0]
    conn.close()
    return count > 0

def request_credits(username):
    if has_pending_credit_request(username):
        return False
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("INSERT INTO credit_requests (username, status) VALUES (?, 'pending')", (username,))
    conn.commit()
    conn.close()
    return True

def get_pending_credit_requests():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT id, username FROM credit_requests WHERE status = 'pending' ORDER BY requested_at")
    requests = [(row[0], row[1]) for row in c.fetchall()]
    conn.close()
    return requests

def approve_credit_request(request_id, username, credits_to_add):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("UPDATE credit_requests SET status = 'approved' WHERE id = ?", (request_id,))
    c.execute("UPDATE users SET credits = credits + ? WHERE username = ?", (credits_to_add, username))
    c.execute("SELECT credits FROM users WHERE username = ?", (username,))
    new_credits = c.fetchone()[0]
    conn.commit()
    conn.close()
    return new_credits

def reject_credit_request(request_id):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("UPDATE credit_requests SET status = 'rejected' WHERE id = ?", (request_id,))
    conn.commit()
    conn.close()

def get_user_credits(username):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('SELECT credits FROM users WHERE username = ?', (username,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else 0

def add_roadmap_item(username, category, item):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM learning_roadmap WHERE username = ? AND item = ?", (username, item))
    if c.fetchone()[0] > 0:
        conn.close()
        return False
    c.execute("INSERT INTO learning_roadmap (username, category, item) VALUES (?, ?, ?)", (username, category, item))
    conn.commit()
    conn.close()
    return True

def get_roadmap(username):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT category, item FROM learning_roadmap WHERE username = ? ORDER BY created_at DESC", (username,))
    rows = c.fetchall()
    conn.close()
    grouped = {}
    for cat, item in rows:
        grouped.setdefault(cat, []).append(item)
    return grouped

def clear_roadmap(username):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("DELETE FROM learning_roadmap WHERE username = ?", (username,))
    conn.commit()
    conn.close()

# ==========================================
# 数据文件初始化容错处理 
# ==========================================
if not os.path.exists('words.csv'):
    pd.DataFrame([{'word': 'apple', 'definition': '苹果', 'wrong_count': 0, 'phonetic': '/ˈæpl/', 'frequency_tier': '🟢 高频核心词汇'}]).to_csv('words.csv', index=False)
if not os.path.exists('essays.csv'):
    pd.DataFrame([
        {'category': '开头', 'subcategory': '建议信', 'content': 'I am writing to express my views concerning...', 'translation': '我写信是想表达关于……的看法。'},
        {'category': '开头', 'subcategory': '建议信', 'content': 'Having learned that you are faced with..., I would like to give you some practical tips.', 'translation': '得知你正面临……我想给你一些实用的建议。'},
        {'category': '开头', 'subcategory': '邀请信', 'content': 'I am writing to invite you to join us in...', 'translation': '我写信是想邀请你加入我们……'},
        {'category': '开头', 'subcategory': '申请信/自荐信', 'content': 'I am writing to apply for the position of...', 'translation': '我写信是想申请……的职位。'},
        {'category': '开头', 'subcategory': '感谢信', 'content': 'I am writing to convey my heartfelt gratitude for...', 'translation': '我写信是为了表达对……由衷的感谢。'},
        {'category': '开头', 'subcategory': '道歉信', 'content': 'I am writing to offer my sincere apology for...', 'translation': '我写信是想就……表达我诚挚的道歉。'},
        {'category': '开头', 'subcategory': '演讲稿', 'content': 'It is a great privilege for me to stand here and address the topic of...', 'translation': '很荣幸站在这里谈论……的话题。'},
        {'category': '正文过渡', 'subcategory': '建议信', 'content': 'Here are several suggestions that you may find helpful.', 'translation': '以下几条建议你可能会觉得有用。'},
        {'category': '正文过渡', 'subcategory': '通用过渡', 'content': 'Needless to say, it is of vital importance for us to take immediate action.', 'translation': '毋庸置疑，我们立即采取行动至关重要。'},
        {'category': '结尾', 'subcategory': '建议信', 'content': 'I sincerely hope that my suggestions will be of some help to you.', 'translation': '我真诚希望我的建议能对你有所帮助。'},
        {'category': '结尾', 'subcategory': '邀请信', 'content': 'I am convinced that your participation will add great brilliance to our activity.', 'translation': '我深信你的参与将为我们的活动增光添彩。'},
        {'category': '结尾', 'subcategory': '通用', 'content': 'Looking forward to your prompt reply.', 'translation': '期待你的及时回复。'},
        {'category': '结尾', 'subcategory': '通用', 'content': 'Only by doing so can we embrace a brighter and more promising future.', 'translation': '唯有如此，我们才能拥抱一个更加光明灿烂的未来。（倒装句）'},
        {'category': '万能衔接', 'subcategory': '并列递进', 'content': 'To begin with / What is more / Last but not least', 'translation': '首先 / 更重要的是 / 最后但同样重要的是'},
        {'category': '万能衔接', 'subcategory': '转折对比', 'content': 'On the contrary / However / Alternatively', 'translation': '相反 / 然而 / 或者'},
        {'category': '万能衔接', 'subcategory': '因果总结', 'content': 'Consequently / As a result / Therefore', 'translation': '因此 / 结果 / 所以'},
        {'category': '万能衔接', 'subcategory': '举例论证', 'content': 'Take... as an example. It is... that...', 'translation': '以……为例。正是……才……'},
        {'category': '亮点句型', 'subcategory': '倒装与强调', 'content': 'Only in this way can we truly live up to our potential and embrace a better future.', 'translation': '唯有如此，我们才能真正发挥潜力、拥抱美好未来。（倒装句）'},
        {'category': '亮点句型', 'subcategory': '强调句', 'content': 'It is consistent practice rather than mere talent that ultimately leads to success.', 'translation': '正是持续练习而非单纯天赋最终通向成功。'},
        {'category': '亮点句型', 'subcategory': '非谓语/高级句式', 'content': 'Inspired by his words, I made up my mind to pursue my dream with unwavering determination.', 'translation': '受他话语的鼓舞，我下定决心以坚定不移的意志追求梦想。（分词作状语）'},
    ]).to_csv('essays.csv', index=False)
if not os.path.exists('upgrade.csv'):
    pd.DataFrame([
        {'basic': 'good', 'advanced': 'excellent / outstanding', 'reason': 'good 太过口语化'},
        {'basic': 'bad', 'advanced': 'detrimental / negative', 'reason': 'bad 缺乏学术感'}
    ]).to_csv('upgrade.csv', index=False)

# 状态变量初始化
if 'current_word' not in st.session_state:
    st.session_state.current_word = ""; st.session_state.chinese_meaning = ""
    st.session_state.phonetic = ""; st.session_state.feedback = ""
    st.session_state.perfect_hit = False; st.session_state.quarantine_list = [] 
if 'options' not in st.session_state:
    st.session_state.options = []
if 'correct_count' not in st.session_state:
    st.session_state.correct_count = 0
if 'wrong_count' not in st.session_state:
    st.session_state.wrong_count = 0
if 'essay_draft' not in st.session_state:
    st.session_state.essay_draft = ""
if 'essay_topic' not in st.session_state:
    st.session_state.essay_topic = ""
if 'last_ai_time' not in st.session_state:
    st.session_state.last_ai_time = 0.0  
if 'current_user' not in st.session_state:
    st.session_state.current_user = None
if 'user_credits' not in st.session_state:
    st.session_state.user_credits = 0
if 'show_balloons' not in st.session_state:
    st.session_state.show_balloons = False
if 'is_admin' not in st.session_state:
    st.session_state.is_admin = False
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'home'
if 'listening_test' not in st.session_state:
    st.session_state.listening_test = None
if 'listening_q_index' not in st.session_state:
    st.session_state.listening_q_index = 0
if 'listening_answers' not in st.session_state:
    st.session_state.listening_answers = {}
if 'listening_finished' not in st.session_state:
    st.session_state.listening_finished = False
if 'continuation_lecture' not in st.session_state:
    st.session_state.continuation_lecture = None
if 'continuation_page_idx' not in st.session_state:
    st.session_state.continuation_page_idx = 0
if 'drill_mode' not in st.session_state:
    st.session_state.drill_mode = None
if 'drill_technique' not in st.session_state:
    st.session_state.drill_technique = '全部技法'
if 'drill_q_idx' not in st.session_state:
    st.session_state.drill_q_idx = 0
if 'drill_user_answer' not in st.session_state:
    st.session_state.drill_user_answer = ''
if 'drill_ai_question' not in st.session_state:
    st.session_state.drill_ai_question = None
if 'drill_ai_feedback' not in st.session_state:
    st.session_state.drill_ai_feedback = None
if 'drill_correct' not in st.session_state:
    st.session_state.drill_correct = 0
if 'drill_total' not in st.session_state:
    st.session_state.drill_total = 0

def navigate_to(page_name):
    st.session_state.current_page = page_name
    reset_task_state() 
    st.rerun()

# ==========================================
# 2. 核心交互函数 
# ==========================================
def append_to_draft(text_to_add):
    st.session_state.essay_draft += text_to_add + " "

def reset_task_state():
    st.session_state.feedback = ""          
    st.session_state.current_word = ""      
    st.session_state.show_balloons = False
    st.session_state.options = []
    st.session_state.correct_count = 0
    st.session_state.wrong_count = 0  

def get_next_word(mode, tier):
    df = pd.read_csv('words.csv')
    if 'frequency_tier' not in df.columns: df['frequency_tier'] = "🟢 高频核心词汇"
    if st.session_state.quarantine_list: df = df[~df['word'].isin(st.session_state.quarantine_list)]
    
    # 【核心升级】：如果是错题大扫除，只抓取该用户专属数据库里的错题
    if mode == "错题大扫除": 
        if st.session_state.current_user:
            wrong_dict = get_user_wrong_words(st.session_state.current_user)
            df = df[df['word'].isin(wrong_dict.keys())]
        else:
            df = pd.DataFrame()
            
    if tier != "🌍 全库混合 (不分级)": df = df[df['frequency_tier'] == tier]
        
    if df.empty:
        st.session_state.current_word = ""
        st.session_state.feedback = "🎉 恭喜！当前任务节点已通关，请切换其他任务！"
        st.session_state.show_balloons = True
        return
        
    row = df.sample(n=1).iloc[0]
    st.session_state.current_word = row['word']
    st.session_state.chinese_meaning = row['definition']
    st.session_state.phonetic = row['phonetic'] if 'phonetic' in row else ""
    distractor_pool = df[df['word'] != st.session_state.current_word]
    n_distractors = min(5, len(distractor_pool))
    distractors = distractor_pool.sample(n=n_distractors)['word'].tolist() if n_distractors > 0 else []
    options = [st.session_state.current_word] + distractors
    import random
    random.shuffle(options)
    st.session_state.options = options

def check_answer(selected_word=None):
    if selected_word is None:
        selected_word = st.session_state.get("user_input", "").strip().lower()
    mode = st.session_state.mode_selector
    tier = st.session_state.tier_selector 
    if not selected_word or not st.session_state.current_word: return
    
    correct_word = st.session_state.current_word
    
    if selected_word == correct_word:
        st.session_state.perfect_hit = True; st.session_state.feedback = ""
        st.session_state.correct_count += 1
        if st.session_state.current_user:
            update_user_wrong_word(st.session_state.current_user, correct_word, True, mode)
    else:
        st.session_state.feedback = f"❌ 正确拼写: {correct_word}"
        st.session_state.wrong_count += 1
        if st.session_state.current_user:
            update_user_wrong_word(st.session_state.current_user, correct_word, False, mode)
        
    only_quarantine_correct = (mode != "错题大扫除") or (selected_word == correct_word)
    if correct_word not in st.session_state.quarantine_list and only_quarantine_correct:
        st.session_state.quarantine_list.append(correct_word)
        if st.session_state.current_user:
            save_progress(st.session_state.current_user, mode, tier, st.session_state.quarantine_list)
            
    st.session_state.user_input = ""
    st.session_state.options = []
    get_next_word(mode, tier)
    st.rerun() 

# ==========================================
# 4. 主界面渲染路由引擎
# ==========================================

if st.session_state.current_user is None:
    st.markdown("""
    <div style='text-align: center; margin-bottom: 24px;'>
        <h1 style='font-weight: 900; font-size: 3.4rem; margin-bottom: 0; letter-spacing: 2px;'>
            逐梦英语<span class='text-highlight'>.</span>
        </h1>
        <p style='font-size: 1rem; margin-top: 6px; font-style: italic; color: #94a3b8; font-weight: 400;'>
            Your AI study buddy for Gaokao ✌️
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class='glass-card' style='text-align:center; padding: 20px 24px; margin-bottom: 28px;'>
        <p style='font-size: 1.1rem; font-weight: 600; color: #f1f5f9; margin: 0 0 6px 0;'>
            <span style='color: #f59e0b;'>✦</span> Dream big. Study smart. <span style='color: #22c55e;'>Ace it.</span>
        </p>
        <p style='font-size: 0.85rem; color: #94a3b8; margin: 0; line-height: 1.7;'>
            Every word you learn today <br>is a step closer to your dream university 🎓
        </p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        tab_login, tab_reg = st.tabs(["👋 Welcome back!", "✨ Join the club"])

        with tab_login:
            st.write("<br>", unsafe_allow_html=True)
            log_user = st.text_input("Username", key="log_u", placeholder="Enter your username")
            log_pwd = st.text_input("Password", type="password", key="log_p", placeholder="••••••••")
            st.write("<br>", unsafe_allow_html=True)
            if st.button("🚀 Let's roll!", use_container_width=True, type="primary"):
                result = login_user(log_user, log_pwd)
                if result is not None:
                    credits, status = result
                    if status == 'pending':
                        st.warning("⏳ Hang tight! 管理员还在审核你的账号~")
                    else:
                        st.session_state.current_user = log_user
                        st.session_state.user_credits = credits
                        st.session_state.is_admin = (log_user == get_secret("ADMIN_USERNAME", "admin"))
                        st.rerun()
                else:
                    st.error("Oops! 用户名或密码不对哦~")

        with tab_reg:
            st.write("<br>", unsafe_allow_html=True)
            reg_user = st.text_input("Pick a username", key="reg_u", placeholder="Make it cool 😎")
            reg_pwd = st.text_input("Create a password", type="password", key="reg_p", placeholder="Make it strong 💪")
            st.write("<br>", unsafe_allow_html=True)
            if st.button("🎉 Count me in!", use_container_width=True):
                if reg_user and reg_pwd:
                    if create_user(reg_user, reg_pwd):
                        st.success("🎉 You're almost there! 等管理员通过就能开练啦~")
                    else:
                        st.error("Uh-oh! 这个名字被抢了，换一个吧~")
                else:
                    st.warning("Hey, 用户名和密码都得填哦~")
        st.markdown("</div>", unsafe_allow_html=True)

elif st.session_state.current_page == 'home':
    st.session_state.user_credits = get_user_credits(st.session_state.current_user)
    st.markdown(f"""
    <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;'>
        <div>
            <h2 style='margin: 0; font-weight: 800;'>欢迎回来, <span class='text-highlight'>{st.session_state.current_user}</span></h2>
        </div>
    </div>
    """, unsafe_allow_html=True)

    current_credits = st.session_state.user_credits
    has_pending = has_pending_credit_request(st.session_state.current_user)

    st.markdown("<div class='glass-card' style='text-align:center; padding: 18px 20px; margin-bottom: 24px;'>", unsafe_allow_html=True)
    if current_credits <= 1:
        st.markdown(f"""
        <p style='font-size: 0.95rem; color: #f8fafc; margin: 0 0 6px 0;'>
            ⚠️ AI 算力余额：<span class='text-danger' style='font-weight:700;'>{current_credits}</span> 次
        </p>
        """, unsafe_allow_html=True)
        if has_pending:
            st.info("⏳ 申请已提交，等待管理员审核中...", icon="📨")
        else:
            st.warning("额度即将耗尽！", icon="🪫")
            if st.button("📩 向管理员申请更多额度", key="req_credits", use_container_width=True):
                if request_credits(st.session_state.current_user):
                    st.success("✅ 申请已提交！请耐心等待管理员审核。")
                    st.rerun()
                else:
                    st.warning("你已有一个待审核的申请，请勿重复提交。")
    elif current_credits <= 2:
        st.markdown(f"""
        <p style='font-size: 0.95rem; color: #f8fafc; margin: 0;'>
            🔋 AI 算力余额：<span class='text-warning' style='font-weight:700;'>{current_credits}</span> 次
        </p>
        """, unsafe_allow_html=True)
        if has_pending:
            st.info("📨 申请已提交，等待管理员审核中...")
        else:
            if st.button("📩 申请补充额度", key="req_credits_2", use_container_width=True):
                if request_credits(st.session_state.current_user):
                    st.success("✅ 申请已提交！请耐心等待管理员审核。")
                    st.rerun()
                else:
                    st.warning("你已有一个待审核的申请。")
    else:
        st.markdown(f"""
        <p style='font-size: 0.95rem; color: #f8fafc; margin: 0;'>
            ✅ AI 算力余额：<span class='text-success' style='font-weight:700;'>{current_credits}</span> 次
        </p>
        """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    col_empty, col_out = st.columns([5, 1])
    with col_out:
        if st.button("退出登录", use_container_width=True):
            st.session_state.current_user = None
            st.session_state.is_admin = False
            st.rerun()

    st.write("<br>", unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown("""
        <div class='dash-card'>
            <div style='font-size: 50px; margin-bottom: 15px;'>🎯</div>
            <h3 style='margin-bottom: 10px;'>单词通关挑战</h3>
            <p style='font-size: 0.9rem; margin-bottom: 25px;'>基于高频考纲，进行科学的错题分级筛查与靶向治疗。</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("进入靶场 →", key="nav_vocab", use_container_width=True):
            navigate_to('vocab')

    with col2:
        st.markdown("""
        <div class='dash-card'>
            <div style='font-size: 50px; margin-bottom: 15px;'>✍️</div>
            <h3 style='margin-bottom: 10px;'>写作灵感工坊</h3>
            <p style='font-size: 0.9rem; margin-bottom: 25px;'>智能捕捉低级词汇，召唤 DeepSeek 导师进行降维打击式批改。</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("启动工坊 →", key="nav_essay", use_container_width=True):
            navigate_to('essay')
    
    with col3:
        st.markdown("""
        <div class='dash-card'>
            <div style='font-size: 50px; margin-bottom: 15px;'>🎧</div>
            <h3 style='margin-bottom: 10px;'>听力训练营</h3>
            <p style='font-size: 0.9rem; margin-bottom: 25px;'>高考真题听力训练，全真模拟 20 题听力考试，即时评分。</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("开始训练 →", key="nav_listening", use_container_width=True):
            navigate_to('listening')

    with col4:
        st.markdown("""
        <div class='dash-card'>
            <div style='font-size: 50px; margin-bottom: 15px;'>📖</div>
            <h3 style='margin-bottom: 10px;'>读后续写宝典</h3>
            <p style='font-size: 0.9rem; margin-bottom: 25px;'>巅峰之作五讲精粹，情节构思、描写技法、满分范例。</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("翻开宝典 →", key="nav_continuation", use_container_width=True):
            navigate_to('continuation')

    if st.session_state.is_admin:
        st.write("<br>", unsafe_allow_html=True)
        st.markdown("---")
        st.markdown("<h4 style='text-align:center;'>👑 管理控制中心</h4>", unsafe_allow_html=True)
        col_admin1, col_admin2, col_admin3 = st.columns([1, 2, 1])
        with col_admin2:
            st.markdown("<div class='glass-card' style='text-align:center; padding: 20px;'>", unsafe_allow_html=True)
            pending_users = get_pending_users()
            if not pending_users:
                st.info("系统安全，无待审核请求")
            else:
                st.warning(f"发现 {len(pending_users)} 条注册申请")
                for pu in pending_users:
                    c1, c2, c3 = st.columns([2, 1, 1])
                    c1.write(f"**{pu}**")
                    if c2.button("放行", key=f"app_{pu}", use_container_width=True):
                        approve_user(pu); st.rerun()
                    if c3.button("拦截", key=f"rej_{pu}", use_container_width=True):
                        reject_user(pu); st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

            st.write("<br>", unsafe_allow_html=True)
            st.markdown("<div class='glass-card' style='text-align:center; padding: 20px;'>", unsafe_allow_html=True)
            st.markdown("<h5>🔋 额度申请审核</h5>", unsafe_allow_html=True)
            credit_reqs = get_pending_credit_requests()
            if not credit_reqs:
                st.info("暂无额度申请")
            else:
                st.warning(f"{len(credit_reqs)} 条额度申请待处理")
                for req_id, req_user in credit_reqs:
                    st.markdown(f"<p style='margin-bottom:8px;'><b>{req_user}</b> 请求补充额度</p>", unsafe_allow_html=True)
                    c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
                    if c2.button("+1", key=f"cr_app1_{req_id}", use_container_width=True):
                        new_creds = approve_credit_request(req_id, req_user, 1)
                        st.success(f"已批准 {req_user} +1 额度（当前 {new_creds}）"); st.rerun()
                    if c3.button("+2", key=f"cr_app2_{req_id}", use_container_width=True):
                        new_creds = approve_credit_request(req_id, req_user, 2)
                        st.success(f"已批准 {req_user} +2 额度（当前 {new_creds}）"); st.rerun()
                    if c4.button("拒绝", key=f"cr_rej_{req_id}", use_container_width=True):
                        reject_credit_request(req_id)
                        st.success(f"已拒绝 {req_user} 的申请"); st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

elif st.session_state.current_page == 'vocab':
    st.markdown("<div class='back-btn'>", unsafe_allow_html=True)
    if st.button("← 返回中央大厅"): navigate_to('home')
    st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("<h2 style='text-align: center; margin-bottom: 30px;'>🎯 靶向词汇通关</h2>", unsafe_allow_html=True)
    
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    mode = st.radio("选择行动代号：", ["全局摸底考", "错题大扫除"], horizontal=True, key="mode_selector", on_change=reset_task_state)
    tiers = ["🌍 全库混合 (不分级)", "🟢 高频核心词汇", "🟡 中高频进阶词汇", "🟠 中频拓展词汇", "🔴 低频生僻词汇"]
    tier = st.selectbox("锁定目标层级：", tiers, key="tier_selector", on_change=reset_task_state)
    
    if st.session_state.current_user:
        st.session_state.quarantine_list = load_progress(st.session_state.current_user, mode, tier)
        
    st.write("<br>", unsafe_allow_html=True)
    col_start, col_reset = st.columns([3, 1])
    with col_start:
        if st.button("🚀 部署并继续任务", type="primary", use_container_width=True):
            get_next_word(mode, tier)
    with col_reset:
        if st.button("🔄 重置进度", use_container_width=True):
            save_progress(st.session_state.current_user, mode, tier, [])
            st.session_state.quarantine_list = []
            st.session_state.current_word = ""
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)
    
    # 【核心升级】：主进度条精准读取专属错题
    df_prog = pd.read_csv('words.csv')
    if 'frequency_tier' not in df_prog.columns: df_prog['frequency_tier'] = "🟢 高频核心词汇"
    if mode == "错题大扫除":
        wrong_dict = get_user_wrong_words(st.session_state.current_user)
        df_prog = df_prog[df_prog['word'].isin(wrong_dict.keys())]
    if tier != "🌍 全库混合 (不分级)": df_prog = df_prog[df_prog['frequency_tier'] == tier]
    total_round_words = len(df_prog)
    completed_words = len(st.session_state.quarantine_list)
    
    if total_round_words > 0:
        progress_ratio = min(completed_words / total_round_words, 1.0)
        st.progress(progress_ratio)
        total_answered = st.session_state.correct_count + st.session_state.wrong_count
        if total_answered > 0:
            acc = round(st.session_state.correct_count / total_answered * 100)
            st.markdown(f"<div style='text-align:center; font-size:0.9rem; margin-top:10px;'>节点肃清进度: <span class='text-highlight'>{completed_words}</span> / {total_round_words} &nbsp;|&nbsp; 准确率: <span class='text-success'>✅ {st.session_state.correct_count}</span> <span class='text-danger'>❌ {st.session_state.wrong_count}</span> &nbsp;({acc}%)</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div style='text-align:center; font-size:0.9rem; margin-top:10px;'>节点肃清进度: <span class='text-highlight'>{completed_words}</span> / {total_round_words}</div>", unsafe_allow_html=True)
    else:
        st.info("当前区域安全，无目标词汇。")

    if st.session_state.feedback:
        if "✨" in st.session_state.feedback: st.success(st.session_state.feedback)
        elif "恭喜" in st.session_state.feedback: 
            if st.session_state.get('show_balloons', False):
                st.balloons(); st.session_state.show_balloons = False
            st.success(st.session_state.feedback)
        else: st.error(st.session_state.feedback)
        
    if st.session_state.current_word:
        if st.session_state.perfect_hit:
            unique_id = str(time.time()).replace('.', '') 
            st.markdown(PERFECT_CSS_TEMPLATE.replace("UID", unique_id), unsafe_allow_html=True)
            st.session_state.perfect_hit = False 
            
        st.markdown(f"""
        <div style='text-align:center; margin: 20px 0; padding: 40px 20px; background: rgba(15,23,42,0.8); border-radius: 24px; border: 1px solid rgba(255,255,255,0.05); box-shadow: inset 0 0 20px rgba(0,0,0,0.5);'>
            <div style='font-size: 3rem; font-weight: 900; color: #f8fafc; margin-bottom: 10px;'>{st.session_state.chinese_meaning}</div>
            <div style='font-size: 1.2rem; color: #64748b; font-family: monospace;'>{st.session_state.phonetic}</div>
        </div>
        """, unsafe_allow_html=True)
        audio_url = f"https://dict.youdao.com/dictvoice?audio={st.session_state.current_word}&type=2"
        st.audio(audio_url, format="audio/mp3", autoplay=False)
        if st.session_state.options:
            st.markdown("<p style='text-align:center; color: #94a3b8; font-size: 0.85rem; margin-top: 15px;'>请选择正确拼写：</p>", unsafe_allow_html=True)
            labels = ['A', 'B', 'C', 'D', 'E', 'F']
            rows = [st.columns(3) for _ in range(2)]
            for i, word in enumerate(st.session_state.options):
                r, c = divmod(i, 3)
                label = labels[i] if i < len(labels) else str(i+1)
                if rows[r][c].button(f"{label}. {word}", key=f"opt_{i}_{word[:4]}", use_container_width=True):
                    check_answer(word)
        else:
            st.text_input(" ", key="user_input", on_change=check_answer, placeholder="在此输入拦截指令 (拼写)...", label_visibility="collapsed")

    # 【核心升级】：底部错题雷达现在只显示该用户自己的专属错题
    with st.expander("📡 展开专属错题雷达扫描结果", expanded=False):
        wrong_dict = get_user_wrong_words(st.session_state.current_user)
        if not wrong_dict: 
            st.write("雷达未发现高危词汇，错题本空空如也！")
        else:
            df_words = pd.read_csv('words.csv')
            df_wrong = df_words[df_words['word'].isin(wrong_dict.keys())].copy()
            df_wrong['wrong_count'] = df_wrong['word'].map(wrong_dict)
            df_wrong = df_wrong.sort_values(by='wrong_count', ascending=False)
            
            for _, row in df_wrong.iterrows():
                count = row['wrong_count']
                if count >= 5:
                    badge_color = '#ef4444'; badge_text = '🔴 高危'
                elif count >= 3:
                    badge_color = '#f59e0b'; badge_text = '🟡 注意'
                elif count >= 2:
                    badge_color = '#94a3b8'; badge_text = '🟠 观察'
                else:
                    badge_color = '#10b981'; badge_text = '🟢 轻微'
                st.markdown(f"<div style='background:rgba(0,0,0,0.3); padding:10px 15px; border-radius:12px; margin-bottom:8px; border-left: 4px solid {badge_color};'><b style='color:#e2e8f0;'>{row['word']}</b> <span style='color:#94a3b8; font-size:0.9rem; margin-left:10px;'>{row['definition']}</span><span style='float:right; color:{badge_color}; font-size:0.8rem; font-weight:bold;'>{badge_text} ×{count}</span></div>", unsafe_allow_html=True)

elif st.session_state.current_page == 'listening':
    st.markdown("<div class='glass-card' style='text-align:center; padding: 30px;'>", unsafe_allow_html=True)
    st.markdown("<h2 style='margin-bottom: 5px;'>🎧 听力训练营</h2>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    st.write("<br>", unsafe_allow_html=True)
    
    if st.button("🏠 返回大厅", key="back_from_listening", use_container_width=True):
        st.session_state.listening_test = None
        st.session_state.listening_q_index = 0
        st.session_state.listening_answers = {}
        st.session_state.listening_finished = False
        navigate_to('home')
    
    st.write("<br>", unsafe_allow_html=True)
    
    if os.path.exists('listening_tests.csv'):
        df_tests = pd.read_csv('listening_tests.csv')
        test_names = df_tests['test'].unique().tolist()
        
        if st.session_state.listening_test is None:
            st.markdown("<div class='glass-card' style='padding: 30px; text-align:center;'>", unsafe_allow_html=True)
            st.markdown("<h3>📋 选择试卷</h3>", unsafe_allow_html=True)
            st.write("<br>", unsafe_allow_html=True)
            for tname in test_names:
                df_t = df_tests[df_tests['test'] == tname]
                total_q = len(df_t)
                if st.button(f"📻 {tname}（共 {total_q} 题）", key=f"sel_{tname}", use_container_width=True):
                    st.session_state.listening_test = tname
                    st.session_state.listening_q_index = 0
                    st.session_state.listening_answers = {}
                    st.session_state.listening_finished = False
                    st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
            
            if st.session_state.is_admin:
                st.write("<br>", unsafe_allow_html=True)
                st.markdown("<div class='glass-card' style='padding: 20px; text-align:center;'>", unsafe_allow_html=True)
                st.markdown("<h4>📤 上传听力音频</h4>", unsafe_allow_html=True)
                uploaded_audio = st.file_uploader("上传 MP3 或 WAV 音频文件", type=["mp3", "wav"], key="audio_upload", label_visibility="collapsed")
                if uploaded_audio is not None:
                    os.makedirs('listening_audio', exist_ok=True)
                    file_path = os.path.join('listening_audio', uploaded_audio.name)
                    with open(file_path, 'wb') as f:
                        f.write(uploaded_audio.getvalue())
                    st.success(f"✅ {uploaded_audio.name} 上传成功！")
                st.markdown("</div>", unsafe_allow_html=True)
        else:
            df_test = df_tests[df_tests['test'] == st.session_state.listening_test].sort_values(by=['section', 'q_num'])
            total_q = len(df_test)
            current_idx = st.session_state.listening_q_index
            
            if st.session_state.listening_finished:
                correct_count = 0
                for idx, (_, row) in enumerate(df_test.iterrows()):
                    q_idx = str(idx)
                    if q_idx in st.session_state.listening_answers and st.session_state.listening_answers[q_idx] == row['answer']:
                        correct_count += 1
                score_pct = round(correct_count / total_q * 100)
                st.markdown("<div class='glass-card' style='padding: 40px; text-align:center;'>", unsafe_allow_html=True)
                st.markdown(f"<div style='font-size: 80px;'>📊</div>", unsafe_allow_html=True)
                if score_pct >= 90:
                    st.markdown(f"<h2 style='color: #22c55e;'>🎉 优秀！正确 {correct_count}/{total_q} ({score_pct}%)</h2>", unsafe_allow_html=True)
                elif score_pct >= 70:
                    st.markdown(f"<h2 style='color: #f59e0b;'>👍 良好！正确 {correct_count}/{total_q} ({score_pct}%)</h2>", unsafe_allow_html=True)
                elif score_pct >= 50:
                    st.markdown(f"<h2 style='color: #f97316;'>📚 及格！正确 {correct_count}/{total_q} ({score_pct}%)</h2>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<h2 style='color: #ef4444;'>💪 继续加油！正确 {correct_count}/{total_q} ({score_pct}%)</h2>", unsafe_allow_html=True)
                st.write("<br>", unsafe_allow_html=True)
                if st.button("🔄 重新答题", use_container_width=True):
                    st.session_state.listening_q_index = 0
                    st.session_state.listening_answers = {}
                    st.session_state.listening_finished = False
                    st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)
            else:
                row = df_test.iloc[current_idx]
                st.markdown("<div class='glass-card' style='padding: 30px;'>", unsafe_allow_html=True)
                st.markdown(f"<p style='color: #94a3b8; font-size: 0.85rem;'>Section: {row['section']} · 第 {row['q_num']} 题 / 共 {total_q} 题</p>", unsafe_allow_html=True)
                st.progress((current_idx) / total_q)
                st.write("<br>", unsafe_allow_html=True)
                
                audio_path = os.path.join('listening_audio', row['audio']) if pd.notna(row.get('audio', None)) else None
                if audio_path and os.path.exists(audio_path):
                    st.audio(audio_path, format="audio/mp3")
                    with st.expander("📝 点击查看对话原文", expanded=False):
                        st.markdown(f"<p style='color:#cbd5e1; line-height:1.8;'>{row['content']}</p>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<p style='color:#cbd5e1; line-height:1.8; background:rgba(0,0,0,0.3); padding:15px; border-radius:10px; margin-bottom:15px;'>{row['content']}</p>", unsafe_allow_html=True)
                    st.info("📂 管理员可上传音频文件，开启真实听力体验")
                
                st.markdown(f"<h4 style='color:#f8fafc; margin-top: 20px;'>{row['question']}</h4>", unsafe_allow_html=True)
                st.write("<br>", unsafe_allow_html=True)
                
                saved_answer = st.session_state.listening_answers.get(str(current_idx), None)
                available_opts = [l for l in ['A', 'B', 'C', 'D'] if l in row.index and pd.notna(row[l]) and str(row[l]).strip() != '']
                for opt_letter in available_opts:
                    opt_text = row[opt_letter]
                    is_selected = (saved_answer == opt_letter)
                    btn_label = f"{'✅ ' if is_selected else ''}{opt_letter}. {opt_text}"
                    btn_style = "primary" if is_selected else "secondary"
                    if st.button(btn_label, key=f"lq_{current_idx}_{opt_letter}", use_container_width=True, type=btn_style):
                        st.session_state.listening_answers[str(current_idx)] = opt_letter
                        st.rerun()
                
                st.write("<br>", unsafe_allow_html=True)
                col_prev, col_next = st.columns(2)
                with col_prev:
                    if current_idx > 0:
                        if st.button("⬅ 上一题", use_container_width=True):
                            st.session_state.listening_q_index -= 1
                            st.rerun()
                with col_next:
                    next_label = "交卷 📋" if current_idx == total_q - 1 else "下一题 ➡"
                    if st.button(next_label, use_container_width=True):
                        if current_idx < total_q - 1:
                            st.session_state.listening_q_index += 1
                            st.rerun()
                        else:
                            st.session_state.listening_finished = True
                            st.rerun()
                
                st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.error("未找到听力题库文件。")

elif st.session_state.current_page == 'continuation':
    st.markdown("<div class='back-btn'>", unsafe_allow_html=True)
    if st.button("← 返回中央大厅"): navigate_to('home')
    st.markdown("</div>", unsafe_allow_html=True)

    if st.session_state.drill_mode is not None:
        st.markdown("<h2 style='text-align: center; margin-bottom: 20px;'>✍️ 情境造句训练场</h2>", unsafe_allow_html=True)
        TECHNIQUES = ['全部技法', '评价判断法', '环境同步法', '动作中断法', '内心矛盾法', '时间压力法', '万能衔接', '主题升华']
        TECH_DESC = {
            '评价判断法': '对前文行动给予评价，直接转折或深化情节',
            '环境同步法': '让外部环境与人物的内心或事件进展产生互动',
            '动作中断法': '在连贯动作中插入因素，使情节转向',
            '内心矛盾法': '将人物内心斗争写成两个声音或选择',
            '时间压力法': '引入时间限制或紧迫后果，迫使人物行动',
            '万能衔接': '四步法中的衔接句：首句承上，段尾启下',
            '主题升华': '最后一句提炼主题，力争呼应标题',
        }

        def reset_drill():
            st.session_state.drill_mode = None
            st.session_state.drill_q_idx = 0
            st.session_state.drill_user_answer = ''
            st.session_state.drill_ai_question = None
            st.session_state.drill_ai_feedback = None
            st.session_state.drill_correct = 0
            st.session_state.drill_total = 0
            st.session_state.drill_technique = '全部技法'

        if st.button("← 返回宝典首页", key="drill_back_home", use_container_width=True):
            reset_drill()

        st.write("<br>", unsafe_allow_html=True)

        is_ai_mode = (st.session_state.drill_mode == 'ai')

        col_t1, col_t2 = st.columns([1.5, 2.5])
        with col_t1:
            prev_tech = st.session_state.drill_technique
            st.session_state.drill_technique = st.selectbox("选择技法", TECHNIQUES, index=TECHNIQUES.index(prev_tech) if prev_tech in TECHNIQUES else 0)
            if st.session_state.drill_technique != prev_tech:
                st.session_state.drill_q_idx = 0
                st.session_state.drill_ai_question = None
                st.session_state.drill_ai_feedback = None
                st.session_state.drill_user_answer = ''
        with col_t2:
            if st.session_state.drill_technique != '全部技法':
                st.caption(TECH_DESC.get(st.session_state.drill_technique, ''))

        if is_ai_mode:
            if st.session_state.drill_ai_question is None:
                st.markdown("<div class='glass-card' style='text-align:center; padding: 40px 30px;'>", unsafe_allow_html=True)
                st.markdown("<p style='color:#94a3b8; font-size:1rem;'>AI 将根据你选择的技法生成一道全新的情境造句题</p>", unsafe_allow_html=True)
                st.write("<br>", unsafe_allow_html=True)
                if st.button("🎲 AI 出题 (消耗 1 点算力)", type="primary", use_container_width=True):
                    cur_credits = get_user_credits(st.session_state.current_user)
                    if cur_credits <= 0:
                        st.error("算力不足！请返回首页申请额度")
                    else:
                        with st.spinner("🧠 AI 正在构思情境..."):
                            try:
                                client = OpenAI(api_key=get_secret("DEEPSEEK_API_KEY"), base_url="https://api.deepseek.com")
                                tech_filter = "" if st.session_state.drill_technique == '全部技法' else f"请严格使用「{st.session_state.drill_technique}」这一技法。"
                                prompt = f"""你是高考英语读后续写的命题专家。请根据以下技法生成一道情境造句训练题。

{tech_filter}

【可用的叙事技法说明】：
1. 评价判断法：对前文行动给予评价句，如 "This turned out to be..." "Little did I know..." "That decision would change everything."
2. 环境同步法：外部环境与人物内心互动，如 "Just as she was about to give up, a ray of sunlight broke through..."
3. 动作中断法：在动作中插入因素使情节转向，如 "He reached for the bread. But his eyes caught the photo on the wall..."
4. 内心矛盾法：写成两个声音的斗争，如 "A part of me screamed to run away. But a stronger part kept my feet on the ground."
5. 时间压力法：引入时间限制，如 "Looking at his watch, he realized he had only ten minutes..."
6. 万能衔接：承上启下的过渡句，如 "Seeing a sign glowing down the street, I knew we needed..."
7. 主题升华：结尾提炼主题，如 "Sometimes, a collision doesn't create wreckage, but an opening for kindness."

【输出格式 — 严格 JSON】：
```json
{{
    "scenario": "用中文写一段情境描述（1-2句话，营造画面感）",
    "template": "用英文写一句含填空的半成品句子，留空处用 _____ 表示（可以是词或短语的填空）",
    "answer": "template 的完整版英文句子",
    "technique_note": "用中文简要说明此句运用了什么技法（10字以内）"
}}
```

【要求】：
- scenario 要具体、有画面感，贴合高考续写真题风格
- template 中的 _____ 必须是关键技法词/短语，学生需要补充核心部分
- answer 必须语法正确、地道自然
- 只输出 JSON，不要其他文字"""
                                response = client.chat.completions.create(
                                    model="deepseek-chat",
                                    messages=[{"role": "system", "content": "你是一位高考英语命题专家，严格按 JSON 格式输出。"}, {"role": "user", "content": prompt}],
                                    temperature=0.9
                                )
                                raw = response.choices[0].message.content
                                json_match = re.search(r'```json\s*([\s\S]*?)\s*```', raw)
                                data = json.loads(json_match.group(1) if json_match else raw)
                                st.session_state.drill_ai_question = data
                                st.session_state.drill_ai_feedback = None
                                st.session_state.drill_user_answer = ''
                                deduct_credit(st.session_state.current_user)
                                st.rerun()
                            except Exception as e:
                                st.error(f"AI 出题失败：{e}")
                st.markdown("</div>", unsafe_allow_html=True)
            else:
                q = st.session_state.drill_ai_question
                st.markdown("<div class='glass-card' style='padding: 24px 28px;'>", unsafe_allow_html=True)
                if st.session_state.drill_technique == '全部技法' and q.get('technique_note'):
                    st.caption(f"🎯 {q['technique_note']}")
                st.markdown(f"<p style='color:#f59e0b; font-weight:600; margin-bottom:6px;'>📖 情境：</p><p style='color:#f1f5f9; font-size:1.05rem; line-height:1.8;'>{q['scenario']}</p>", unsafe_allow_html=True)
                st.write("<br>", unsafe_allow_html=True)
                st.markdown(f"<p style='color:#60a5fa; font-weight:600; margin-bottom:6px;'>✍️ 请补全：</p><p style='color:#e2e8f0; font-size:1rem; font-family:Georgia,serif; line-height:1.8; background:rgba(0,0,0,0.25); padding:14px 18px; border-radius:10px;'>{q['template']}</p>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

                st.write("<br>", unsafe_allow_html=True)
                st.session_state.drill_user_answer = st.text_area("你的答案", key="drill_ai_input", value=st.session_state.drill_user_answer, height=100, placeholder="在此输入你补全的英文句子...", label_visibility="collapsed")
                col_submit, col_newq = st.columns(2)
                with col_submit:
                    if st.button("📝 AI 批改 (消耗 1 点算力)", type="primary", use_container_width=True, disabled=not st.session_state.drill_user_answer.strip()):
                        cur_credits = get_user_credits(st.session_state.current_user)
                        if cur_credits <= 0:
                            st.error("算力不足！请返回首页申请额度")
                        else:
                            with st.spinner("🧠 AI 正在批改..."):
                                try:
                                    client = OpenAI(api_key=get_secret("DEEPSEEK_API_KEY"), base_url="https://api.deepseek.com")
                                    grading_prompt = f"""你是高考英语阅卷老师。请批改学生的情境造句。

【题目】
情境：{q['scenario']}
英文模板：{q['template']}
标准答案：{q['answer']}

【学生答案】
{st.session_state.drill_user_answer}

【输出格式 — 严格 JSON】：
```json
{{
    "score": "给一个 0-10 的评分（整数）",
    "feedback": "用中文写 1-2 句评语，指出优点和问题",
    "correction": "如果需要修正，给出修正后的完整句子；如果已经很好，写 '无需修改'"
}}
```

只输出 JSON，不要其他文字。"""
                                    response = client.chat.completions.create(
                                        model="deepseek-chat",
                                        messages=[{"role": "system", "content": "你是一位严格但公正的高考英语阅卷老师。"}, {"role": "user", "content": grading_prompt}],
                                        temperature=0.3
                                    )
                                    raw = response.choices[0].message.content
                                    json_match = re.search(r'```json\s*([\s\S]*?)\s*```', raw)
                                    result = json.loads(json_match.group(1) if json_match else raw)
                                    st.session_state.drill_ai_feedback = result
                                    st.session_state.drill_total += 1
                                    if int(result.get('score', 0)) >= 6:
                                        st.session_state.drill_correct += 1
                                    deduct_credit(st.session_state.current_user)
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"AI 批改失败：{e}")
                with col_newq:
                    if st.button("🎲 换一题", use_container_width=True):
                        st.session_state.drill_ai_question = None
                        st.session_state.drill_ai_feedback = None
                        st.session_state.drill_user_answer = ''
                        st.rerun()

                if st.session_state.drill_ai_feedback:
                    fb = st.session_state.drill_ai_feedback
                    score = int(fb.get('score', 0))
                    score_color = '#22c55e' if score >= 8 else '#f59e0b' if score >= 6 else '#ef4444'
                    st.write("<br>", unsafe_allow_html=True)
                    st.markdown(f"<div class='glass-card' style='border-top: 4px solid {score_color}; padding: 20px 24px;'>", unsafe_allow_html=True)
                    st.markdown(f"<h3 style='color:{score_color}; margin-top:0;'>📊 AI 评分：{score}/10</h3>", unsafe_allow_html=True)
                    st.markdown(f"<p style='color:#e2e8f0; line-height:1.7;'>{fb.get('feedback', '')}</p>", unsafe_allow_html=True)
                    corr = fb.get('correction', '')
                    if corr and corr != '无需修改':
                        st.markdown(f"<p style='color:#60a5fa; font-weight:600; margin-top:12px;'>✅ 修正版：</p><p style='color:#f1f5f9; background:rgba(0,0,0,0.3); padding:10px 16px; border-radius:8px; font-family:Georgia,serif;'>{corr}</p>", unsafe_allow_html=True)
                    st.markdown(f"<p style='color:#94a3b8; margin-top:12px;'>💡 标准答案：<span style='color:#10b981; font-family:Georgia,serif;'>{q['answer']}</span></p>", unsafe_allow_html=True)
                    st.markdown("<p style='color:#64748b; font-size:0.8rem; margin-top:8px;'>🎯 " + q.get('technique_note', '') + "</p>", unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)

        else:
            if os.path.exists('continuation_drills.csv'):
                df_drills = pd.read_csv('continuation_drills.csv')
                tech_filter = st.session_state.drill_technique
                if tech_filter != '全部技法':
                    df_drills = df_drills[df_drills['technique'] == tech_filter]
                if len(df_drills) == 0:
                    st.info("该技法暂无题库，试试「全部技法」或切换技法")
                else:
                    q_idx = st.session_state.drill_q_idx % len(df_drills)
                    row = df_drills.iloc[q_idx]
                    st.markdown("<div class='glass-card' style='padding: 24px 28px;'>", unsafe_allow_html=True)
                    st.caption(f"🎯 {row['technique']}")
                    st.markdown(f"<p style='color:#f59e0b; font-weight:600; margin-bottom:6px;'>📖 情境：</p><p style='color:#f1f5f9; font-size:1.05rem; line-height:1.8;'>{row['scenario']}</p>", unsafe_allow_html=True)
                    st.write("<br>", unsafe_allow_html=True)
                    st.markdown(f"<p style='color:#60a5fa; font-weight:600; margin-bottom:6px;'>✍️ 请补全：</p><p style='color:#e2e8f0; font-size:1rem; font-family:Georgia,serif; line-height:1.8; background:rgba(0,0,0,0.25); padding:14px 18px; border-radius:10px;'>{row['template']}</p>", unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)

                    st.write("<br>", unsafe_allow_html=True)
                    if 'classic_show_answer' not in st.session_state:
                        st.session_state.classic_show_answer = False
                    user_ans = st.text_area("你的答案", key="drill_classic_input", height=100, placeholder="在此输入你补全的英文句子...", label_visibility="collapsed")
                    col_chk, col_nxt = st.columns(2)
                    with col_chk:
                        if st.button("✅ 查看答案", use_container_width=True, disabled=not user_ans.strip()):
                            st.session_state.classic_show_answer = True
                            st.session_state.drill_total += 1
                    with col_nxt:
                        def next_classic_q():
                            st.session_state.drill_q_idx = (st.session_state.drill_q_idx + 1) % len(df_drills)
                            st.session_state.classic_show_answer = False
                        st.button("➡ 下一题", key="drill_next_btn", on_click=next_classic_q, use_container_width=True)

                    if st.session_state.classic_show_answer:
                        st.write("<br>", unsafe_allow_html=True)
                        st.markdown("<div class='glass-card' style='border-top: 4px solid #22c55e; padding: 20px 24px;'>", unsafe_allow_html=True)
                        st.markdown(f"<p style='color:#10b981; font-weight:600;'>✅ 标准答案：</p><p style='color:#f1f5f9; font-family:Georgia,serif; line-height:1.8;'>{row['answer']}</p>", unsafe_allow_html=True)
                        st.markdown(f"<p style='color:#64748b; font-size:0.85rem; margin-top:8px;'>💡 {row['tip']}</p>", unsafe_allow_html=True)
                        st.markdown("</div>", unsafe_allow_html=True)
            else:
                st.error("题库文件缺失")

        st.write("<br>", unsafe_allow_html=True)
        if st.session_state.drill_total > 0:
            acc = round(st.session_state.drill_correct / st.session_state.drill_total * 100) if st.session_state.drill_total > 0 else 0
            st.markdown(f"<p style='text-align:center; color:#94a3b8; font-size:0.85rem;'>本次训练：{st.session_state.drill_total} 题 | 通过率 {acc}%</p>", unsafe_allow_html=True)

    else:
        st.markdown("<h2 style='text-align: center; margin-bottom: 20px;'>📖 读后续写 · 巅峰之作</h2>", unsafe_allow_html=True)

        LECTURES = [
            ("第一讲", "情节构思与实战", 7),
            ("第二讲", "情节构思进阶", 8),
            ("第三讲", "综合实战演练", 68),
            ("第四讲", "描写技法精讲", 48),
            ("第五讲", "情节构思原则+实战", 8),
        ]

        def open_lecture(lidx):
            st.session_state.continuation_lecture = lidx
            st.session_state.continuation_page_idx = 0

        def go_prev():
            st.session_state.continuation_page_idx -= 1

        def go_next():
            st.session_state.continuation_page_idx += 1

        def back_to_catalog():
            st.session_state.continuation_lecture = None
            st.session_state.continuation_page_idx = 0

        if st.session_state.continuation_lecture is None:
            st.write("<br>", unsafe_allow_html=True)
            st.markdown("<p style='text-align:center; color:#94a3b8; font-size:0.9rem;'>👇 选择一讲开始阅读</p>", unsafe_allow_html=True)
            st.write("<br>", unsafe_allow_html=True)
            for lidx, (lname, ldesc, lpages) in enumerate(LECTURES):
                icon = "📝" if lidx == 4 else "📷"
                label = f"{icon} {lname} · {ldesc} ({lpages} 页)"
                st.markdown(f"<div class='glass-card' style='text-align:center; padding: 18px 24px; margin-bottom: 12px;'>", unsafe_allow_html=True)
                st.button(label, key=f"sel_lec_{lidx}", on_click=open_lecture, args=(lidx,), use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)

            st.markdown("<hr style='margin: 28px 0; border-color: rgba(255,255,255,0.08);'>", unsafe_allow_html=True)
            st.markdown("<p style='text-align:center; color:#94a3b8; font-size:0.9rem;'>👇 或者进入训练模式</p>", unsafe_allow_html=True)
            st.write("<br>", unsafe_allow_html=True)
            col_d1, col_d2 = st.columns(2)
            with col_d1:
                st.markdown("<div class='glass-card' style='text-align:center; padding: 20px;'>", unsafe_allow_html=True)
                st.markdown("<div style='font-size:40px;'>📋</div>", unsafe_allow_html=True)
                st.markdown("<h4>经典题库</h4>", unsafe_allow_html=True)
                st.markdown("<p style='font-size:0.8rem; color:#94a3b8;'>25 道精选情境造句题<br>不消耗算力，随时练习</p>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)
                if st.button("进入经典题库 →", key="go_classic", use_container_width=True):
                    st.session_state.drill_mode = 'classic'
                    st.rerun()
            with col_d2:
                st.markdown("<div class='glass-card' style='text-align:center; padding: 20px;'>", unsafe_allow_html=True)
                st.markdown("<div style='font-size:40px;'>🤖</div>", unsafe_allow_html=True)
                st.markdown("<h4>AI 智能出题</h4>", unsafe_allow_html=True)
                st.markdown("<p style='font-size:0.8rem; color:#94a3b8;'>AI 随机生成新题 + 批改<br>每题消耗 2 点算力</p>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)
                if st.button("进入 AI 出题 →", key="go_ai", use_container_width=True):
                    st.session_state.drill_mode = 'ai'
                    st.rerun()
        else:
            lidx = st.session_state.continuation_lecture
            lname, ldesc, lpages = LECTURES[lidx]
            is_text = (lidx == 4)

            st.markdown(f"<div class='glass-card' style='text-align:center; padding: 14px 20px; margin-bottom: 16px;'>", unsafe_allow_html=True)
            st.markdown(f"<p style='color:#94a3b8; font-size:0.8rem; margin:0;'>📖 {lname} · {ldesc} ({lpages} 页)</p>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

            pg = st.session_state.continuation_page_idx

            if is_text:
                txt_path = "extension_writing_l5.txt"
                if os.path.exists(txt_path):
                    with open(txt_path, "r", encoding="utf-8") as f:
                        raw = f.read()
                    chunks = raw.split("\n\n")
                    if pg < len(chunks):
                        st.markdown(f"<div class='glass-card' style='padding: 24px 28px; line-height: 1.9; font-size: 0.95rem; color: #e2e8f0;'>{chunks[pg].replace(chr(10), '<br>')}</div>", unsafe_allow_html=True)
                    else:
                        st.info("本讲已读完 ✅")
                    total = max(len(chunks) - 1, 1)
                else:
                    st.error("第五讲文字文件缺失")
                    total = lpages
            else:
                folder = os.path.join("continuation_writing", lname)
                img_name = f"p{pg+1:03d}.png"
                img_path = os.path.join(folder, img_name)
                if os.path.exists(img_path):
                    st.image(img_path, use_container_width=True)
                else:
                    st.info(f"第 {pg+1} 页暂无图片")
                total = lpages

            st.write("<br>", unsafe_allow_html=True)
            col_prev, col_sel, col_next = st.columns([1, 2, 1])
            with col_prev:
                if pg > 0:
                    st.button("⬅ 上一页", key="cont_prev", on_click=go_prev, use_container_width=True)
            with col_sel:
                st.markdown(f"<p style='text-align:center; color:#94a3b8; line-height:2.5;'>{pg+1} / {total}</p>", unsafe_allow_html=True)
            with col_next:
                if pg < total - 1:
                    st.button("下一页 ➡", key="cont_next", on_click=go_next, use_container_width=True)

            st.write("<br>", unsafe_allow_html=True)
            col_back, _ = st.columns([1, 3])
            with col_back:
                st.button("📚 返回目录", key="cont_back", on_click=back_to_catalog, use_container_width=True)

elif st.session_state.current_page == 'essay':
    st.session_state.user_credits = get_user_credits(st.session_state.current_user)
    st.markdown("<div class='back-btn'>", unsafe_allow_html=True)
    if st.button("← 返回中央大厅"): navigate_to('home')
    st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("<h2 style='text-align: center; margin-bottom: 15px;'>✍️ 高考文书锻造工坊</h2>", unsafe_allow_html=True)

    roadmap = get_roadmap(st.session_state.current_user)
    if roadmap:
        total_items = sum(len(v) for v in roadmap.values())
        with st.expander(f"🗺️ 我的学习路线 ({total_items} 条待学习)", expanded=False):
            CAT_ICONS_R = {"词汇升级": ("📝", "#f59e0b"), "句型升级": ("🏗️", "#3b82f6"), "语法强化": ("🔧", "#ef4444"), "衔接优化": ("🔗", "#10b981")}
            for cat, items in roadmap.items():
                icon, color = CAT_ICONS_R.get(cat, ("📌", "#94a3b8"))
                st.markdown(f"<p style='font-weight:700; color:{color}; margin-bottom:4px;'>{icon} {cat}（{len(items)}）</p>", unsafe_allow_html=True)
                for itm in items:
                    st.markdown(f"<div style='background:rgba(0,0,0,0.2); padding:6px 12px; border-radius:6px; margin-bottom:5px; margin-left:8px; border-left:3px solid {color}; font-size:0.85rem; color:#cbd5e1;'>{itm}</div>", unsafe_allow_html=True)
            _, col_reset = st.columns([5, 1])
            with col_reset:
                if st.button("🗑️ 清空路线", key="clear_roadmap_essay", use_container_width=True):
                    clear_roadmap(st.session_state.current_user)
                    st.rerun()
    else:
        with st.expander("🗺️ 我的学习路线（暂无）", expanded=False):
            st.caption("提交作文批改后，AI 会为你生成专属学习路线")

    with st.container():
        st.markdown("<p style='color: #94a3b8; font-size: 0.85rem; margin-bottom: 5px;'>📋 作文题目（中文）：</p>", unsafe_allow_html=True)
        st.text_area(" ", height=80, key="essay_topic", placeholder="例如：假定你是李华，你的英国朋友Peter来信询问你校学生体育运动情况。请给他回信...", label_visibility="collapsed")
        with st.expander("📸 拍照识别题目", expanded=False):
            topic_img = st.file_uploader("📷 拍照或选择图片", type=["jpg", "jpeg", "png"], key="ocr_topic", label_visibility="collapsed")
            if topic_img is not None:
                st.image(topic_img, width=300)
                if st.button("🔍 识别题目文字", key="btn_topic", use_container_width=True):
                    with st.spinner("AI 正在识别题目文字..."):
                        topic_ocr_text, topic_ocr_error = baidu_ocr(topic_img.getvalue())
                    if topic_ocr_error:
                        st.error(topic_ocr_error)
                    else:
                        st.session_state.essay_topic = topic_ocr_text
                        st.success(f"识别完成！已自动填入上方题目栏")
                        st.rerun()
        st.write("<br>", unsafe_allow_html=True)
        with st.expander("📸 拍照识别作文", expanded=False):
            ocr_image = st.file_uploader("📷 拍照或选择图片", type=["jpg", "jpeg", "png"], key="ocr_essay", label_visibility="collapsed")
            if ocr_image is not None:
                st.image(ocr_image, width=300)
                if st.button("🔍 识别作文文字", key="btn_essay", use_container_width=True):
                    with st.spinner("AI 正在识别作文文字..."):
                        ocr_text, ocr_error = baidu_ocr(ocr_image.getvalue())
                    if ocr_error:
                        st.error(ocr_error)
                    else:
                        st.session_state.essay_draft = ocr_text
                        st.success(f"识别完成！共 {len(ocr_text)} 个字符，已自动填入下方作文栏")
                        st.rerun()
        st.markdown("<p style='color: #94a3b8; font-size: 0.85rem; margin-bottom: 5px;'>📝 你的英文作文：</p>", unsafe_allow_html=True)
        st.text_area(" ", height=250, key="essay_draft", placeholder="在此输入你的英文草稿...", label_visibility="collapsed")
        
        st.write("<br>", unsafe_allow_html=True)
        col_scan, col_ai, col_clear = st.columns([2, 2, 1])
        with col_scan:
            scan_btn = st.button("🔍 弱点词汇扫描", use_container_width=True)
        with col_ai:
            ai_btn = st.button("🤖 召唤 DeepSeek 导师", type="primary", use_container_width=True)
        with col_clear:
            if st.button("🗑️ 清空", use_container_width=True): st.session_state.essay_draft = ""; st.session_state.essay_topic = ""; st.rerun()
            
        if scan_btn and st.session_state.essay_draft.strip():
            draft_text = st.session_state.essay_draft.lower()
            df_upgrade = pd.read_csv('upgrade.csv')
            found_words = []
            for _, row in df_upgrade.iterrows():
                basic_word = row['basic']
                if re.search(r'\b' + re.escape(basic_word) + r'\b', draft_text): found_words.append(row)
            if not found_words: st.success("雷达未发现低级词汇，文笔坚固！")
            else:
                st.warning(f"⚠️ 发现 {len(found_words)} 处可替换装甲：")
                for item in found_words:
                    st.markdown(f"<div style='background: rgba(0,0,0,0.3); padding: 15px; border-radius: 12px; border-left: 4px solid #f59e0b; margin-bottom: 10px;'><span style='color: #94a3b8; text-decoration: line-through;'>{item['basic']}</span> <span style='margin: 0 10px;'>👉</span> <span class='text-success' style='font-weight: 900; font-size: 1.1rem;'>{item['advanced']}</span><div style='font-size: 0.85rem; color: #64748b; margin-top: 5px;'>{item['reason']}</div></div>", unsafe_allow_html=True)
        
        if ai_btn and st.session_state.essay_draft.strip():
            current_time = time.time()
            COOLDOWN_SECONDS = 30
            has_credits = st.session_state.user_credits > 0 
            
            st.markdown("<p style='font-size:0.85rem; color:#64748b; margin-top:10px;'>*若无系统算力额度，请在此输入私人 Key</p>", unsafe_allow_html=True)
            user_api_key = st.text_input("DeepSeek Key:", type="password", label_visibility="collapsed")
            
            if current_time - st.session_state.last_ai_time < COOLDOWN_SECONDS:
                st.warning(f"引擎冷却中：请等待 {int(COOLDOWN_SECONDS - (current_time - st.session_state.last_ai_time))} 秒。")
            elif not has_credits and not user_api_key:
                st.error("🛑 系统配额已耗尽。你可以返回首页向管理员申请补充额度，或在此输入私人 Key。")
                if st.button("📩 去申请额度", key="goto_req_credits", use_container_width=True):
                    navigate_to('home')
            else:
                with st.spinner("🧠 神经元网络正在解构你的文章..."):
                    try:
                        active_api_key = user_api_key if user_api_key else get_secret("DEEPSEEK_API_KEY")
                        if not active_api_key: st.error("未检测到 API 密钥，连接中断。")
                        else:
                            client = OpenAI(api_key=active_api_key, base_url="https://api.deepseek.com")
                            prompt = f"""
                            你现在是【浙江省高考英语阅卷组长】，极其严厉、专业且毒舌。你的任务是对下面这篇 80 词左右的高考应用文草稿进行降维打击式的批改。
                            
                            【本次作文题目（中文）】：
                            {st.session_state.essay_topic if st.session_state.essay_topic.strip() else '（学生未提供题目）'}

                            【浙江卷评分标准（满分 15 分）—— 五大维度对照表】：
                            | 档次 | 分数 | 内容覆盖度 | 词汇水平 | 语法复杂度 | 逻辑与衔接 |
                            |------|------|-----------|---------|-----------|-----------|
                            | 五档 | 13-15 | 全覆盖所有要点，细节充实 | 地道高级词汇≥5个，精准无废词 | 熟练运用倒装/强调/非谓语/从句等≥3类高级结构 | 衔接丝滑，段落浑然一体 |
                            | 四档 | 10-12 | 覆盖主要要点(≥80%) | 词汇基本准确，偶用高级词 | 有少量复合句，尝试使用高级语法 | 基础连贯，有过渡词 |
                            | 三档 | 7-9 | 漏掉1-2个要点 | 词汇单一重复，口语化严重 | 多为简单句，偶有从句 | 衔接生硬，跳脱感明显 |
                            | 二档 | 4-6 | 要点缺失严重(≤50%) | 大量基础词汇错误 | 几乎全是简单句 | 逻辑混乱，前言不搭后语 |
                            | 一档 | 0-3 | 完全离题或未完成 | 词不达意 | 无完整句子 | 无法阅读 |
                            
                            【🛑 零分红线 — 遇到以下情况直接打 0 分，不要犹豫】：
                            - 字数极少（少于 20 个词）
                            - 只写了两三句话敷衍了事
                            - 照抄题目原文或前面的阅读理解段落
                            - 完全空白或用中文胡乱应付
                            
                            - **重要**：请根据上方作文题目判断学生是否覆盖了所有题目要点，要点遗漏必须扣分！

                            【执行工作流（严格按此结构输出）】：

                            ### 📊 一、判卷定档
                            - **预估总分**：X/15
                            - **定档理由**：一针见血地指出为什么给这个分数。**必须对照上方的作文题目要求**，指明哪些要点覆盖了、哪些遗漏了。

                            ### 📊 二、分项得分明细
                            | 评分维度 | 满分 | 实际得分 | 扣分原因 |
                            |---------|------|---------|---------|
                            | 内容要点覆盖 | 5 | X | （一句说清） |
                            | 词汇丰富与精准 | 4 | X | （一句说清） |
                            | 语法结构水平 | 3 | X | （一句说清） |
                            | 逻辑连贯与衔接 | 2 | X | （一句说清） |
                            | 格式与书写规范 | 1 | X | （一句说清） |

                            ### 👨‍🏫 三、阅卷组长毒舌手记
                            （用 2-3 句辛辣的、像高三老师骂人一样的语气，直击这篇文章最致命的死穴。不要假客气，越毒越好。）

                            ### 🔪 四、致命雷区排查
                            （如果没有错误，此项可写"基础尚可，无致命语法硬伤"。如果有，请逐项列出：）
                            - 找出所有的时态错误、主谓不一致、中式英语（Chinglish）、拼写错误、以及烂大街的低级词汇。
                            - 格式：`原句错误` ❌ → `诊断说明`。

                            ### 💎 五、满分升格示范 (The Masterpiece)
                            这是你的核心任务！请在保持学生原意的前提下，重写这篇应用文。**必须严格贴合上方的作文题目要求**。
                            - 必须使用至少 2 个高级句型（如：倒装句、强调句、非谓语动词作状语/定语、复合从句）。
                            - 必须使用地道的高级词汇替换掉平庸词汇。
                            - 句与句之间必须有符合逻辑的高级衔接词（如：what is more, consequently, nevertheless）。
                            - 请将你使用的**高级语法和亮眼词汇**加粗显示，并在段落下方用 💡 逐条简要批注你改动的绝妙之处。

                            ### 📖 六、低级词汇升格速查表
                            从学生草稿中挑出 3-5 个可以升级的低级词汇，列成表格：
                            | 学生原词 ❌ | 升格替换 ✅ | 升格理由 |
                            |-----------|-----------|---------|
                            | （原词） | （高阶词） | （一句话） |

                            ### 🗺️ 七、个性化学习路线 (JSON)
                            根据学生在本次作文中暴露出的具体弱点，生成一份定制化学习路线。你必须输出一个严格的 JSON 数组（不要有任何其他文字），格式如下：
                            ```json
                            [
                                {{"category": "词汇升级", "item": "将 'happy' 替换为 'delighted / thrilled'"}},
                                {{"category": "句型升级", "item": "学习强调句：It is ... that ..."}},
                                {{"category": "语法强化", "item": "主谓一致：主语是第三人称单数时动词要加 s"}},
                                {{"category": "衔接优化", "item": "用 'What is more' 代替 'And' 来连接段落"}}
                            ]
                            ```
                            要求：
                            - 类别只能是以下四种之一：`词汇升级`、`句型升级`、`语法强化`、`衔接优化`
                            - 每条 item 要具体到学生作文中的真实错误，不能泛泛而谈
                            - 至少输出 3 条，最多 6 条
                            - 必须严格输出 JSON 代码块，方便系统解析

                            【学生草稿】：
                            {st.session_state.essay_draft}
                            """
                            response = client.chat.completions.create(
                                model="deepseek-chat",
                                messages=[{"role": "system", "content": "你是一位负责、专业且要求极高的高考英语名师。"},{"role": "user", "content": prompt}],
                                temperature=0.7 
                            )
                            ai_feedback = response.choices[0].message.content
                            
                            roadmap_items = []
                            try:
                                json_match = re.search(r'```json\s*([\s\S]*?)\s*```', ai_feedback)
                                if json_match:
                                    roadmap_data = json.loads(json_match.group(1))
                                    for entry in roadmap_data:
                                        cat = entry.get("category", "").strip()
                                        itm = entry.get("item", "").strip()
                                        if cat and itm:
                                            add_roadmap_item(st.session_state.current_user, cat, itm)
                                            roadmap_items.append((cat, itm))
                            except Exception:
                                pass
                            
                            if not user_api_key:
                                new_creds = deduct_credit(st.session_state.current_user)
                                st.session_state.user_credits = new_creds 
                            
                            st.session_state.last_ai_time = time.time()
                            st.success("数据传输完成！")
                            st.markdown(f"""
                            <div class='glass-card' style='border-top: 4px solid #3b82f6; margin-top: 30px;'>
                                <h3 style='color: #60a5fa; margin-top: 0; margin-bottom: 20px;'>🤖 导师协议执行报告</h3>
                                <div style='font-size: 1rem; line-height: 1.8; color: #e2e8f0;'>
                                    {ai_feedback}
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                            if roadmap_items:
                                st.markdown("<div class='glass-card' style='border-top: 4px solid #f59e0b; margin-top: 20px;'>", unsafe_allow_html=True)
                                st.markdown("<h4 style='color: #f59e0b; margin-top: 0;'>🗺️ 你的专属学习路线已更新</h4>", unsafe_allow_html=True)
                                CAT_ICONS = {"词汇升级": "📝", "句型升级": "🏗️", "语法强化": "🔧", "衔接优化": "🔗"}
                                for cat, itm in roadmap_items:
                                    icon = CAT_ICONS.get(cat, "📌")
                                    st.markdown(f"<div style='background:rgba(0,0,0,0.3); padding:10px 15px; border-radius:10px; margin-bottom:8px; border-left:3px solid #f59e0b;'><span style='font-size:0.85rem; color:#f59e0b; font-weight:600;'>{icon} {cat}</span><br><span style='color:#e2e8f0;'>{itm}</span></div>", unsafe_allow_html=True)
                                st.caption("💡 所有路线已保存，返回首页可随时查看你的完整学习计划")
                                st.markdown("</div>", unsafe_allow_html=True)
                    except Exception as e: st.error(f"❌ 神经元连接失败：{e}")
                    
    st.markdown("<h4 style='margin-top: 40px; margin-bottom: 20px;'>📚 模块化组件库</h4>", unsafe_allow_html=True)
    df_essays = pd.read_csv('essays.csv')
    categories = list(df_essays['category'].unique())
    tabs = st.tabs(categories)
    for i, cat in enumerate(categories):
        with tabs[i]:
            cat_data = df_essays[df_essays['category'] == cat]
            subcats = cat_data['subcategory'].unique()
            for sub in subcats:
                st.markdown(f"<p class='text-highlight' style='font-weight: 700; margin-top: 15px;'>• {sub}</p>", unsafe_allow_html=True)
                sub_data = cat_data[cat_data['subcategory'] == sub]
                for idx, row in sub_data.iterrows():
                    with st.container():
                        st.markdown(f"""
                        <div style='background: rgba(0,0,0,0.2); padding: 15px 20px; border-radius: 12px; border-left: 4px solid #3b82f6; margin-bottom: 10px;'>
                            <div style='font-family: Georgia, serif; font-size: 1.1rem; color: #f8fafc; margin-bottom: 5px;'>{row['content']}</div>
                            <div style='color: #64748b; font-size: 0.85rem;'>{row['translation']}</div>
                        </div>
                        """, unsafe_allow_html=True)
                        col1, col2 = st.columns([5, 1])
                        with col2: st.button("➕ 部署", key=f"add_{idx}", on_click=append_to_draft, args=(row['content'],))
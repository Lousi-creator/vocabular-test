import streamlit as st
import pandas as pd
import os
import time  
import re  
import sqlite3  
import hashlib 
import json 
from gtts import gTTS
from openai import OpenAI
from dotenv import load_dotenv
from dotenv import load_dotenv
load_dotenv()  # 激活 .env 文件
# ==========================================
# 0. 网页全局设置 
# ==========================================
st.set_page_config(page_title="极客词汇系统", page_icon="✨", layout="centered", initial_sidebar_state="collapsed")

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
@keyframes criticalHit_UID {
    0% { transform: translate(-50%, -50%) scale(0.1); opacity: 0; }
    15% { transform: translate(-50%, -50%) scale(1.4) skewX(-15deg); opacity: 1; text-shadow: 5px 5px 0px #FF0000, -5px -5px 0px #00FFFF; }
    30% { transform: translate(-50%, -50%) scale(1) skewX(5deg); opacity: 1; text-shadow: 0px 0px 30px #FF8C00; }
    70% { transform: translate(-50%, -50%) scale(1.1) skewX(0deg); opacity: 1; text-shadow: 0px 0px 15px #FFD700; }
    100% { transform: translate(-50%, -50%) scale(2.5); opacity: 0; filter: blur(10px); }
}
.monster-kill-text-UID {
    position: fixed; top: 35%; left: 50%; z-index: 999999;
    font-family: 'Impact', sans-serif; font-size: 110px; color: #FFDF00;
    font-style: italic; font-weight: 900; -webkit-text-stroke: 4px #D32F2F;
    pointer-events: none; animation: criticalHit_UID 0.9s cubic-bezier(0.25, 0.46, 0.45, 0.94) forwards;
}
</style>
<div class="monster-kill-text-UID">PERFECT!</div>
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
    conn.commit()
    conn.close()

init_db()

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

def make_hash(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_hash(password, hashed_text):
    return make_hash(password) == hashed_text

def create_user(username, password):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    try:
        status = 'active' if username == st.secrets.get("ADMIN_USERNAME", "admin") else 'pending'
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

# ==========================================
# 数据文件初始化容错处理 
# ==========================================
if not os.path.exists('words.csv'):
    pd.DataFrame([{'word': 'apple', 'definition': '苹果', 'wrong_count': 0, 'phonetic': '/ˈæpl/', 'frequency_tier': '🟢 高频核心词汇'}]).to_csv('words.csv', index=False)
if not os.path.exists('essays.csv'):
    pd.DataFrame([
        {'category': '开头', 'subcategory': '建议信', 'content': 'I am writing to express my views concerning...', 'translation': '我写信是想表达关于……的看法。'},
        {'category': '结尾', 'subcategory': '通用', 'content': 'Looking forward to your prompt reply.', 'translation': '期待你的及时回复。'}
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
if 'essay_draft' not in st.session_state:
    st.session_state.essay_draft = ""
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
    # 【修复点】：彻底抛弃切换时清空隔离名单的旧逻辑，交由实时云同步接管
    st.session_state.feedback = ""          
    st.session_state.current_word = ""      
    st.session_state.show_balloons = False  

def get_next_word(mode, tier):
    df = pd.read_csv('words.csv')
    if 'frequency_tier' not in df.columns: df['frequency_tier'] = "🟢 高频核心词汇"
    if st.session_state.quarantine_list: df = df[~df['word'].isin(st.session_state.quarantine_list)]
    if mode == "错题大扫除": df = df[df['wrong_count'] > 0]
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

def check_answer():
    user_input = st.session_state.user_input.strip().lower()
    mode = st.session_state.mode_selector
    tier = st.session_state.tier_selector 
    if not user_input or not st.session_state.current_word: return
    df = pd.read_csv('words.csv')
    correct_word = st.session_state.current_word
    
    if user_input == correct_word:
        st.session_state.perfect_hit = True; st.session_state.feedback = ""      
        if mode == "错题大扫除": df.loc[df['word'] == correct_word, 'wrong_count'] = 0
    else:
        st.session_state.feedback = f"❌ 正确拼写: {correct_word}"
        df.loc[df['word'] == correct_word, 'wrong_count'] += 1
        
    if correct_word not in st.session_state.quarantine_list: 
        st.session_state.quarantine_list.append(correct_word)
        if st.session_state.current_user:
            save_progress(st.session_state.current_user, mode, tier, st.session_state.quarantine_list)
            
    df.to_csv('words.csv', index=False)
    st.session_state.user_input = ""
    get_next_word(mode, tier) 

# ==========================================
# 4. 主界面渲染路由引擎
# ==========================================

if st.session_state.current_user is None:
    st.markdown("""
    <div style='text-align: center; margin-bottom: 30px;'>
        <h1 style='font-weight: 900; font-size: 3rem; margin-bottom: 0;'>极客词汇系统<span class='text-highlight'>.</span></h1>
        <p style='font-size: 1.2rem; margin-top: 5px;'>专注、高效、数据驱动的高考提分引擎</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        tab_login, tab_reg = st.tabs(["🔑 身份验证", "📝 新用户注册"])
        
        with tab_login:
            st.write("<br>", unsafe_allow_html=True)
            log_user = st.text_input("用户名", key="log_u", placeholder="输入账号")
            log_pwd = st.text_input("安全密码", type="password", key="log_p", placeholder="••••••••")
            st.write("<br>", unsafe_allow_html=True)
            if st.button("进入系统", use_container_width=True, type="primary"):
                result = login_user(log_user, log_pwd)
                if result is not None:
                    credits, status = result
                    if status == 'pending':
                        st.warning("⏳ 您的账号正在等待管理员审核。")
                    else:
                        st.session_state.current_user = log_user
                        st.session_state.user_credits = credits
                        st.session_state.is_admin = (log_user == os.getenv("ADMIN_USERNAME", "admin"))
                        st.rerun()
                else:
                    st.error("用户名或密码不匹配")
                    
        with tab_reg:
            st.write("<br>", unsafe_allow_html=True)
            reg_user = st.text_input("设置用户名", key="reg_u")
            reg_pwd = st.text_input("设置高强度密码", type="password", key="reg_p")
            st.write("<br>", unsafe_allow_html=True)
            if st.button("提交注册申请", use_container_width=True):
                if reg_user and reg_pwd:
                    if create_user(reg_user, reg_pwd):
                        st.success("注册请求已发送！请等待管理员放行。")
                    else:
                        st.error("该用户名已被其他极客占用")
                else:
                    st.warning("字段不可为空")
        st.markdown("</div>", unsafe_allow_html=True)

elif st.session_state.current_page == 'home':
    st.markdown(f"""
    <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 40px;'>
        <div>
            <h2 style='margin: 0; font-weight: 800;'>欢迎回来, <span class='text-highlight'>{st.session_state.current_user}</span></h2>
            <p style='margin: 0; font-size: 0.9rem;'>当前可用 AI 算力额度：<strong class='text-highlight'>{st.session_state.user_credits}</strong> 次</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    col_empty, col_out = st.columns([5, 1])
    with col_out:
        if st.button("退出登录", use_container_width=True):
            st.session_state.current_user = None
            st.session_state.is_admin = False
            st.rerun()

    st.write("<br>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    
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

elif st.session_state.current_page == 'vocab':
    st.markdown("<div class='back-btn'>", unsafe_allow_html=True)
    if st.button("← 返回中央大厅"): navigate_to('home')
    st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("<h2 style='text-align: center; margin-bottom: 30px;'>🎯 靶向词汇通关</h2>", unsafe_allow_html=True)
    
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    mode = st.radio("选择行动代号：", ["全局摸底考", "错题大扫除"], horizontal=True, key="mode_selector", on_change=reset_task_state)
    tiers = ["🌍 全库混合 (不分级)", "🟢 高频核心词汇", "🟡 中高频进阶词汇", "🟠 中频拓展词汇", "🔴 低频生僻词汇"]
    tier = st.selectbox("锁定目标层级：", tiers, key="tier_selector", on_change=reset_task_state)
    
    # 【极致体验更新】：选择框变化时，代码立刻往下执行读取最新存档，无需再点击按钮！
    if st.session_state.current_user:
        st.session_state.quarantine_list = load_progress(st.session_state.current_user, mode, tier)
        
    st.write("<br>", unsafe_allow_html=True)
    col_start, col_reset = st.columns([3, 1])
    with col_start:
        if st.button("🚀 部署并继续任务", type="primary", use_container_width=True):
            # 因为上面已经自动完成了 load_progress，所以按钮按下去只需要发新单词即可
            get_next_word(mode, tier)
    with col_reset:
        if st.button("🔄 重置进度", use_container_width=True):
            save_progress(st.session_state.current_user, mode, tier, [])
            st.session_state.quarantine_list = []
            st.session_state.current_word = ""
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)
    
    df_prog = pd.read_csv('words.csv')
    if 'frequency_tier' not in df_prog.columns: df_prog['frequency_tier'] = "🟢 高频核心词汇"
    if mode == "错题大扫除": df_prog = df_prog[df_prog['wrong_count'] > 0]
    if tier != "🌍 全库混合 (不分级)": df_prog = df_prog[df_prog['frequency_tier'] == tier]
    total_round_words = len(df_prog)
    completed_words = len(st.session_state.quarantine_list)
    
    if total_round_words > 0:
        progress_ratio = min(completed_words / total_round_words, 1.0)
        st.progress(progress_ratio)
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
        tts = gTTS(st.session_state.current_word, lang='en')
        tts.save("temp.mp3"); st.audio("temp.mp3", format="audio/mp3", autoplay=True)
        st.text_input(" ", key="user_input", on_change=check_answer, placeholder="在此输入拦截指令 (拼写)...", label_visibility="collapsed")

    with st.expander("📡 展开错题雷达扫描结果", expanded=False):
        df_wrong = pd.read_csv('words.csv')
        df_wrong = df_wrong[df_wrong['wrong_count'] > 0].sort_values(by='wrong_count', ascending=False)
        if df_wrong.empty: st.write("雷达未发现高危词汇")
        for _, row in df_wrong.iterrows():
            st.markdown(f"<div style='background:rgba(0,0,0,0.3); padding:10px 15px; border-radius:12px; margin-bottom:8px; border-left: 3px solid #ef4444;'><b style='color:#e2e8f0;'>{row['word']}</b> <span style='color:#94a3b8; font-size:0.9rem; margin-left:10px;'>{row['definition']}</span><span style='float:right; color:#ef4444; font-size:0.8rem; font-weight:bold;'>威胁度 {row['wrong_count']}</span></div>", unsafe_allow_html=True)

elif st.session_state.current_page == 'essay':
    st.markdown("<div class='back-btn'>", unsafe_allow_html=True)
    if st.button("← 返回中央大厅"): navigate_to('home')
    st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("<h2 style='text-align: center; margin-bottom: 30px;'>✍️ 高考文书锻造工坊</h2>", unsafe_allow_html=True)
    
    with st.container():
        st.text_area(" ", height=250, key="essay_draft", placeholder="在此输入你的草稿...", label_visibility="collapsed")
        
        st.write("<br>", unsafe_allow_html=True)
        col_scan, col_ai, col_clear = st.columns([2, 2, 1])
        with col_scan:
            scan_btn = st.button("🔍 弱点词汇扫描", use_container_width=True)
        with col_ai:
            ai_btn = st.button("🤖 召唤 DeepSeek 导师", type="primary", use_container_width=True)
        with col_clear:
            if st.button("🗑️ 清空", use_container_width=True): st.session_state.essay_draft = ""; st.rerun()
            
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
                st.error("🛑 系统配额已耗尽，请注入私人 Key 启动。")
            else:
                with st.spinner("🧠 神经元网络正在解构你的文章..."):
                    try:
                        active_api_key = user_api_key if user_api_key else os.getenv("DEEPSEEK_API_KEY", "")
                        if not active_api_key: st.error("未检测到 API 密钥，连接中断。")
                        else:
                            client = OpenAI(api_key=active_api_key, base_url="https://api.deepseek.com")
                            prompt = f"""
                            你现在是【浙江省高考英语阅卷组长】，极其严厉、专业且毒舌。你的任务是对下面这篇 80 词左右的高考应用文草稿进行降维打击式的批改。
                            
                            【浙江卷评分标准（满分 15 分）】：
                            - 第五档(13-15分)：全覆盖要点，使用较多复杂语法和高级词汇，极少错误，逻辑丝滑。
                            - 第四档(10-12分)：覆盖主要要点，语法词汇基本满足要求，有基础连贯性。
                            - 第三档(7-9分)：漏掉部分要点，词汇语法单一，有一些错误但不影响理解。
                            - 低分档(0-6分)：不知所云，错误百出。
                            - 特殊说明：如果字数不达标直接扣除大部分分数

                            【执行工作流（严格按此结构输出）】：
                            
                            ### 📊 一、 判卷定档
                            - **预估分数**：X/15
                            - **定档理由**：一针见血地指出为什么给这个分数（别跟我客气，直击痛点）。

                            ### 🔪 二、 致命雷区排查
                            （如果没有错误，此项可写“基础尚可，无致命语法硬伤”。如果有，请列出：）
                            - 找出所有的时态错误、主谓不一致、中式英语（Chinglish）、以及烂大街的低级词汇。
                            - 格式：`原句错误` ❌ -> `诊断说明`。
                            
                            ### 💎 三、 满分升格示范 (The Masterpiece)
                            这是你的核心任务！请在保持学生原意的前提下，重写这篇应用文。
                            - 必须使用至少 2 个高级句型（如：倒装句、强调句、非谓语动词作状语/定语、复合从句）。
                            - 必须使用地道的高级词汇替换掉平庸词汇。
                            - 句与句之间必须有符合逻辑的高级衔接词。
                            - 请将你使用的**高级语法和亮眼词汇**加粗显示，并在段落下方用 💡 简要批注你这样改的绝妙之处。
                            
                            【学生草稿】：
                            {st.session_state.essay_draft}
                            """
                            response = client.chat.completions.create(
                                model="deepseek-chat",
                                messages=[{"role": "system", "content": "你是一位负责、专业且要求极高的高考英语名师。"},{"role": "user", "content": prompt}],
                                temperature=0.7 
                            )
                            ai_feedback = response.choices[0].message.content
                            
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
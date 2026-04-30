import streamlit as st
import pandas as pd
import os
import time  
import re  
import sqlite3  
import hashlib 
from gtts import gTTS
from openai import OpenAI
from dotenv import load_dotenv

# ==========================================
# 0. 网页全局设置 
# ==========================================
st.set_page_config(page_title="极客词汇系统", page_icon="📝", layout="centered", initial_sidebar_state="expanded")

# ==========================================
# 0.5 终极前端黑魔法 (UI 劫持)
# ==========================================
BASE_CSS = """
<style>
#MainMenu, footer {visibility: hidden;}
header {background-color: transparent !important; box-shadow: none !important;} 
.stApp {background-color: #F4F6F9 !important;} 
.block-container {max-width: 500px !important; padding-top: 1rem !important;}
.stTextInput > div > div > input {
    background-color: transparent !important; border: none !important;
    border-bottom: 3px solid #E5E7EB !important; border-radius: 0px !important;
    text-align: center !important; font-size: 36px !important; 
    font-weight: 800 !important; color: #111827 !important; padding: 10px !important;
}
.stTextInput > div > div > input:focus { border-bottom: 3px solid #3B82F6 !important; outline: none !important;}
.stButton > button {
    border-radius: 30px !important; border: none !important;
    background: #FFFFFF !important; color: #4B5563 !important;
    box-shadow: 0 4px 15px rgba(0,0,0,0.04) !important; font-weight: 600 !important; height: 50px !important;
}
div[data-testid="stRadio"] > div {background: white; padding: 15px 20px; border-radius: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.02); margin-bottom: 10px;}
.stButton > button[kind="secondary"] {
    height: 35px !important; font-size: 0.8rem !important; padding: 0 15px !important; border: 1px solid #E5E7EB !important;
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
    conn.commit()
    conn.close()

init_db()

def make_hash(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_hash(password, hashed_text):
    return make_hash(password) == hashed_text

def create_user(username, password):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    try:
        status = 'active' if username == os.getenv("ADMIN_USERNAME", "admin") else 'pending'
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

# ==========================================
# 2. 核心交互函数 
# ==========================================
def append_to_draft(text_to_add):
    st.session_state.essay_draft += text_to_add + " "

# 【修复Bug新增】：任务切换时触发的清洗函数
def reset_task_state():
    st.session_state.feedback = ""          # 清空恭喜或报错信息
    st.session_state.current_word = ""      # 清空当前正在测的单词
    st.session_state.quarantine_list = []   # 清空当前任务的通关进度
    st.session_state.show_balloons = False  # 关掉气球开关

def get_next_word(mode, tier):
    df = pd.read_csv('words.csv')
    
    if 'frequency_tier' not in df.columns:
        df['frequency_tier'] = "🟢 高频核心词汇"
        
    if st.session_state.quarantine_list:
        df = df[~df['word'].isin(st.session_state.quarantine_list)]
        
    if mode == "错题大扫除":
        df = df[df['wrong_count'] > 0]
        
    if tier != "🌍 全库混合 (不分级)":
        df = df[df['frequency_tier'] == tier]
        
    if df.empty:
        st.session_state.current_word = ""
        st.session_state.feedback = "🎉 恭喜！当前任务节点已通关，请切换其他任务或模式！"
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
        
    df.to_csv('words.csv', index=False)
    st.session_state.user_input = ""
    get_next_word(mode, tier) 

# ==========================================
# 3. 侧边栏多功能导航台 
# ==========================================
with st.sidebar:
    st.markdown("<h2 style='text-align: center; color: #111827;'>🛠️ 控制中心</h2>", unsafe_allow_html=True)
    
    if st.session_state.current_user is None:
        st.markdown("<p style='text-align: center; color: #6B7280; font-size: 0.85rem;'>身份未验证，请先登录</p>", unsafe_allow_html=True)
        tab_login, tab_reg = st.tabs(["🔑 登录", "📝 注册"])
        
        with tab_login:
            log_user = st.text_input("用户名", key="log_u")
            log_pwd = st.text_input("密码", type="password", key="log_p")
            if st.button("登 录", use_container_width=True):
                result = login_user(log_user, log_pwd)
                if result is not None:
                    credits, status = result
                    if status == 'pending':
                        st.warning("⏳ 您的账号正在等待管理员审核，审核通过后即可登录。")
                    else:
                        st.session_state.current_user = log_user
                        st.session_state.user_credits = credits
                        st.session_state.is_admin = (log_user == os.getenv("ADMIN_USERNAME", "admin"))
                        st.success("登录成功！")
                        st.rerun()
                else:
                    st.error("用户名或密码错误！")
                    
        with tab_reg:
            reg_user = st.text_input("设置用户名", key="reg_u")
            reg_pwd = st.text_input("设置密码", type="password", key="reg_p")
            if st.button("注 册", use_container_width=True):
                if reg_user and reg_pwd:
                    if create_user(reg_user, reg_pwd):
                        st.success("注册成功！您的账号需等待管理员审核通过后方可登录。")
                    else:
                        st.error("该用户名已被占用，换一个吧！")
                else:
                    st.warning("用户名和密码不能为空！")
        st.divider()
    else:
        st.markdown(f"<div style='background-color: #EFF6FF; padding: 15px; border-radius: 10px; border: 1px solid #BFDBFE; text-align: center;'><p style='margin: 0; color: #1E3A8A; font-weight: bold; font-size: 1.1rem;'>👤 {st.session_state.current_user}</p><p style='margin: 5px 0 0 0; color: #3B82F6; font-size: 0.9rem;'>可用 AI 额度: <b style='font-size: 1.1rem;'>{st.session_state.user_credits}</b> 次</p></div>", unsafe_allow_html=True)
        if st.button("🚪 退出登录", use_container_width=True):
            st.session_state.current_user = None
            st.session_state.is_admin = False
            st.rerun()
        st.divider()

        if st.session_state.is_admin:
            st.markdown("<p style='text-align: center; color: #92400E; font-weight: bold;'>👑 管理员审核面板</p>", unsafe_allow_html=True)
            pending_users = get_pending_users()
            if not pending_users:
                st.info("✅ 暂无待审核用户")
            else:
                st.markdown(f"<p style='text-align: center; color: #6B7280; font-size: 0.85rem;'>待审核: {len(pending_users)} 人</p>", unsafe_allow_html=True)
                for pu in pending_users:
                    col_approve, col_reject = st.columns([1, 1])
                    with col_approve:
                        if st.button(f"✅ 通过 {pu}", key=f"approve_{pu}", use_container_width=True):
                            approve_user(pu)
                            st.success(f"{pu} 已通过审核")
                            st.rerun()
                    with col_reject:
                        if st.button(f"❌ 拒绝 {pu}", key=f"reject_{pu}", use_container_width=True):
                            reject_user(pu)
                            st.warning(f"{pu} 已被拒绝")
                            st.rerun()
            st.divider()

    app_mode = st.selectbox("请选择功能模块：", ["单词通关挑战", "写作灵感工坊"])
    st.divider()
    
    if st.session_state.current_user is not None:
        if app_mode == "单词通关挑战":
            st.markdown("<p style='text-align: center; color: #6B7280;'>🔥 专属错题本</p>", unsafe_allow_html=True)
            df_sidebar = pd.read_csv('words.csv')
            df_wrong = df_sidebar[df_sidebar['wrong_count'] > 0].sort_values(by='wrong_count', ascending=False)
            with st.expander("🫣 点击展开 / 收起排行榜", expanded=False):
                for _, row in df_wrong.iterrows():
                    st.markdown(f"<div style='background:white;padding:10px;border-radius:10px;margin-bottom:5px;border:1px solid #EEE;'><b>{row['word']}</b><br><small>{row['definition']}</small><br><span style='color:red;'>错 {row['wrong_count']} 次</span></div>", unsafe_allow_html=True)
        else:
            st.markdown("<p style='text-align: center; color: #6B7280;'>✍️ 语料快速搜索</p>", unsafe_allow_html=True)
            search_query = st.text_input(" ", placeholder="输入关键字...", label_visibility="collapsed")
            if st.button("🗑️ 清空草稿箱", use_container_width=True):
                st.session_state.essay_draft = ""; st.rerun()
            st.divider()
            st.markdown("<p style='text-align: center; color: #6B7280;'>🔑 防刷验证区</p>", unsafe_allow_html=True)
            user_api_key = st.text_input("自带 DeepSeek Key (突破次数限制):", type="password")

# ==========================================
# 4. 主界面渲染逻辑 
# ==========================================
if st.session_state.current_user is None:
    st.markdown("""
    <div style='text-align: center; padding: 100px 20px; background-color: white; border-radius: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.05); margin-top: 50px;'>
        <div style='font-size: 60px; margin-bottom: 20px;'>🔒</div>
        <h2 style='color: #111827;'>系统已锁定</h2>
        <p style='color: #6B7280; font-size: 1.1rem;'>为了保护服务器资源与 API 额度，请先在左侧菜单栏登录。<br>如果您还没有账号，请免费注册。</p>
    </div>
    """, unsafe_allow_html=True)

else:
    if app_mode == "单词通关挑战":
        if st.session_state.perfect_hit:
            unique_id = str(time.time()).replace('.', '') 
            st.markdown(PERFECT_CSS_TEMPLATE.replace("UID", unique_id), unsafe_allow_html=True)
            st.session_state.perfect_hit = False 
            
        # 【应用修复】：给模式和节点切换绑定上清洗功能
        mode = st.radio(" ", ["全局摸底考", "错题大扫除"], horizontal=True, key="mode_selector", label_visibility="collapsed", on_change=reset_task_state)
        
        tiers = ["🌍 全库混合 (不分级)", "🟢 高频核心词汇", "🟡 中高频进阶词汇", "🟠 中频拓展词汇", "🔴 低频生僻词汇"]
        tier = st.selectbox("🎯 选择挑战任务节点：", tiers, key="tier_selector", on_change=reset_task_state)
        
        if st.button("🚀 开始测试", use_container_width=True):
            st.session_state.quarantine_list = []
            get_next_word(mode, tier)
            
        st.write("<br>", unsafe_allow_html=True)
        
        df_prog = pd.read_csv('words.csv')
        if 'frequency_tier' not in df_prog.columns:
            df_prog['frequency_tier'] = "🟢 高频核心词汇"
            
        if mode == "错题大扫除":
            df_prog = df_prog[df_prog['wrong_count'] > 0]
        if tier != "🌍 全库混合 (不分级)":
            df_prog = df_prog[df_prog['frequency_tier'] == tier]
            
        total_round_words = len(df_prog)
        completed_words = len(st.session_state.quarantine_list)
        
        if total_round_words > 0:
            progress_ratio = min(completed_words / total_round_words, 1.0)
            st.progress(progress_ratio)
            st.markdown(f"<div style='text-align:center; color:#9CA3AF; font-size:0.85rem; margin-top:5px; margin-bottom:20px;'>🏁 任务通关进度: {completed_words} / {total_round_words}</div>", unsafe_allow_html=True)
        else:
            st.info("💡 当前节点下没有需要复习的词汇，去挑战别的任务吧！")

        if st.session_state.feedback:
            if "✨" in st.session_state.feedback: st.success(st.session_state.feedback)
            elif "恭喜" in st.session_state.feedback: 
                if st.session_state.get('show_balloons', False):
                    st.balloons()
                    st.session_state.show_balloons = False
                st.success(st.session_state.feedback)
            else: st.error(st.session_state.feedback)
            
        if st.session_state.current_word:
            st.markdown(f"<div style='text-align:center;margin:20px 0 40px 0;'><div style='font-size:2.5rem;font-weight:900;color:#111827;'>{st.session_state.chinese_meaning}</div><div style='font-size:1.2rem;color:#6B7280;margin-top:10px;'>{st.session_state.phonetic}</div></div>", unsafe_allow_html=True)
            tts = gTTS(st.session_state.current_word, lang='en')
            tts.save("temp.mp3"); st.audio("temp.mp3", format="audio/mp3", autoplay=True)
            st.text_input(" ", key="user_input", on_change=check_answer, placeholder="Type here...", label_visibility="collapsed")
    
    else:
        st.markdown("<h1 style='text-align: center; color: #111827;'>✍️ 写作灵感工坊</h1>", unsafe_allow_html=True)
        with st.container():
            st.markdown("<p style='color: #6B7280; font-size: 0.9rem; margin-bottom: 5px;'>📝 我的作文草稿:</p>", unsafe_allow_html=True)
            st.text_area(" ", height=200, key="essay_draft", label_visibility="collapsed")
            col_scan, col_ai = st.columns([1, 1])
            with col_scan:
                scan_btn = st.button("🔍 扫描低级词汇", use_container_width=True)
            with col_ai:
                ai_btn = st.button("🤖 召唤 AI 阅卷导师", use_container_width=True)
            if scan_btn and st.session_state.essay_draft.strip():
                draft_text = st.session_state.essay_draft.lower()
                df_upgrade = pd.read_csv('upgrade.csv')
                found_words = []
                for _, row in df_upgrade.iterrows():
                    basic_word = row['basic']
                    if re.search(r'\b' + re.escape(basic_word) + r'\b', draft_text): found_words.append(row)
                if not found_words: st.success("🎉 太棒了！没有检测到常见的低级词汇，继续保持！")
                else:
                    st.warning(f"⚠️ 滴滴滴！雷达发现了 {len(found_words)} 处可以升格的低级词汇：")
                    for item in found_words:
                        st.markdown(f"<div style='background-color: #FFFBEB; padding: 15px; border-radius: 10px; border-left: 4px solid #F59E0B; margin-bottom: 10px;'><span style='color: #B45309; font-weight: bold; text-decoration: line-through;'>{item['basic']}</span> 👉 <span style='color: #059669; font-weight: bold; font-size: 1.1rem;'>{item['advanced']}</span><div style='font-size: 0.85rem; color: #6B7280; margin-top: 5px;'>💡 {item['reason']}</div></div>", unsafe_allow_html=True)
            
            if ai_btn and st.session_state.essay_draft.strip():
                current_time = time.time()
                COOLDOWN_SECONDS = 30
                has_credits = st.session_state.user_credits > 0 
                
                if current_time - st.session_state.last_ai_time < COOLDOWN_SECONDS:
                    st.warning(f"⏳ 技能冷却中！请等待 {int(COOLDOWN_SECONDS - (current_time - st.session_state.last_ai_time))} 秒。")
                elif not has_credits and not user_api_key:
                    st.error("🛑 免费次数已用完！请在左侧侧边栏底部填入你自己的 API Key。")
                else:
                    with st.spinner("🧠 AI 导师正在批阅..."):
                        try:
                            load_dotenv()
                            active_api_key = user_api_key if user_api_key else os.getenv("DEEPSEEK_API_KEY")
                            if not active_api_key: st.error("❌ 找不到 API 密钥！")
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
                                st.success("🎉 批阅完成！")
                                st.markdown(f"""
                                <div style='background-color: white; padding: 25px; border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); border-top: 5px solid #10B981; margin-top: 20px; margin-bottom: 20px;'>
                                    <h3 style='color: #065F46; margin: 0;'>👩‍🏫 导师点评与升格方案</h3>
                                </div>
                                """, unsafe_allow_html=True)
                                st.markdown(ai_feedback)
                        except Exception as e: st.error(f"❌ 调用失败：{e}")
        st.divider()
        df_essays = pd.read_csv('essays.csv')
        categories = list(df_essays['category'].unique())
        tabs = st.tabs(categories)
        for i, cat in enumerate(categories):
            with tabs[i]:
                cat_data = df_essays[df_essays['category'] == cat]
                subcats = cat_data['subcategory'].unique()
                for sub in subcats:
                    st.markdown(f"<p style='color: #3B82F6; font-weight: bold; margin-top: 20px;'>• {sub}</p>", unsafe_allow_html=True)
                    sub_data = cat_data[cat_data['subcategory'] == sub]
                    for idx, row in sub_data.iterrows():
                        with st.container():
                            st.markdown(f"""
                            <div style='background: white; padding: 20px; border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.02); border-left: 5px solid #3B82F6;'>
                                <div style='font-family: serif; font-size: 1.1rem; color: #111827;'>{row['content']}</div>
                                <div style='color: #6B7280; font-size: 0.85rem; margin-top: 8px;'>{row['translation']}</div>
                            </div>
                            """, unsafe_allow_html=True)
                            col1, col2 = st.columns([4, 1])
                            with col2: st.button("➕ 添加", key=f"add_{idx}", on_click=append_to_draft, args=(row['content'],))
import streamlit as st
import pandas as pd
import os
import time  
from gtts import gTTS

# ==========================================
# 0. 网页全局设置
# ==========================================
# 【手术点 1】：加入 initial_sidebar_state="collapsed"，让侧边栏默认强制隐藏！
st.set_page_config(page_title="极客词汇系统", page_icon="📝", layout="centered", initial_sidebar_state="collapsed")

# ==========================================
# 0.5 终极前端黑魔法 (彻底劫持 Streamlit 默认UI)
# ==========================================
BASE_CSS = """
<style>
/* 1. 净化基础环境 (【手术点 2】：修复误伤！不再粗暴隐藏整个header，让侧边栏的 > 按钮回来，但把背景变透明保持极简) */
#MainMenu, footer {visibility: hidden;}
header {background-color: transparent !important; box-shadow: none !important;} 

.stApp {background-color: #F4F6F9 !important;} 

/* 2. 强制窄屏布局，在电脑上也拥有完美的手机App比例 */
.block-container {max-width: 500px !important; padding-top: 1rem !important;}

/* 3. 核心大改造：输入框变成极简下划线！ */
.stTextInput > div > div > input {
    background-color: transparent !important;
    border: none !important;
    border-bottom: 3px solid #E5E7EB !important; 
    border-radius: 0px !important;
    text-align: center !important; 
    font-size: 36px !important; 
    font-weight: 800 !important;
    color: #111827 !important;
    padding: 10px !important;
    box-shadow: none !important;
    transition: border-color 0.3s;
}
.stTextInput > div > div > input:focus { 
    border-bottom: 3px solid #3B82F6 !important; 
    outline: none !important;
}

/* 4. 按钮大改造：变成圆润的、带有呼吸感的悬浮卡片 */
.stButton > button {
    border-radius: 30px !important; 
    border: none !important;
    background: #FFFFFF !important; 
    color: #4B5563 !important;
    box-shadow: 0 4px 15px rgba(0,0,0,0.04) !important;
    font-weight: 600 !important; 
    height: 50px !important;
    transition: all 0.2s !important;
}
.stButton > button:hover {
    transform: translateY(-2px) !important; 
    box-shadow: 0 8px 20px rgba(0,0,0,0.08) !important; 
    color: #3B82F6 !important;
}

/* 5. 选项卡改造：装进一个白色药丸形状的盒子里 */
div[data-testid="stRadio"] > div {
    background: white; 
    padding: 15px 20px; 
    border-radius: 20px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.02); 
    margin-bottom: 10px;
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
    pointer-events: none; 
    animation: criticalHit_UID 0.9s cubic-bezier(0.25, 0.46, 0.45, 0.94) forwards;
}
</style>
<div class="monster-kill-text-UID">PERFECT!</div>
"""

# ==========================================
# 1. 数据初始化与状态管理 (原版保留)
# ==========================================
if not os.path.exists('words.csv'):
    df = pd.DataFrame([
        {'word': 'apple', 'definition': '苹果', 'wrong_count': 0},
        {'word': 'banana', 'definition': '香蕉', 'wrong_count': 0},
        {'word': 'study', 'definition': '学习', 'wrong_count': 1}
    ])
    df.to_csv('words.csv', index=False)

if 'current_word' not in st.session_state:
    st.session_state.current_word = ""
    st.session_state.chinese_meaning = ""
    st.session_state.feedback = ""
    st.session_state.perfect_hit = False  
    st.session_state.quarantine_list = [] 

# ==========================================
# 2. 核心交互函数 (原版保留)
# ==========================================
def get_next_word(mode):
    df = pd.read_csv('words.csv')
    
    if st.session_state.quarantine_list:
        df = df[~df['word'].isin(st.session_state.quarantine_list)]

    if mode == "错题大扫除":
        df_to_test = df[df['wrong_count'] > 0]
        if df_to_test.empty:
            st.session_state.current_word = ""
            if len(st.session_state.quarantine_list) > 0:
                st.session_state.feedback = "⏳ 本轮错题已复习完毕！答错的词已进入冷却期，请休息片刻开启新一轮！"
            else:
                st.session_state.feedback = "🎉 错题本空空如也！请切换全局模式。"
            return
    else:
        df_to_test = df
        if df_to_test.empty:
            st.session_state.current_word = ""
            st.session_state.feedback = "🎉 词库已全部抽完！"
            return

    row = df_to_test.sample(n=1).iloc[0]
    st.session_state.current_word = row['word']
    st.session_state.chinese_meaning = row['definition']

def check_answer():
    user_input = st.session_state.user_input.strip().lower()
    mode = st.session_state.mode_selector
    
    if not user_input or not st.session_state.current_word:
        return

    df = pd.read_csv('words.csv')
    correct_word = st.session_state.current_word

    if user_input == correct_word:
        st.session_state.perfect_hit = True 
        st.session_state.feedback = ""      
        
        if mode == "错题大扫除" and df.loc[df['word'] == correct_word, 'wrong_count'].iloc[0] > 0:
            df.loc[df['word'] == correct_word, 'wrong_count'] = 0
            st.session_state.feedback = f"✨ 【{correct_word}】已从错题本斩杀！" 
            
    else:
        st.session_state.feedback = f"❌ 遗憾！正确拼写是: **{correct_word}**"
        df.loc[df['word'] == correct_word, 'wrong_count'] += 1
        
        if correct_word not in st.session_state.quarantine_list:
            st.session_state.quarantine_list.append(correct_word)
        
    df.to_csv('words.csv', index=False)
    st.session_state.user_input = "" 
    get_next_word(mode) 

# ==========================================
# 3. 侧边栏错题记录本 (防剧透升级)
# ==========================================
with st.sidebar:
    st.markdown("<h2 style='text-align: center; color: #111827;'>🔥 专属错题本</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #6B7280; font-size: 14px;'>你的易错词汇排行榜</p>", unsafe_allow_html=True)
    st.divider()

    df_sidebar = pd.read_csv('words.csv')
    df_wrong = df_sidebar[df_sidebar['wrong_count'] > 0].sort_values(by='wrong_count', ascending=False)
    
    if df_wrong.empty:
        st.success("🎉 太强了！目前没有任何错题记录。")
    else:
        # 【手术点 3】：双重防剧透保护罩！把单词全装进这个必须点击才能展开的盒子里
        with st.expander("🫣 点击展开 / 收起排行榜", expanded=False):
            for index, row in df_wrong.iterrows():
                st.markdown(f"""
                <div style='background-color: white; padding: 12px; border-radius: 12px; margin-bottom: 12px; border: 1px solid #E5E7EB;'>
                    <div style='font-size: 18px; font-weight: bold; color: #111827;'>{row['word']}</div>
                    <div style='font-size: 14px; color: #6B7280; margin-bottom: 4px;'>{row['definition']}</div>
                    <div style='font-size: 13px; color: #EF4444; font-weight: bold;'>❌ 累计错误: {row['wrong_count']} 次</div>
                </div>
                """, unsafe_allow_html=True)

# ==========================================
# 4. 绘制网页 UI (精简排版 - 原版保留)
# ==========================================
if st.session_state.perfect_hit:
    unique_id = str(time.time()).replace('.', '') 
    dynamic_css = PERFECT_CSS_TEMPLATE.replace("UID", unique_id) 
    st.markdown(dynamic_css, unsafe_allow_html=True)
    st.session_state.perfect_hit = False 

mode = st.radio(" ", ["全局摸底考", "错题大扫除"], horizontal=True, key="mode_selector", label_visibility="collapsed")

if st.button("🚀 开始测试 / 手动切题", use_container_width=True):
    st.session_state.feedback = "" 
    st.session_state.quarantine_list = []
    get_next_word(mode)

if not st.session_state.current_word and len(st.session_state.quarantine_list) > 0:
    if st.button("🔄 开启新一轮 (重置冷却)", use_container_width=True):
        st.session_state.quarantine_list = []
        st.session_state.feedback = ""
        get_next_word(mode)

if st.session_state.feedback:
    if "❌" in st.session_state.feedback:
        st.error(st.session_state.feedback)
    elif "⏳" in st.session_state.feedback:
        st.warning(st.session_state.feedback)
    else:
        st.success(st.session_state.feedback)

if st.session_state.current_word:
    st.markdown(f"<div style='text-align: center; font-size: 2.5rem; font-weight: 900; color: #111827; margin: 40px 0;'>{st.session_state.chinese_meaning}</div>", unsafe_allow_html=True)
    
    tts = gTTS(st.session_state.current_word, lang='en')
    tts.save("temp.mp3")
    st.audio("temp.mp3", format="audio/mp3", autoplay=True)
    
    st.text_input(" ", key="user_input", on_change=check_answer, placeholder="Type here...", label_visibility="collapsed")

df = pd.read_csv('words.csv')
st.markdown(f"<div style='text-align: center; color: #9CA3AF; margin-top: 30px; font-size: 0.9rem;'>📊 词库总量: {len(df)} 词   |   🔥 待消灭错题: {len(df[df['wrong_count'] > 0])} 词</div>", unsafe_allow_html=True)
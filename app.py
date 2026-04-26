import streamlit as st
import pandas as pd
import os
import time  
import re  # 【新增】：正则表达式，用于精准扫描单词，防止误伤
from gtts import gTTS

# ==========================================
# 0. 网页全局设置 (原版保留)
# ==========================================
st.set_page_config(page_title="极客词汇系统", page_icon="📝", layout="centered", initial_sidebar_state="expanded")

# ==========================================
# 0.5 终极前端黑魔法 (UI 劫持 - 原版保留)
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
# 1. 数据初始化与状态管理
# ==========================================
if not os.path.exists('words.csv'):
    pd.DataFrame([{'word': 'apple', 'definition': '苹果', 'wrong_count': 0, 'phonetic': '/ˈæpl/'}]).to_csv('words.csv', index=False)

if not os.path.exists('essays.csv'):
    pd.DataFrame([
        {'category': '开头', 'subcategory': '建议信', 'content': 'I am writing to express my views concerning...', 'translation': '我写信是想表达关于……的看法。'},
        {'category': '结尾', 'subcategory': '通用', 'content': 'Looking forward to your prompt reply.', 'translation': '期待你的及时回复。'}
    ]).to_csv('essays.csv', index=False)

# 【核心手术点 1】：初始化“词汇升格字典” (upgrade.csv)
if not os.path.exists('upgrade.csv'):
    pd.DataFrame([
        {'basic': 'good', 'advanced': 'excellent / outstanding', 'reason': 'good 太过口语化'},
        {'basic': 'bad', 'advanced': 'detrimental / negative', 'reason': 'bad 缺乏学术感'},
        {'basic': 'very', 'advanced': 'exceedingly / extremely', 'reason': 'very 是初中词汇'},
        {'basic': 'important', 'advanced': 'crucial / of great significance', 'reason': 'important 使用频率过高，易让阅卷老师审美疲劳'},
        {'basic': 'think', 'advanced': 'hold the view that / maintain', 'reason': 'think 过于主观随意'}
    ]).to_csv('upgrade.csv', index=False)

if 'current_word' not in st.session_state:
    st.session_state.current_word = ""; st.session_state.chinese_meaning = ""
    st.session_state.phonetic = ""; st.session_state.feedback = ""
    st.session_state.perfect_hit = False; st.session_state.quarantine_list = [] 
if 'essay_draft' not in st.session_state:
    st.session_state.essay_draft = ""

# ==========================================
# 2. 核心交互函数 (原版保留)
# ==========================================
def append_to_draft(text_to_add):
    st.session_state.essay_draft += text_to_add + " "

def get_next_word(mode):
    df = pd.read_csv('words.csv')
    if st.session_state.quarantine_list:
        df = df[~df['word'].isin(st.session_state.quarantine_list)]
    if mode == "错题大扫除":
        df_to_test = df[df['wrong_count'] > 0]
        if df_to_test.empty:
            st.session_state.current_word = ""; st.session_state.feedback = "⏳ 本轮错题已复习完毕！" if st.session_state.quarantine_list else "🎉 错题本空空如也！"
            return
    else: df_to_test = df
    if df_to_test.empty: return
    row = df_to_test.sample(n=1).iloc[0]
    st.session_state.current_word = row['word']; st.session_state.chinese_meaning = row['definition']
    st.session_state.phonetic = row['phonetic'] if 'phonetic' in row else ""

def check_answer():
    user_input = st.session_state.user_input.strip().lower()
    mode = st.session_state.mode_selector
    if not user_input or not st.session_state.current_word: return
    df = pd.read_csv('words.csv')
    correct_word = st.session_state.current_word
    if user_input == correct_word:
        st.session_state.perfect_hit = True; st.session_state.feedback = ""      
        if mode == "错题大扫除": df.loc[df['word'] == correct_word, 'wrong_count'] = 0
    else:
        st.session_state.feedback = f"❌ 正确拼写: {correct_word}"
        df.loc[df['word'] == correct_word, 'wrong_count'] += 1
        if correct_word not in st.session_state.quarantine_list: st.session_state.quarantine_list.append(correct_word)
    df.to_csv('words.csv', index=False)
    st.session_state.user_input = ""; get_next_word(mode) 

# ==========================================
# 3. 侧边栏多功能导航台 (原版保留)
# ==========================================
with st.sidebar:
    st.markdown("<h2 style='text-align: center; color: #111827;'>🛠️ 控制中心</h2>", unsafe_allow_html=True)
    app_mode = st.selectbox("请选择功能模块：", ["单词通关挑战", "写作灵感工坊"])
    st.divider()
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

# ==========================================
# 4. 主界面渲染逻辑
# ==========================================
if app_mode == "单词通关挑战":
    if st.session_state.perfect_hit:
        unique_id = str(time.time()).replace('.', '') 
        st.markdown(PERFECT_CSS_TEMPLATE.replace("UID", unique_id), unsafe_allow_html=True)
        st.session_state.perfect_hit = False 
    mode = st.radio(" ", ["全局摸底考", "错题大扫除"], horizontal=True, key="mode_selector", label_visibility="collapsed")
    if st.button("🚀 开始测试", use_container_width=True):
        st.session_state.quarantine_list = []; get_next_word(mode)
    if st.session_state.feedback:
        if "✨" in st.session_state.feedback: st.success(st.session_state.feedback)
        else: st.error(st.session_state.feedback)
    if st.session_state.current_word:
        st.markdown(f"<div style='text-align:center;margin:40px 0;'><div style='font-size:2.5rem;font-weight:900;color:#111827;'>{st.session_state.chinese_meaning}</div><div style='font-size:1.2rem;color:#6B7280;margin-top:10px;'>{st.session_state.phonetic}</div></div>", unsafe_allow_html=True)
        tts = gTTS(st.session_state.current_word, lang='en')
        tts.save("temp.mp3"); st.audio("temp.mp3", format="audio/mp3", autoplay=True)
        st.text_input(" ", key="user_input", on_change=check_answer, placeholder="Type here...", label_visibility="collapsed")

else:
    st.markdown("<h1 style='text-align: center; color: #111827;'>✍️ 写作灵感工坊</h1>", unsafe_allow_html=True)
    
    with st.container():
        st.markdown("<p style='color: #6B7280; font-size: 0.9rem; margin-bottom: 5px;'>📝 我的作文草稿:</p>", unsafe_allow_html=True)
        st.text_area(" ", height=200, key="essay_draft", label_visibility="collapsed")
        
        # 【核心手术点 2】：植入“降维平替雷达”按钮
        col_scan, col_empty = st.columns([1, 2])
        with col_scan:
            scan_btn = st.button("🔍 扫描低级词汇", use_container_width=True)

        # 雷达扫描逻辑：
        if scan_btn and st.session_state.essay_draft.strip():
            draft_text = st.session_state.essay_draft.lower()
            df_upgrade = pd.read_csv('upgrade.csv')
            found_words = []
            
            # 用正则寻找独立的单词，防止把 "goodness" 误判为 "good"
            for _, row in df_upgrade.iterrows():
                basic_word = row['basic']
                if re.search(r'\b' + re.escape(basic_word) + r'\b', draft_text):
                    found_words.append(row)
            
            if not found_words:
                st.success("🎉 太棒了！没有检测到常见的低级词汇，继续保持！")
            else:
                st.warning(f"⚠️ 滴滴滴！雷达发现了 {len(found_words)} 处可以升格的低级词汇：")
                for item in found_words:
                    st.markdown(f"""
                    <div style='background-color: #FFFBEB; padding: 15px; border-radius: 10px; border-left: 4px solid #F59E0B; margin-bottom: 10px;'>
                        <span style='color: #B45309; font-weight: bold; text-decoration: line-through;'>{item['basic']}</span> 
                        👉 <span style='color: #059669; font-weight: bold; font-size: 1.1rem;'>{item['advanced']}</span>
                        <div style='font-size: 0.85rem; color: #6B7280; margin-top: 5px;'>💡 {item['reason']}</div>
                    </div>
                    """, unsafe_allow_html=True)
    
    st.divider()

    # (下方选项卡原版保留)
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
                    if 'search_query' in locals() and search_query:
                        if search_query.lower() not in row['content'].lower() and search_query not in row['translation']:
                            continue
                    with st.container():
                        st.markdown(f"""
                        <div style='background: white; padding: 20px; border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.02); border-left: 5px solid #3B82F6;'>
                            <div style='font-family: serif; font-size: 1.1rem; color: #111827;'>{row['content']}</div>
                            <div style='color: #6B7280; font-size: 0.85rem; margin-top: 8px;'>{row['translation']}</div>
                        </div>
                        """, unsafe_allow_html=True)
                        col1, col2 = st.columns([4, 1])
                        with col2:
                            st.button("➕ 添加", key=f"add_{idx}", on_click=append_to_draft, args=(row['content'],))
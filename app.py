import streamlit as st
import pandas as pd
import os
import time  
from gtts import gTTS

# ==========================================
# 0. 网页全局设置
# ==========================================
st.set_page_config(page_title="极客词汇系统", page_icon="📝", layout="centered")

# ==========================================
# 0.5 暴击特效黑魔法 (CSS3 动画 - 绝对原版保留)
# ==========================================
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
    position: fixed;
    top: 35%;
    left: 50%;
    z-index: 999999;
    font-family: 'Impact', 'Arial Black', sans-serif;
    font-size: 110px;
    color: #FFDF00;
    font-style: italic;
    font-weight: 900;
    -webkit-text-stroke: 4px #D32F2F;
    text-transform: uppercase;
    pointer-events: none; 
    animation: criticalHit_UID 0.9s cubic-bezier(0.25, 0.46, 0.45, 0.94) forwards;
}
</style>
<div class="monster-kill-text-UID">PERFECT!</div>
"""

# ==========================================
# 1. 数据初始化与状态管理
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
    # 【手术点 1】：在后台建立一个隐形的“隔离区”
    st.session_state.quarantine_list = [] 

# ==========================================
# 2. 核心交互函数 (精准逻辑升级)
# ==========================================
def get_next_word(mode):
    df = pd.read_csv('words.csv')
    
    # 【手术点 2】：抽题前，强制过滤掉所有在“隔离区”里的单词！
    if st.session_state.quarantine_list:
        df = df[~df['word'].isin(st.session_state.quarantine_list)]

    if mode == "错题大扫除":
        df_to_test = df[df['wrong_count'] > 0]
        if df_to_test.empty:
            st.session_state.current_word = ""
            # 智能判断：是真的没错题了，还是本轮错题全进隔离区了？
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
        st.session_state.feedback = f"❌ 遗憾！【{st.session_state.chinese_meaning}】的正确拼写是: **{correct_word}**"
        df.loc[df['word'] == correct_word, 'wrong_count'] += 1
        
        # 【手术点 3】：只要答错，立刻关进“隔离区”，本轮不再出现！
        if correct_word not in st.session_state.quarantine_list:
            st.session_state.quarantine_list.append(correct_word)
        
    df.to_csv('words.csv', index=False)
    st.session_state.user_input = "" 
    get_next_word(mode) 

# ==========================================
# 3. 绘制网页 UI (原版保留)
# ==========================================
if st.session_state.perfect_hit:
    unique_id = str(time.time()).replace('.', '') 
    dynamic_css = PERFECT_CSS_TEMPLATE.replace("UID", unique_id) 
    st.markdown(dynamic_css, unsafe_allow_html=True)
    st.session_state.perfect_hit = False 

st.title("✨ 英语词汇智能筛查 Web 版")

mode = st.radio("选择测试模式：", ["全局摸底考", "错题大扫除"], horizontal=True, key="mode_selector")

if st.button("🚀 开始测试 / 手动切题", use_container_width=True):
    st.session_state.feedback = "" 
    # 如果用户手动点击了“开始测试”，我们默认他想开启新一轮，清空隔离区
    st.session_state.quarantine_list = []
    get_next_word(mode)

# 【新增 UI】：只有当词被抽干，且隔离区有词时，才会显示这个专属的“新一轮”按钮
if not st.session_state.current_word and len(st.session_state.quarantine_list) > 0:
    if st.button("🔄 开启新一轮 (重置冷却)", use_container_width=True):
        st.session_state.quarantine_list = []
        st.session_state.feedback = ""
        get_next_word(mode)

st.divider() 

if st.session_state.feedback:
    if "❌" in st.session_state.feedback:
        st.error(st.session_state.feedback)
    elif "⏳" in st.session_state.feedback:
        st.warning(st.session_state.feedback)
    else:
        st.success(st.session_state.feedback)

if st.session_state.current_word:
    st.header(f"释义: {st.session_state.chinese_meaning}")
    
    tts = gTTS(st.session_state.current_word, lang='en')
    tts.save("temp.mp3")
    st.audio("temp.mp3", format="audio/mp3", autoplay=True)
    
    st.text_input("请输入单词英文（按回车提交）：", key="user_input", on_change=check_answer)

df = pd.read_csv('words.csv')
st.caption(f"📊 词库总量: {len(df)} 词   |   🔥 待消灭错题: {len(df[df['wrong_count'] > 0])} 词")
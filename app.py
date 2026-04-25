import streamlit as st
import pandas as pd
import os
from gtts import gTTS

# ==========================================
# 0. 网页全局设置
# ==========================================
st.set_page_config(page_title="极客词汇系统", page_icon="📝", layout="centered")

# ==========================================
# 1. 数据初始化与状态管理 (Session State)
# ==========================================
# 检查并初始化单词本
if not os.path.exists('words.csv'):
    df = pd.DataFrame([
        {'word': 'apple', 'definition': '苹果', 'wrong_count': 0},
        {'word': 'banana', 'definition': '香蕉', 'wrong_count': 0},
        {'word': 'study', 'definition': '学习', 'wrong_count': 1}
    ])
    df.to_csv('words.csv', index=False)

# 在网页中，每次点击都会重新加载页面，所以必须用 session_state 记住当前考到哪了
if 'current_word' not in st.session_state:
    st.session_state.current_word = ""
    st.session_state.chinese_meaning = ""
    st.session_state.feedback = ""

# ==========================================
# 2. 核心交互函数
# ==========================================
def get_next_word(mode):
    df = pd.read_csv('words.csv')
    if mode == "错题大扫除":
        df_to_test = df[df['wrong_count'] > 0]
        if df_to_test.empty:
            st.session_state.current_word = ""
            st.session_state.feedback = "🎉 错题本空空如也！请切换全局模式。"
            return
    else:
        df_to_test = df

    row = df_to_test.sample(n=1).iloc[0]
    st.session_state.current_word = row['word']
    st.session_state.chinese_meaning = row['definition']
    st.session_state.feedback = "" # 清空上一题的反馈

def check_answer():
    user_input = st.session_state.user_input.strip().lower()
    mode = st.session_state.mode_selector
    
    if not user_input or not st.session_state.current_word:
        return

    df = pd.read_csv('words.csv')
    correct_word = st.session_state.current_word

    if user_input == correct_word:
        st.session_state.feedback = f"✅ 【{correct_word}】回答正确！"
        if mode == "错题大扫除" and df.loc[df['word'] == correct_word, 'wrong_count'].iloc[0] > 0:
            df.loc[df['word'] == correct_word, 'wrong_count'] = 0
    else:
        st.session_state.feedback = f"❌ 错了！【{st.session_state.chinese_meaning}】正确拼写是: {correct_word}"
        df.loc[df['word'] == correct_word, 'wrong_count'] += 1

    df.to_csv('words.csv', index=False)
    st.session_state.user_input = "" # 自动清空输入框
    get_next_word(mode) # 自动抽取下一题

# ==========================================
# 3. 绘制网页 UI (Streamlit 的魔法)
# ==========================================
st.title("✨ 英语词汇智能筛查 Web 版")

# 模式选择器
mode = st.radio("选择测试模式：", ["全局摸底考", "错题大扫除"], horizontal=True, key="mode_selector")

# 发令枪按钮
if st.button("🚀 开始测试 / 手动切题", use_container_width=True):
    get_next_word(mode)

st.divider() # 画一条分割线

# 只有当抽了题之后，才显示答题区
if st.session_state.current_word:
    st.header(f"释义: {st.session_state.chinese_meaning}")
    
    # 动态生成发音 MP3 并推送到浏览器
    tts = gTTS(st.session_state.current_word, lang='en')
    tts.save("temp.mp3")
    st.audio("temp.mp3", format="audio/mp3", autoplay=True)
    
    # 极简输入框：按下回车自动触发 on_change 绑定的 check_answer 函数
    st.text_input("请输入单词英文（按回车提交）：", key="user_input", on_change=check_answer)

# 显示上一题的判分结果
if st.session_state.feedback:
    if "✅" in st.session_state.feedback or "🎉" in st.session_state.feedback:
        st.success(st.session_state.feedback)
    else:
        st.error(st.session_state.feedback)

# 实时战况板
df = pd.read_csv('words.csv')
st.caption(f"📊 词库总量: {len(df)} 词   |   🔥 待消灭错题: {len(df[df['wrong_count'] > 0])} 词")
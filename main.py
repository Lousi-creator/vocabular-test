import customtkinter as ctk
import tkinter as tk
import pandas as pd
import pyttsx3
import os

# ==========================================
# 0. UI 主题全局设置 (现代感的核心)
# ==========================================
ctk.set_appearance_mode("System")  # 自动跟随系统的主题（深色/浅色）
ctk.set_default_color_theme("blue")  # 核心高亮颜色

# ==========================================
# 1. 引擎初始化
# ==========================================
engine = pyttsx3.init()
current_word = ""

if not os.path.exists('words.csv'):
    df = pd.DataFrame([
        {'word': 'apple', 'definition': '苹果', 'wrong_count': 0},
        {'word': 'banana', 'definition': '香蕉', 'wrong_count': 0},
        {'word': 'study', 'definition': '学习', 'wrong_count': 1}
    ])
    df.to_csv('words.csv', index=False)

# ==========================================
# 2. 核心交互函数 (保留了你V3.2的严谨逻辑)
# ==========================================

def update_stats():
    """更新底部的实时数据统计面板"""
    if os.path.exists('words.csv'):
        df = pd.read_csv('words.csv')
        total_words = len(df)
        wrong_words = len(df[df['wrong_count'] > 0])
        lbl_stats.configure(text=f"📊 词库总量: {total_words} 词   |   🔥 待消灭错题: {wrong_words} 词")

def play_sound():
    global current_word
    if current_word:
        local_engine = pyttsx3.init()
        local_engine.say(current_word)
        local_engine.runAndWait()

def get_next_word():
    global current_word
    
    # 隐藏开始按钮
    btn_start.pack_forget()
    main_card.pack(pady=20, padx=20, fill="both", expand=True) # 显示中央答题卡片
    
    df = pd.read_csv('words.csv')
    current_mode = seg_button_var.get() # 读取现代切换器的值
    
    if current_mode == "错题大扫除":
        df_to_test = df[df['wrong_count'] > 0]
        if df_to_test.empty:
            lbl_feedback.configure(text="🎉 错题本空空如也！你太棒了！", text_color="#2ECC71")
            lbl_meaning.configure(text="无错题", font=("Arial", 20))
            current_word = ""
            entry_word.configure(state="disabled")
            return
    else:
        df_to_test = df

    row = df_to_test.sample(n=1).iloc[0]
    current_word = row['word']
    chinese_meaning = row['definition']
    
    # 刷新卡片 UI
    lbl_meaning.configure(text=f"{chinese_meaning}", font=("Microsoft YaHei UI", 28, "bold"))
    lbl_feedback.configure(text="请听音输入，按 回车键 提交", text_color="gray")
    
    entry_word.configure(state="normal")
    entry_word.delete(0, "end")
    entry_word.focus() 
    
    engine.say(current_word)
    engine.say(current_word)
    engine.runAndWait()

def on_mode_change(value):
    """当切换模式时，立刻刷新界面"""
    # 只有当卡片已经显示（即测验已开始）时，才触发新题
    if main_card.winfo_ismapped():
        entry_word.configure(state="normal")
        entry_word.focus()
        get_next_word()

def check_answer(event=None): 
    global current_word
    if not current_word:
        return

    user_input = entry_word.get().strip().lower()
    if user_input == "":
        lbl_feedback.configure(text="⚠️ 请输入单词！不要交白卷哦", text_color="#F39C12")
        return

    df = pd.read_csv('words.csv')
    wait_time = 0 
    current_mode = seg_button_var.get()
    
    if user_input == current_word:
        lbl_feedback.configure(text="✅ 完美命中！准备下一题...", text_color="#2ECC71", font=("Microsoft YaHei", 16, "bold"))
        if current_mode == "错题大扫除" and df.loc[df['word'] == current_word, 'wrong_count'].iloc[0] > 0:
            df.loc[df['word'] == current_word, 'wrong_count'] = 0
        wait_time = 800
    else:
        lbl_feedback.configure(text=f"❌ 错了！正确拼写: {current_word}", text_color="#E74C3C", font=("Microsoft YaHei", 18, "bold"))
        df.loc[df['word'] == current_word, 'wrong_count'] += 1
        wait_time = 2500 
    
    df.to_csv('words.csv', index=False)
    update_stats() # 每次答完题，实时刷新底部的战况板
    
    entry_word.configure(state="disabled")
    app.after(wait_time, get_next_word)


# ==========================================
# 3. 绘制现代主义用户界面
# ==========================================

# 创建现代主窗口
app = ctk.CTk()
app.title("高考词汇极客版 (Focus Mode)")
app.geometry("450x500")

# --- 顶部：标题与模式切换 ---
lbl_title = ctk.CTkLabel(app, text="✨ 词汇筛查系统", font=("Microsoft YaHei UI", 24, "bold"))
lbl_title.pack(pady=(20, 10))

seg_button_var = ctk.StringVar(value="全局摸底考")
seg_button = ctk.CTkSegmentedButton(app, values=["全局摸底考", "错题大扫除"], 
                                    variable=seg_button_var, 
                                    command=on_mode_change,
                                    font=("Microsoft YaHei", 14),
                                    selected_color="#3498DB",
                                    selected_hover_color="#2980B9")
seg_button.pack(pady=10)

# --- 发令枪按钮 ---
btn_start = ctk.CTkButton(app, text="🚀 开始专注测试", command=get_next_word, 
                          font=("Microsoft YaHei", 16, "bold"), height=50, corner_radius=25,
                          fg_color="#2ECC71", hover_color="#27AE60")
btn_start.pack(pady=40)

# --- 中部：沉浸式专注卡片 (默认隐藏，开始后显示) ---
main_card = ctk.CTkFrame(app, corner_radius=15, fg_color=("gray90", "gray15"))

lbl_meaning = ctk.CTkLabel(main_card, text="", text_color=("black", "white"))
lbl_meaning.pack(pady=(30, 10))

btn_play = ctk.CTkButton(main_card, text="🔊 重新发音", command=play_sound, 
                         width=100, height=30, corner_radius=15, fg_color="transparent", 
                         border_width=1, text_color=("gray30", "gray70"))
btn_play.pack(pady=5)

entry_word = ctk.CTkEntry(main_card, font=("Helvetica", 24), width=280, height=50, 
                          justify="center", corner_radius=10, placeholder_text="Type here...")
entry_word.pack(pady=(20, 10))

lbl_feedback = ctk.CTkLabel(main_card, text="", font=("Microsoft YaHei", 14))
lbl_feedback.pack(pady=(0, 20))

app.bind('<Return>', check_answer)

# --- 底部：实时战况数据板 ---
lbl_stats = ctk.CTkLabel(app, text="", font=("Microsoft YaHei", 12), text_color="gray")
lbl_stats.pack(side="bottom", pady=20)
update_stats() # 软件刚打开时读取一次数据

app.mainloop()
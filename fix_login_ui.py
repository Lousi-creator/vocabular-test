import re

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Fix subtitle
content = content.replace(
    'AI 驱动的高考英语智能训练舱',
    'Your AI study buddy for Gaokao \u270c\ufe0f'
)

# 2. Fix motivational card - top line
content = content.replace(
    '\u26a1 路虽远，行则将至；词虽难，练则必通',
    '\u2726 Dream big. Study smart. Ace it.'
)

# 3. Fix motivational card - bottom line  
content = content.replace(
    '每一次积累，都在为六月的梦想蓄力<br>今天的努力，是明天考场上的从容',
    'Every word you learn today <br>is a step closer to your dream university \U0001f393'
)

# 4. Fix tabs
content = content.replace(
    'st.tabs([" Welcome back!", " Join the club"])',
    'st.tabs(["\U0001f44b Welcome back!", "\u2728 Join the club"])'
)

# 5. Fix login fields
content = content.replace(
    'st.text_input("用户名", key="log_u", placeholder="输入账号")',
    'st.text_input("Username", key="log_u", placeholder="Enter your username")'
)
content = content.replace(
    'st.text_input("安全密码", type="password", key="log_p", placeholder="\u2022\u2022\u2022\u2022\u2022\u2022\u2022\u2022")',
    'st.text_input("Password", type="password", key="log_p", placeholder="\u2022\u2022\u2022\u2022\u2022\u2022\u2022\u2022")'
)

# 6. Fix login button
content = content.replace(
    'st.button("\U0001f525 进入训练", use_container_width=True, type="primary")',
    'st.button("\U0001f680 Let\'s roll!", use_container_width=True, type="primary")'
)

# 7. Fix pending warning
content = content.replace(
    'st.warning("\u23f3 你的账号正在等待管理员审核，请耐心等待。")',
    'st.warning("\u23f3 Hang tight! 管理员还在审核你的账号~")'
)

# 8. Fix login error
content = content.replace(
    'st.error("用户名或密码不匹配")',
    'st.error("Oops! 用户名或密码不对哦~")'
)

# 9. Fix reg fields
content = content.replace(
    'st.text_input("设置用户名", key="reg_u", placeholder="取一个响亮的名号")',
    'st.text_input("Pick a username", key="reg_u", placeholder="Make it cool \U0001f60e")'
)
content = content.replace(
    'st.text_input("设置高强度密码", type="password", key="reg_p", placeholder="设置你的安全密码")',
    'st.text_input("Create a password", type="password", key="reg_p", placeholder="Make it strong \U0001f4aa")'
)

# 10. Fix reg button
content = content.replace(
    'st.button("\U0001f4aa 提交申请，加入备战", use_container_width=True)',
    'st.button("\U0001f389 Count me in!", use_container_width=True)'
)

# 11. Fix reg success
content = content.replace(
    'st.success("\U0001f389 注册请求已发送！管理员审核通过后即可开始训练。")',
    'st.success("\U0001f389 You\'re almost there! 等管理员通过就能开练啦~")'
)

# 12. Fix reg name taken
content = content.replace(
    'st.error("该用户名已被占用，换一个吧")',
    'st.error("Uh-oh! 这个名字被抢了，换一个吧~")'
)

# 13. Fix reg empty fields
content = content.replace(
    'st.warning("请填写完整的注册信息")',
    'st.warning("Hey, 用户名和密码都得填哦~")'
)

# 14. Fix title font size
content = content.replace(
    "font-size: 3.2rem; margin-bottom: 0; letter-spacing: 2px;",
    "font-size: 3.4rem; margin-bottom: 0; letter-spacing: 2px;"
)

# 15. Fix subtitle font style
content = content.replace(
    "font-size: 1.05rem; margin-top: 8px;",
    "font-size: 1rem; margin-top: 6px; font-style: italic;"
)

# 16. Fix moto card padding
content = content.replace(
    "padding: 22px 24px; margin-bottom: 28px;",
    "padding: 20px 24px; margin-bottom: 28px;"
)

# 17. Fix moto top line style
content = content.replace(
    "font-size: 1.15rem; font-weight: 700; color: #f8fafc; margin: 0 0 8px 0;",
    "font-size: 1.1rem; font-weight: 600; color: #f1f5f9; margin: 0 0 6px 0;"
)

# 18. Fix moto bottom line style
content = content.replace(
    "font-size: 0.88rem;",
    "font-size: 0.85rem;"
)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("All fixes applied!")

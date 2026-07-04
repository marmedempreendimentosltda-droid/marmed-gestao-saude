def login_page():
    st.markdown("""
        <style>
        .stApp { 
            background: linear-gradient(135deg, #0f172a, #1e3a8a, #0f172a) !important; 
            overflow: hidden;
        }
        div[data-testid="column"]:nth-child(2) {
            background: rgba(15, 23, 42, 0.75) !important;
            backdrop-filter: blur(16px) !important;
            -webkit-backdrop-filter: blur(16px) !important;
            border: 1px solid rgba(14, 165, 233, 0.3) !important;
            border-radius: 24px !important;
            padding: 48px 40px !important;
            box-shadow: 0 20px 60px rgba(0,0,0,0.5) !important;
            margin-top: 120px !important;
            max-width: 420px !important;
            margin-left: auto !important;
            margin-right: auto !important;
        }
        .marmed-title {
            font-size: 52px; font-weight: 800; text-align: center;
            color: #e0f2fe; letter-spacing: 6px;
            text-shadow: 0 0 20px rgba(14, 165, 233, 0.6);
            margin-bottom: 8px;
        }
        .subtitle {
            text-align: center; color: #7dd3fc; font-size: 14px;
            letter-spacing: 4px; margin-bottom: 36px; text-transform: uppercase;
        }
        .stTextInput label {
            color: #22d3ee !important; font-weight: 600; font-size: 13px; letter-spacing: 1px;
        }
        .stTextInput > div > div > input {
            background: rgba(30, 41, 59, 0.8) !important;
            border: 1px solid rgba(34, 211, 238, 0.3) !important;
            color: #e0f2fe !important; border-radius: 10px !important;
        }
        .stButton > button {
            background: linear-gradient(90deg, #06b6d4, #3b82f6) !important;
            color: #fff !important; font-weight: 700 !important;
            border-radius: 10px !important; border: none !important;
            width: 100%; padding: 12px !important; letter-spacing: 2px;
        }
        </style>
    """, unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div class="marmed-title">MARMED</div>', unsafe_allow_html=True)
        st.markdown('<div class="subtitle">SISTEMA INTEGRADO DE GESTAO</div>', unsafe_allow_html=True)
        username = st.text_input("USUARIO", key="login_user")
        password = st.text_input("SENHA", type="password", key="login_pass")
        if st.button("Acessar", key="login_btn"):
            pw_hash = hashlib.sha256(password.encode()).hexdigest()
            conn = sqlite3.connect("marmed.db")
            c = conn.cursor()
            c.execute("SELECT * FROM users WHERE username=? AND password_hash=?", (username, pw_hash))
            user = c.fetchone()
            conn.close()
            if user:
                st.session_state["logged_in"] = True
                st.session_state["username"] = username
                st.session_state["page"] = "Dashboard"
                st.rerun()
            else:
                st.error("Usuario ou senha invalidos")
        st.markdown('<div style="text-align:center;color:#94a3b8;font-size:12px;margin-top:28px;">Acesso restrito a usuarios autorizados</div>', unsafe_allow_html=True)

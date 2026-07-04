import hashlib
import sqlite3
import random


def login_page():
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700&display=swap');
        .stApp {
            background: linear-gradient(135deg, #0d1117 0%, #161b22 50%, #0a0c10 100%) !important;
            overflow: hidden;
        }
        .card-container {
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            width: 420px;
            padding: 48px 40px;
            background: rgba(255, 255, 255, 0.06);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.12);
            border-radius: 24px;
            box-shadow: 0 25px 80px rgba(0, 0, 0, 0.5), inset 0 1px 0 rgba(255, 255, 255, 0.1);
            text-align: center;
            z-index: 10;
        }
        .title-marmed {
            font-family: 'Montserrat', sans-serif;
            font-size: 42px;
            font-weight: 700;
            color: #ffffff;
            letter-spacing: 3px;
            margin-bottom: 8px;
            text-shadow: 0 0 30px rgba(6, 182, 212, 0.4);
        }
        .subtitle {
            font-family: 'Montserrat', sans-serif;
            font-size: 13px;
            font-weight: 600;
            color: #94a3b8;
            letter-spacing: 2px;
            margin-bottom: 36px;
            text-transform: uppercase;
        }
        .input-label {
            display: block;
            text-align: left;
            font-family: 'Montserrat', sans-serif;
            font-size: 12px;
            font-weight: 600;
            color: #22d3ee;
            margin-bottom: 8px;
            letter-spacing: 1px;
            text-transform: uppercase;
        }
        .login-input input {
            background: rgba(0, 0, 0, 0.25) !important;
            border: 1px solid rgba(34, 211, 238, 0.3) !important;
            border-radius: 12px !important;
            color: #ffffff !important;
            padding: 14px 16px !important;
            font-family: 'Montserrat', sans-serif !important;
            font-size: 14px !important;
            width: 100% !important;
        }
        .login-input input:focus {
            border-color: #22d3ee !important;
            box-shadow: 0 0 15px rgba(34, 211, 238, 0.2) !important;
            outline: none !important;
        }
        .login-btn {
            width: 100%;
            padding: 14px 24px;
            background: linear-gradient(135deg, #0891b2 0%, #22d3ee 100%);
            color: #0f172a;
            border: none;
            border-radius: 12px;
            font-family: 'Montserrat', sans-serif;
            font-size: 15px;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.3s ease;
            margin-top: 12px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .login-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 30px rgba(34, 211, 238, 0.3);
        }
        .bottom-text {
            font-family: 'Montserrat', sans-serif;
            font-size: 11px;
            color: #64748b;
            margin-top: 28px;
            letter-spacing: 0.5px;
        }
        .particle {
            position: fixed;
            border-radius: 50%;
            background: rgba(34, 211, 238, 0.15);
            pointer-events: none;
            animation: float 15s infinite linear;
            z-index: 1;
        }
        @keyframes float {
            0% { transform: translateY(100vh) translateX(0); opacity: 0; }
            10% { opacity: 1; }
            90% { opacity: 1; }
            100% { transform: translateY(-10vh) translateX(50px); opacity: 0; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    particles = ""
    for i in range(30):
        size = random.randint(2, 6)
        left = random.randint(0, 100)
        delay = random.uniform(0, 15)
        duration = random.uniform(10, 20)
        particles += f'<div class="particle" style="width:{size}px;height:{size}px;left:{left}%;animation-delay:{delay:.1f}s;animation-duration:{duration:.1f}s;"></div>'
    st.markdown(particles, unsafe_allow_html=True)
    st.markdown(
        """
        <div class="card-container">
            <div class="title-marmed">MARMED</div>
            <div class="subtitle">SISTEMA INTEGRADO DE GESTAO</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    card = st.container()
    with card:
        st.markdown('<div class="card-container">', unsafe_allow_html=True)
        st.markdown('<div class="title-marmed">MARMED</div>', unsafe_allow_html=True)
        st.markdown('<div class="subtitle">SISTEMA INTEGRADO DE GESTAO</div>', unsafe_allow_html=True)
        st.markdown('<label class="input-label">USUARIO</label>', unsafe_allow_html=True)
        username = st.text_input("", key="login_username", placeholder="Digite seu usuario", label_visibility="collapsed")
        st.markdown('<label class="input-label">SENHA</label>', unsafe_allow_html=True)
        password = st.text_input("", key="login_password", type="password", placeholder="Digite sua senha", label_visibility="collapsed")
        if st.button("Acessar", key="login_button", use_container_width=True):
            expected_hash = hashlib.sha256("Diretor2025#".encode()).hexdigest()
            provided_hash = hashlib.sha256(password.encode()).hexdigest()
            if username == "admin" and provided_hash == expected_hash:
                st.session_state.authenticated = True
                st.session_state.username = username
                st.rerun()
            else:
                st.error("Usuario ou senha invalidos")
        st.markdown('<div class="bottom-text">Acesso restrito a usuarios autorizados</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

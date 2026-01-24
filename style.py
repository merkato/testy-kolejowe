import streamlit as st

def apply_custom_css():
    """Wstrzykuje pastelowe style CSS do aplikacji."""
    pastel_css = """
    <style>
        /* GŁÓWNY STYL PRZYCISKÓW (Pastelowy Błękit) */
        div.stButton > button {
            background-color: #E3F2FD !important;
            color: #0D47A1 !important;
            border: 1px solid #BBDEFB !important;
            border-radius: 8px !important;
            font-weight: 600 !important;
            transition: all 0.2s ease;
        }
        div.stButton > button:hover {
            background-color: #BBDEFB !important;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }

        /* PRZYCISKI PRIMARY (Pastelowa Zieleń - np. Zapisz/Importuj) */
        div.stButton > button[kind="primary"] {
            background-color: #E8F5E9 !important;
            color: #1B5E20 !important;
            border: 1px solid #C8E6C9 !important;
        }

        /* PRZYCISK WYLOGUJ / DANGER (Pastelowy Koral) */
        [data-testid="stSidebar"] div.stButton > button {
            background-color: #FFEBEE !important;
            color: #B71C1C !important;
            border: 1px solid #FFCDD2 !important;
        }

        /* POPRAWA CZYTELNOŚCI TEKSTU W SIDEBARZE */
        [data-testid="stSidebar"] {
            color: #1c1c1c;
        }
        
        /* STYLIZACJA TABEL I PÓŁ WYBORU */
        .stDataFrame, div[data-baseweb="select"] {
            border-radius: 8px !important;
            overflow: hidden;
        }
    </style>
    """
    st.markdown(pastel_css, unsafe_allow_html=True)

def st_responsive_image(image_path, caption=None, width_percent=0.6):
    """
    Wyświetla obrazek responsywnie:
    - Na PC: zajmuje centralną część (domyślnie 60%)
    - Na Mobile: rozciąga się do 100%
    """
    if image_path:
        side_space = (1.0 - width_percent) / 2
        col1, col2, col3 = st.columns([side_space, width_percent, side_space])
        with col2:
            st.image(image_path, caption=caption, use_container_width=True)

def st_answer_layout(label, text, img_path=None):
    """Układ dla odpowiedzi A, B, C: Tekst obok obrazka."""
    col_text, col_img = st.columns([3, 1])
    with col_text:
        st.markdown(f"#### {label}) {text if text else ''}")
    with col_img:
        if img_path:
            st.image(img_path, use_container_width=True)
    st.divider()
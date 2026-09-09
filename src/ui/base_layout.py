import streamlit as st



def style_background_home():

    st.markdown("""
        <style>

                .stApp {
                    background: #5865F2 !important;
                }

                .stApp div[data-testid="stColumn"]{
                    background-color:#E0E3FF !important;
                    padding:2.5rem !important;
                    border-radius: 5rem !important;
                    }
        </style>  

                """
            ,unsafe_allow_html=True)
    

def style_background_dashboard():

    st.markdown("""
        <style>

                .stApp {
                    background: #E0E3FF !important;
                }

        </style>  

                """
            ,unsafe_allow_html=True)
    

    

def style_base_layout():
# asdasd
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Climate+Crisis:YEAR@1979&display=swap');
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@100..900&display=swap');

                
         /* Hide Top Bar of streamlit */
                
            #MainMenu, footer, header {
                visibility: hidden;
            }
                
            .block-container {
                padding-top:1.5rem !important;    
            }

            h1 {
                font-family: 'Outfit', sans-serif !important;
                font-weight: 800 !important;
                font-size: 2.8rem !important;
                color: #1E1E4B !important;
                line-height:1.1 !important;
                margin-bottom:0.5rem !important;
            }
                

            h2 {
                font-family: 'Outfit', sans-serif !important;
                font-weight: 700 !important;
                font-size: 2rem !important;
                color: #1E1E4B !important;
                line-height:1.2 !important;
                margin-bottom:0.5rem !important;
            }
                
            h3, h4, p {
                font-family: 'Outfit', sans-serif;    
                color: #1E1E4B !important;
            }

            /* --- Base Buttons --- */
            button,
            div.stButton > button,
            button[data-testid^="baseButton"] {
                border-radius: 1.5rem !important;
                background-color: #5865F2 !important;
                color: #FFFFFF !important;
                padding: 10px 20px !important;
                border: none !important;
                font-family: 'Outfit', sans-serif !important;
                font-weight: 600 !important;
                transition: transform 0.2s ease-in-out, background-color 0.2s ease-in-out, color 0.2s ease-in-out !important;
            }

            /* Primary button */
            button[kind="primary"],
            div.stButton > button[kind="primary"],
            button[data-testid="baseButton-primary"] {
                background-color: #5865F2 !important;
                color: #FFFFFF !important;
            }
            button[kind="primary"] p,
            button[kind="primary"] span,
            button[kind="primary"] div,
            div.stButton > button[kind="primary"] p,
            div.stButton > button[kind="primary"] span,
            button[data-testid="baseButton-primary"] p,
            button[data-testid="baseButton-primary"] span {
                color: #FFFFFF !important;
                font-weight: 600 !important;
            }

            /* Secondary button (Pink) */
            button[kind="secondary"],
            div.stButton > button[kind="secondary"],
            button[data-testid="baseButton-secondary"] {
                background-color: #EB459E !important;
                color: #FFFFFF !important;
            }
            button[kind="secondary"] p,
            button[kind="secondary"] span,
            button[kind="secondary"] div,
            div.stButton > button[kind="secondary"] p,
            div.stButton > button[kind="secondary"] span,
            button[data-testid="baseButton-secondary"] p,
            button[data-testid="baseButton-secondary"] span {
                color: #FFFFFF !important;
                font-weight: 600 !important;
            }

            /* Tertiary button (Unselected Nav Tabs / Neutral dark pill) */
            button[kind="tertiary"],
            div.stButton > button[kind="tertiary"],
            button[data-testid="baseButton-tertiary"] {
                background-color: #121324 !important;
                color: #FFFFFF !important;
            }
            button[kind="tertiary"] p,
            button[kind="tertiary"] span,
            button[kind="tertiary"] div,
            div.stButton > button[kind="tertiary"] p,
            div.stButton > button[kind="tertiary"] span,
            div.stButton > button[kind="tertiary"] div,
            button[data-testid="baseButton-tertiary"] p,
            button[data-testid="baseButton-tertiary"] span,
            button[data-testid="baseButton-tertiary"] div {
                color: #FFFFFF !important;
                font-weight: 600 !important;
            }

            /* Hover states */
            button:hover,
            div.stButton > button:hover,
            button[data-testid^="baseButton"]:hover {
                transform: scale(1.05) !important;
            }
            button[kind="primary"]:hover,
            div.stButton > button[kind="primary"]:hover,
            button[data-testid="baseButton-primary"]:hover {
                background-color: #4752C4 !important;
            }
            button[kind="primary"]:hover p,
            button[kind="primary"]:hover span,
            div.stButton > button[kind="primary"]:hover p,
            div.stButton > button[kind="primary"]:hover span {
                color: #FFFFFF !important;
            }
            button[kind="secondary"]:hover,
            div.stButton > button[kind="secondary"]:hover,
            button[data-testid="baseButton-secondary"]:hover {
                background-color: #D83389 !important;
            }
            button[kind="secondary"]:hover p,
            button[kind="secondary"]:hover span,
            div.stButton > button[kind="secondary"]:hover p,
            div.stButton > button[kind="secondary"]:hover span {
                color: #FFFFFF !important;
            }
            button[kind="tertiary"]:hover,
            div.stButton > button[kind="tertiary"]:hover,
            button[data-testid="baseButton-tertiary"]:hover {
                background-color: #2F3154 !important;
            }
            button[kind="tertiary"]:hover p,
            button[kind="tertiary"]:hover span,
            div.stButton > button[kind="tertiary"]:hover p,
            div.stButton > button[kind="tertiary"]:hover span {
                color: #FFFFFF !important;
            }

            /* --- Streamlit Tabs (AI Face Attendance & Voice Attendance) --- */
            div[data-testid="stTabs"] div[role="tablist"] {
                gap: 12px !important;
                border-bottom: none !important;
                padding-bottom: 4px !important;
            }
            div[data-testid="stTabs"] button[role="tab"] {
                border-radius: 1.5rem !important;
                padding: 10px 22px !important;
                border: 1.5px solid transparent !important;
                font-family: 'Outfit', sans-serif !important;
                font-size: 0.98rem !important;
                transition: transform 0.2s ease-in-out, background-color 0.2s ease-in-out, color 0.2s ease-in-out !important;
            }
            /* Active tab */
            div[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
                background-color: #5865F2 !important;
                border-color: #5865F2 !important;
            }
            div[data-testid="stTabs"] button[role="tab"][aria-selected="true"] p,
            div[data-testid="stTabs"] button[role="tab"][aria-selected="true"] span,
            div[data-testid="stTabs"] button[role="tab"][aria-selected="true"] div {
                color: #FFFFFF !important;
                font-weight: 700 !important;
            }
            /* Inactive tab */
            div[data-testid="stTabs"] button[role="tab"][aria-selected="false"] {
                background-color: #FFFFFF !important;
                border: 1.5px solid #C4C8F5 !important;
            }
            div[data-testid="stTabs"] button[role="tab"][aria-selected="false"] p,
            div[data-testid="stTabs"] button[role="tab"][aria-selected="false"] span,
            div[data-testid="stTabs"] button[role="tab"][aria-selected="false"] div {
                color: #1E1E4B !important;
                font-weight: 600 !important;
            }
            /* Tab hover */
            div[data-testid="stTabs"] button[role="tab"]:hover {
                transform: scale(1.04) !important;
            }
            div[data-testid="stTabs"] button[role="tab"][aria-selected="false"]:hover {
                background-color: #EEF0FF !important;
                border-color: #5865F2 !important;
            }
            div[data-testid="stTabs"] button[role="tab"][aria-selected="false"]:hover p,
            div[data-testid="stTabs"] button[role="tab"][aria-selected="false"]:hover span {
                color: #5865F2 !important;
            }
        </style>  

                """
            ,unsafe_allow_html=True)
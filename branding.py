# branding.py
import os, base64, streamlit as st

def brand_header(
    title="Stadt Essen · KI-Labor",
    subtitle="Verwaltungstexte in 3 Verständlichkeitsstufen",
    logo_path="assets/essen_logo.png",
    color="#004f9f"
):
    # CSS: Header + Umbruch für code/pre (kein horizontales Scrollen) + leichte Layout-Politur
    st.markdown(f"""
    <style>
      .essen-header {{
        position: sticky; top:0; z-index:999;
        background: linear-gradient(90deg, {color} 0%, #0a74da 100%);
        color:#fff; padding:14px 18px; border-radius:12px; margin-bottom:12px;
      }}
      .essen-header .row {{ display:flex; align-items:center; gap:12px; }}
      .essen-header h1 {{ margin:0; font-size:1.15rem; }}
      .essen-header p {{ margin:2px 0 0 0; opacity:.95; }}
      .essen-badge {{ margin-left:auto; background:rgba(255,255,255,.14); padding:4px 10px;
                      border-radius:999px; font-size:.8rem; }}
      /* Ergebnis immer umbrechen, kein horizontales Scrollen */
      pre, code, pre code {{
        white-space: pre-wrap !important;
        word-wrap: break-word !important;
        overflow-wrap: anywhere !important;
      }}
      .block-container{{ padding-top:0.8rem; }}
    </style>
    """, unsafe_allow_html=True)

    logo_html = ""
    if os.path.exists(logo_path):
        with open(logo_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        logo_html = f'<img src="data:image/png;base64,{b64}" style="height:42px;border-radius:6px;" />'

    st.markdown(f"""
    <div class="essen-header">
      <div class="row">
        {logo_html}
        <div>
          <h1>{title}</h1>
          <p>{subtitle}</p>
        </div>
        <div class="essen-badge">Demo · intern</div>
      </div>
    </div>
    """, unsafe_allow_html=True)
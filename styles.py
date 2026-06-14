def get_css(lang: str = "ar") -> str:
    is_rtl = lang == "ar"
    direction = "rtl" if is_rtl else "ltr"
    font_ar = "Cairo"
    font_en = "Inter"
    primary_font = font_ar if is_rtl else font_en
    font_import = (
        f"@import url('https://fonts.googleapis.com/css2?family={font_ar}:wght@400;600;700;900&"
        f"family={font_en}:wght@400;500;600;700;900&display=swap');"
    )

    score_border = "border-right" if is_rtl else "border-left"

    return f"""<style>
{font_import}

[class*="css"] {{ font-family: '{primary_font}', '{font_ar}', '{font_en}', sans-serif !important; }}

.main .block-container {{ direction: {direction}; }}
[data-testid="stSidebar"] > div {{ direction: {direction}; }}

.stApp {{ background: #060d1a; }}
.main {{ background: #060d1a; }}

.metric-card {{
    background: #0d1d32;
    border: 1px solid #152236;
    border-radius: 12px;
    padding: 16px;
    text-align: center;
    margin: 4px;
    transition: transform 0.2s, border-color 0.2s;
}}
.metric-card:hover {{
    border-color: #00c89644;
    transform: translateY(-2px);
}}
.score-good  {{ {score_border}: 4px solid #00c896 !important; }}
.score-warn  {{ {score_border}: 4px solid #f59e0b !important; }}
.score-bad   {{ {score_border}: 4px solid #ef4444 !important; }}

.progress-bar-container {{
    background: #152236;
    border-radius: 8px;
    height: 8px;
    margin: 6px 0;
    overflow: hidden;
}}
.progress-bar-fill {{
    height: 100%;
    border-radius: 8px;
    transition: width 1s ease;
}}

.score-hero {{
    background: linear-gradient(135deg, #0d1d32, #081425);
    border: 1px solid #152236;
    border-radius: 16px;
    padding: 28px;
    text-align: center;
}}

.alert-good    {{ background: #00c89618; border: 1px solid #00c89644; border-radius: 8px; padding: 12px; margin: 6px 0; }}
.alert-warning {{ background: #f59e0b18; border: 1px solid #f59e0b44; border-radius: 8px; padding: 12px; margin: 6px 0; }}
.alert-danger  {{ background: #ef444418; border: 1px solid #ef444444; border-radius: 8px; padding: 12px; margin: 6px 0; }}

.og-preview {{
    background: #fff;
    border: 1px solid #dadde1;
    border-radius: 8px;
    overflow: hidden;
    max-width: 500px;
    margin: 10px auto;
    direction: ltr;
}}
.og-preview img {{ width: 100%; height: 200px; object-fit: cover; background: #e2e8f0; }}
.og-preview-body {{ padding: 12px; }}
.og-preview-domain {{ color: #65676b; font-size: 12px; text-transform: uppercase; }}
.og-preview-title {{ color: #1c1e21; font-size: 16px; font-weight: 700; margin: 4px 0; }}
.og-preview-desc {{ color: #65676b; font-size: 14px; }}

section[data-testid="stSidebar"] {{ background: #0a1525 !important; }}
section[data-testid="stSidebar"] * {{ color: #e2e8f0 !important; }}
[data-testid="stAppDeployButton"] {{ display: none !important; }}
#MainMenu {{ visibility: hidden !important; }}
footer {{ visibility: hidden !important; }}
header {{ background-color: transparent !important; }}

[data-testid="collapsedControl"] {{
    position: fixed !important;
    top: 15px !important;
    left: 15px !important;
    display: flex !important;
    visibility: visible !important;
    opacity: 1 !important;
    z-index: 999999 !important;
    background-color: #1e293b !important;
    border: 1px solid #334155 !important;
    border-radius: 8px !important;
}}
</style>"""

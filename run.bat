@echo off
chcp 65001 > nul
title محلل SEO الذكي

echo.
echo  ╔══════════════════════════════════════╗
echo  ║       محلل SEO الذكي - SEO Pro       ║
echo  ╚══════════════════════════════════════╝
echo.

:: التحقق من Python
python --version > nul 2>&1
if errorlevel 1 (
    echo  ❌ Python غير مثبت على جهازك
    echo  حمّل Python من: https://www.python.org/downloads/
    echo  تأكد من تفعيل "Add Python to PATH" أثناء التثبيت
    pause
    exit
)

echo  ✅ Python موجود
echo.

:: تثبيت المكتبات
echo  ⟳ جاري تثبيت المكتبات المطلوبة...
pip install -r requirements.txt -q
echo  ✅ المكتبات جاهزة
echo.

:: تشغيل التطبيق
echo  🚀 جاري تشغيل محلل SEO الذكي...
echo  افتح المتصفح على: http://localhost:8501
echo.
start http://localhost:8501
streamlit run app.py

pause

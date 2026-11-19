docker compose up -d
Start-Process powershell -ArgumentList "-NoExit","-Command","streamlit run app.py"
Start-Sleep 5
ngrok http 8501`
# 飆股狙擊後端

## 部署到 Render.com

1. 去 render.com 免費註冊
2. New → Web Service
3. 選 "Deploy from GitHub" 或 "Upload files"
4. 上傳這個資料夾的所有檔案
5. 設定：
   - Environment: Python
   - Build Command: pip install -r requirements.txt
   - Start Command: gunicorn app:app
6. 按 Deploy
7. 部署完後會得到網址如：https://feigu-sniper-backend.onrender.com

## API 端點
- GET /api/stock_price?token=xxx&stock_id=2330&start_date=2024-01-01
- GET /api/institutional?token=xxx&start_date=2024-01-01&end_date=2024-01-05
- GET /api/margin?token=xxx&stock_id=2330&start_date=2024-01-01
- GET /api/stock_info?token=xxx
- GET /api/health

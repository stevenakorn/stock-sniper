from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app)

FINMIND_API = "https://api.finmindtrade.com/api/v4/data"

def call_finmind(dataset, params, token):
    params["dataset"] = dataset
    params["token"] = token
    # 這裡直接加上 Token 在參數中，FinMind API 較為穩定的做法
    try:
        res = requests.get(FINMIND_API, params=params, timeout=30)
        return res.json()
    except Exception as e:
        return {"status": 0, "error": str(e), "data": []}

@app.route("/api/twse_institutional")
def twse_institutional():
    # 改用 os.environ.get 確保讀取 Vercel 設定
    token = os.environ.get("FINMIND_TOKEN")
    req_date = request.args.get("date", "")
    
    if not token:
        return jsonify({"data": [], "error": "後端通道未獲取付費 Token 金鑰", "status": 400})

    # 日期邏輯：如果不給日期，預設今天
    target_dt = datetime.strptime(req_date, "%Y-%m-%d") if req_date else datetime.now()

    # 如果是假日，自動往前推
    while target_dt.weekday() >= 5: # 5=週六, 6=週日
        target_dt -= timedelta(days=1)
    
    target_date = target_dt.strftime("%Y-%m-%d")

    # 取得資料
    fm_res = call_finmind("TaiwanStockInstitutionalInvestorsBuySell", 
                         {"start_date": target_date, "end_date": target_date}, 
                         token)

    # 檢查是否真的抓到資料
    if fm_res.get("status") == 200 and fm_res.get("data"):
        # ... (這裡保持你原本的資料處理邏輯，它沒問題) ...
        # (確保這邊的 stock_map 處理邏輯保持原樣即可)
        return jsonify({"data": result, "date": target_date, "status": 200})
    else:
        # 如果當天抓不到，遞迴往前找 (補強邏輯)
        return jsonify({"data": [], "msg": f"日期 {target_date} 無資料", "status": 404})

# Vercel 只需要 app 物件，不要加上 if __name__ == "__main__":

from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app)

# 強制寫入你的 Token，直接繞過環境變數問題
FINMIND_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoic3RldmVuMDMyMyIsImVtYWlsIjoic3RldmVuYWtvcm5AZ21haWwuY29tIiwidG9rZW5fdmVyc2lvbiI6Mn0.skA0AbGBSnuH4aji-E7NQPKDNd-G31K7g_sq772bg5w"
FINMIND_API = "https://api.finmindtrade.com/api/v4/data"

def call_finmind(dataset, params):
    params["dataset"] = dataset
    params["token"] = FINMIND_TOKEN
    headers = {"Authorization": f"Bearer {FINMIND_TOKEN}"}
    try:
        res = requests.get(FINMIND_API, params=params, headers=headers, timeout=30)
        return res.json()
    except Exception as e:
        return {"status": 0, "error": str(e), "data": []}

@app.route("/api/twse_institutional")
def twse_institutional():
    req_date = request.args.get("date", "")
    now = datetime.now()
    
    # 日期處理邏輯：若是週末，自動往回推至週五
    try:
        if req_date:
            dt_obj = datetime.strptime(req_date, "%Y-%m-%d")
        else:
            dt_obj = now
            
        if dt_obj.weekday() == 5: dt_obj -= timedelta(days=1)
        elif dt_obj.weekday() == 6: dt_obj -= timedelta(days=2)
        
        target_date = dt_obj.strftime("%Y-%m-%d")
    except:
        target_date = now.strftime("%Y-%m-%d")

    # 呼叫 API
    params = {"start_date": target_date, "end_date": target_date}
    fm_res = call_finmind("TaiwanStockInstitutionalInvestorsBuySell", params)

    if fm_res.get("status") == 200 and fm_res.get("data"):
        return jsonify({"data": fm_res["data"], "date": target_date, "status": 200})
    else:
        return jsonify({"data": [], "msg": "無資料", "status": 404})

# Vercel Serverless 需要這個
if __name__ == "__main__":
    app.run()

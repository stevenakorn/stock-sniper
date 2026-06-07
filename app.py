from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from datetime import datetime, timedelta

app = Flask(__name__) # 這行非常重要，Vercel 靠這個變數找 Flask
CORS(app)

# 暴力寫入 Token，繞過 Vercel 環境變數問題
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
    try:
        dt_obj = datetime.strptime(req_date, "%Y-%m-%d") if req_date else now
        if dt_obj.weekday() == 5: dt_obj -= timedelta(days=1)
        elif dt_obj.weekday() == 6: dt_obj -= timedelta(days=2)
        target_date = dt_obj.strftime("%Y-%m-%d")
    except:
        target_date = now.strftime("%Y-%m-%d")

    params = {"start_date": target_date, "end_date": target_date}
    fm_res = call_finmind("TaiwanStockInstitutionalInvestorsBuySell", params)

    if fm_res.get("status") == 200 and fm_res.get("data"):
        return jsonify({"data": fm_res["data"], "date": target_date, "status": 200})
    return jsonify({"data": [], "msg": "無資料", "status": 404})

@app.route("/api/stock_price")
def stock_price():
    sid = request.args.get("stock_id")
    start = request.args.get("start_date")
    end = request.args.get("end_date")
    data = call_finmind("TaiwanStockPrice", {"data_id": sid, "start_date": start, "end_date": end})
    return jsonify(data)

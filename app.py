from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from datetime import datetime, timedelta
import os

app = Flask(__name__)
CORS(app)

# 1. 填入你的真實 Token (請務必將此字串更新為你官網申請到的代碼)
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

# 2. 籌碼資料路由 (法人合計)
@app.route("/api/twse_institutional")
def twse_institutional():
    req_date = request.args.get("date", datetime.now().strftime("%Y-%m-%d"))
    try:
        dt_obj = datetime.strptime(req_date, "%Y-%m-%d")
        if dt_obj.weekday() == 5: dt_obj -= timedelta(days=1)
        elif dt_obj.weekday() == 6: dt_obj -= timedelta(days=2)
        target_date = dt_obj.strftime("%Y-%m-%d")
    except:
        target_date = datetime.now().strftime("%Y-%m-%d")

    fm_res = call_finmind("TaiwanStockInstitutionalInvestorsBuySell", {"start_date": target_date, "end_date": target_date})

    if fm_res.get("status") == 200 and fm_res.get("data"):
        return jsonify({"data": fm_res["data"], "date": target_date, "status": 200})
    return jsonify({"data": [], "msg": "無資料", "status": 404})

# 3. 個股股價路由 (供掃描策略使用)
@app.route("/api/stock_price")
def stock_price():
    stock_id = request.args.get("stock_id")
    start = request.args.get("start_date")
    end = request.args.get("end_date")
    data = call_finmind("TaiwanStockPrice", {"data_id": stock_id, "start_date": start, "end_date": end})
    return jsonify(data)

# 4. 個股法人路由
@app.route("/api/institutional")
def institutional():
    stock_id = request.args.get("stock_id")
    start = request.args.get("start_date")
    end = request.args.get("end_date")
    data = call_finmind("TaiwanStockInstitutionalInvestorsBuySell", {"data_id": stock_id, "start_date": start, "end_date": end})
    return jsonify(data)

# 5. 個股融資路由
@app.route("/api/margin")
def margin():
    stock_id = request.args.get("stock_id")
    start = request.args.get("start_date")
    end = request.args.get("end_date")
    data = call_finmind("TaiwanStockMarginPurchaseShortSale", {"data_id": stock_id, "start_date": start, "end_date": end})
    return jsonify(data)

# Vercel 部署必須的結構，不要加 app.run()

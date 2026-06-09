from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app)

# 你的 Token 已設定
FINMIND_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoic3RldmVuMDMyMyIsImVtYWlsIjoic3RldmVuYWtvcm5AZ21haWwuY29tIiwidG9rZW5fdmVyc2lvbiI6Mn0.skA0AbGBSnuH4aji-E7NQPKDNd-G31K7g_sq772bg5w"
FINMIND_API = "https://api.finmindtrade.com/api/v4/data"

def call_finmind(dataset, params):
    # 確保參數包含 token 和 dataset
    params["dataset"] = dataset
    params["token"] = FINMIND_TOKEN
    headers = {"Authorization": f"Bearer {FINMIND_TOKEN}"}
    try:
        # 使用 requests.get 傳遞 params 字典，正確處理 URL 參數
        res = requests.get(FINMIND_API, params=params, headers=headers, timeout=30)
        return res.json()
    except Exception as e:
        return {"status": 0, "error": str(e), "data": []}

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

@app.route("/api/stock_price")
def stock_price():
    # 確保參數正確傳遞
    params = {
        "data_id": request.args.get("stock_id"),
        "start_date": request.args.get("start_date"),
        "end_date": request.args.get("end_date")
    }
    return jsonify(call_finmind("TaiwanStockPrice", params))

@app.route("/api/institutional")
def institutional():
    # 個股法人資料：FinMind 的 dataset 為 TaiwanStockInstitutionalInvestorsBuySell
    params = {
        "data_id": request.args.get("stock_id"),
        "start_date": request.args.get("start_date"),
        "end_date": request.args.get("end_date")
    }
    return jsonify(call_finmind("TaiwanStockInstitutionalInvestorsBuySell", params))

@app.route("/api/margin")
def margin():
    params = {
        "data_id": request.args.get("stock_id"),
        "start_date": request.args.get("start_date"),
        "end_date": request.args.get("end_date")
    }
    return jsonify(call_finmind("TaiwanStockMarginPurchaseShortSale", params))

# Vercel 部署不需要 app.run()，保持原架構即可

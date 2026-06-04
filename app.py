"""
飆股狙擊系統後端 v2.0
====================
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)

FINMIND_API = "https://api.finmindtrade.com/api/v4/data"

def call_finmind(dataset, params, token):
    params["dataset"] = dataset
    params["token"]   = token
    headers = {"Authorization": f"Bearer {token}"}
    try:
        res = requests.get(FINMIND_API, params=params, headers=headers, timeout=30)
        return res.json()
    except Exception as e:
        return {"status": 0, "error": str(e), "data": []}

@app.route("/")
def index():
    return jsonify({"status": "ok", "message": "飆股狙擊後端 v2.0"})

@app.route("/api/health")
def health():
    return jsonify({"status": "ok", "time": datetime.now().isoformat()})

@app.route("/api/stock_price")
def stock_price():
    token    = request.args.get("token", "")
    stock_id = request.args.get("stock_id", "")
    start    = request.args.get("start_date", "")
    end      = request.args.get("end_date", "")
    if not all([token, stock_id, start]):
        return jsonify({"error": "缺少參數", "data": []}), 400
    data = call_finmind("TaiwanStockPrice", {
        "data_id": stock_id, "start_date": start, "end_date": end
    }, token)
    return jsonify(data)

@app.route("/api/institutional")
def institutional():
    token    = request.args.get("token", "")
    stock_id = request.args.get("stock_id", "")
    start    = request.args.get("start_date", "")
    end      = request.args.get("end_date", "")
    if not token:
        return jsonify({"error": "缺少 token", "data": []}), 400
    params = {"start_date": start, "end_date": end}
    if stock_id:
        params["data_id"] = stock_id
    data = call_finmind("TaiwanStockInstitutionalInvestorsBuySell", params, token)
    return jsonify(data)

@app.route("/api/margin")
def margin():
    token    = request.args.get("token", "")
    stock_id = request.args.get("stock_id", "")
    start    = request.args.get("start_date", "")
    end      = request.args.get("end_date", "")
    if not all([token, stock_id]):
        return jsonify({"error": "缺少參數", "data": []}), 400
    data = call_finmind("TaiwanStockMarginPurchaseShortSale", {
        "data_id": stock_id, "start_date": start, "end_date": end
    }, token)
    return jsonify(data)


@app.route("/api/twse_institutional")
def twse_institutional():
    """TWSE 三大法人買賣超（免費，不需 Token）"""
    date = request.args.get("date", "")
    if not date:
        from datetime import datetime
        today = datetime.now()
        date = f"{today.year-1911}{today.month:02d}{today.day:02d}"
    try:
        # TWSE 個股三大法人買賣超日報
        url = f"https://www.twse.com.tw/rwd/zh/fund/T86?date={date}&selectType=ALL&response=json"
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(url, headers=headers, timeout=15)
        data = res.json()
        if data.get("stat") == "OK" and data.get("data"):
            fields = data.get("fields", [])
            result = []
            for row in data["data"]:
                result.append({
                    "Code": row[0].strip(),
                    "Name": row[1].strip(),
                    "Foreignbuy": row[2].replace(",",""),
                    "Foreignsell": row[3].replace(",",""),
                    "ForeignNet": row[4].replace(",",""),
                    "Investmentbuy": row[5].replace(",",""),
                    "Investmentsell": row[6].replace(",",""),
                    "InvestmentNet": row[7].replace(",",""),
                    "Dealerbuy": row[8].replace(",",""),
                    "Dealersell": row[9].replace(",",""),
                    "DealerNet": row[10].replace(",",""),
                    "TotalNet": row[11].replace(",",""),
                })
            return jsonify({"data": result, "date": date, "status": 200})
        else:
            return jsonify({"data": [], "msg": data.get("stat","無資料"), "status": 404})
    except Exception as e:
        return jsonify({"data": [], "error": str(e), "status": 500})

@app.route("/api/clear_cache")
def clear_cache():
    return jsonify({"status": "ok", "cleared": 0})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

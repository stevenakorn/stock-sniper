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


@app.route("/api/twse_stock_list")
def twse_stock_list():
    """TWSE 上市股票完整清單（含ETF）"""
    try:
        # TWSE 上市股票清單
        url = "https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL"
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(url, headers=headers, timeout=15)
        data = res.json()
        result = []
        for item in data:
            code = item.get("Code","").strip()
            name = item.get("Name","").strip()
            if code and re.match(r"^\d{4,6}$", code):
                result.append({"id": code, "name": name})
        return jsonify({"data": result, "count": len(result)})
    except Exception as e:
        # fallback: 用 TWSE 另一個端點
        try:
            url2 = "https://www.twse.com.tw/rwd/zh/afterTrading/STOCK_DAY_ALL?response=json"
            res2 = requests.get(url2, headers={"User-Agent":"Mozilla/5.0"}, timeout=15)
            data2 = res2.json()
            result2 = []
            for row in data2.get("data",[]):
                if len(row) >= 2:
                    code = str(row[0]).strip()
                    name = str(row[1]).strip()
                    if re.match(r"^\d{4,6}$", code):
                        result2.append({"id": code, "name": name})
            return jsonify({"data": result2, "count": len(result2)})
        except Exception as e2:
            return jsonify({"data": [], "error": str(e2)})

@app.route("/api/tpex_stock_list")
def tpex_stock_list():
    """TPEx 上櫃股票完整清單（含ETF）"""
    try:
        # TPEx 上櫃股票清單
        url = "https://www.tpex.org.tw/openapi/v1/tpex_mainboard_daily_close_quotes"
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(url, headers=headers, timeout=15)
        data = res.json()
        result = []
        for item in data:
            code = str(item.get("SecuritiesCompanyCode","") or item.get("Code","")).strip()
            name = str(item.get("CompanyName","") or item.get("Name","")).strip()
            if code and re.match(r"^\d{4,6}$", code):
                result.append({"id": code, "name": name})
        return jsonify({"data": result, "count": len(result)})
    except Exception as e:
        return jsonify({"data": [], "error": str(e)})

@app.route("/api/clear_cache")
def clear_cache():
    return jsonify({"status": "ok", "cleared": 0})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

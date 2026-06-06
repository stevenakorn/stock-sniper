"""
飆股狙擊系統後端 v8.5 - FinMind 付費高級開發者通道版
======================================================
完美修復證交所封鎖 IP 導致資金雷達卡死在 2026-05-28 的 Bug
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
    params["token"] = token
    headers = {"Authorization": f"Bearer {token}"}
    try:
        res = requests.get(FINMIND_API, params=params, headers=headers, timeout=30)
        return res.json()
    except Exception as e:
        return {"status": 0, "error": str(e), "data": []}

@app.route("/")
def index():
    return jsonify({"status": "ok", "message": "飆股狙擊後端 v8.5 - FinMind 高級版"})

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
    """
    【核心修復】三大法人資金雷達路由
    拋棄會被封鎖的證交所爬蟲，改由前端傳入的付費 Token 直接跟 FinMind 撈取全市場無延遲日報
    """
    token = request.args.get("token", "")
    req_date = request.args.get("date", "") # 民國格式 e.g., 1150604
    
    if not token:
        return jsonify({"data": [], "error": "後端通道未獲取付費 Token 金鑰", "status": 400})

    # 將網頁傳來的民國日期字串（如 1150604）轉換成西元格式（2026-06-04）給 FinMind 識別
    try:
        if req_date and len(req_date) >= 6:
            y = int(req_date[:-4]) + 1911
            m = req_date[-4:-2]
            d = req_date[-2:]
            target_date = f"{y}-{m}-{d}"
        else:
            target_date = datetime.now().strftime("%Y-%m-%d")
    except:
        target_date = datetime.now().strftime("%Y-%m-%d")

    # 呼叫 FinMind 抓取當天全市場個股三大法人明細
    params = {"start_date": target_date, "end_date": target_date}
    fm_res = call_finmind("TaiwanStockInstitutionalInvestorsBuySell", params, token)

    if fm_res.get("status") == 200 and fm_res.get("data"):
        # 將 FinMind 資料格式重新組織，並對齊原證交所的欄位命名結構，確保前端網頁不需要改任何一行 Code
        stock_map = {}
        for row in fm_res["data"]:
            sid = row.get("stock_id")
            name = row.get("name", sid)
            buy = int(row.get("buy", 0))
            sell = int(row.get("sell", 0))
            net = buy - sell
            
            if sid not in stock_map:
                stock_map[sid] = {
                    "Code": sid, "Name": name,
                    "Foreignbuy": 0, "Foreignsell": 0, "ForeignNet": 0,
                    "Investmentbuy": 0, "Investmentsell": 0, "InvestmentNet": 0,
                    "Dealerbuy": 0, "Dealersell": 0, "DealerNet": 0, "TotalNet": 0
                }
            
            # 依據法人種類分別加總（處理同一檔股票有多個子法人的狀況）
            legal_by = row.get("z_legal_by", row.get("name", ""))
            if "外資" in legal_by or "Foreign" in legal_by:
                stock_map[sid]["Foreignbuy"] += buy
                stock_map[sid]["Foreignsell"] += sell
                stock_map[sid]["ForeignNet"] += net
            elif "投信" in legal_by or "Trust" in legal_by:
                stock_map[sid]["Investmentbuy"] += buy
                stock_map[sid]["Investmentsell"] += sell
                stock_map[sid]["InvestmentNet"] += net
            else:
                stock_map[sid]["Dealerbuy"] += buy
                stock_map[sid]["Dealersell"] += sell
                stock_map[sid]["DealerNet"] += net
                
            stock_map[sid]["TotalNet"] += net

        # 將物件結構轉換為前端渲染專用陣列，並把股數轉成張數（除以1000）
        result = []
        for s in stock_map.values():
            result.append({
                "Code": s["Code"], "Name": s["Name"],
                "Foreignbuy": str(round(s["Foreignbuy"]/1000)),
                "Foreignsell": str(round(s["Foreignsell"]/1000)),
                "ForeignNet": str(round(s["ForeignNet"]/1000)),
                "Investmentbuy": str(round(s["Investmentbuy"]/1000)),
                "Investmentsell": str(round(s["Investmentsell"]/1000)),
                "InvestmentNet": str(round(s["InvestmentNet"]/1000)),
                "Dealerbuy": str(round(s["Dealerbuy"]/1000)),
                "Dealersell": str(round(s["Dealersell"]/1000)),
                "DealerNet": str(round(s["DealerNet"]/1000)),
                "TotalNet": str(round(s["TotalNet"]/1000)),
            })
        return jsonify({"data": result, "date": req_date, "status": 200})
    else:
        # 如果當天還沒有資料（例如下午4點前），回傳空陣列
        return jsonify({"data": [], "msg": "FinMind高級資料庫此日期尚未發布或無權限", "status": 404})

@app.route("/api/clear_cache")
def clear_cache():
    return jsonify({"status": "ok", "cleared": 0})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

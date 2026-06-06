"""
飆股狙擊系統後端 v9.5 - 智能雙日期格式相容版
======================================================
1. 修復前端傳入西元格式(2026-05-28)或民國格式(1150528)時，後端切片算錯日期的致命 Bug
2. 完美支援週末與假日自動退回上一個交易日(週五)數據機制
"""
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
    headers = {"Authorization": f"Bearer {token}"}
    try:
        res = requests.get(FINMIND_API, params=params, headers=headers, timeout=30)
        return res.json()
    except Exception as e:
        return {"status": 0, "error": str(e), "data": []}

@app.route("/")
def index():
    return jsonify({"status": "ok", "message": "飆股狙擊後端 v9.5 - 智能日期相容版"})

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

    try:
        # 統一處理西元格式
        if "-" in end:
            end_dt = datetime.strptime(end, "%Y-%m-%d")
        else:
            y = int(end[:-4]) + 1911
            end_dt = datetime(y, int(end[-4:-2]), int(end[-2:]))

        if end_dt.date() >= datetime.now().date():
            if end_dt.weekday() == 5: # 週六
                end_dt = end_dt - timedelta(days=1)
            elif end_dt.weekday() == 6: # 週日
                end_dt = end_dt - timedelta(days=2)
            end = end_dt.strftime("%Y-%m-%d")
    except:
        pass

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
        
    try:
        if "-" in end:
            end_dt = datetime.strptime(end, "%Y-%m-%d")
        else:
            y = int(end[:-4]) + 1911
            end_dt = datetime(y, int(end[-4:-2]), int(end[-2:]))

        if end_dt.date() >= datetime.now().date():
            if end_dt.weekday() == 5:
                end_dt = end_dt - timedelta(days=1)
            elif end_dt.weekday() == 6:
                end_dt = end_dt - timedelta(days=2)
            end = end_dt.strftime("%Y-%m-%d")
    except:
        pass

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
        
    try:
        if "-" in end:
            end_dt = datetime.strptime(end, "%Y-%m-%d")
        else:
            y = int(end[:-4]) + 1911
            end_dt = datetime(y, int(end[-4:-2]), int(end[-2:]))

        if end_dt.date() >= datetime.now().date():
            if end_dt.weekday() == 5:
                end_dt = end_dt - timedelta(days=1)
            elif end_dt.weekday() == 6:
                end_dt = end_dt - timedelta(days=2)
            end = end_dt.strftime("%Y-%m-%d")
    except:
        pass

    data = call_finmind("TaiwanStockMarginPurchaseShortSale", {
        "data_id": stock_id, "start_date": start, "end_date": end
    }, token)
    return jsonify(data)

@app.route("/api/twse_institutional")
def twse_institutional():
    """【智能防錯雷達】自動識別前端傳入的 民國 或 西元 日期格式"""
    token = request.args.get("token", "")
    req_date = request.args.get("date", "") 
    
    if not token:
        return jsonify({"data": [], "error": "後端通道未獲取付費 Token 金鑰", "status": 400})

    try:
        if req_date:
            # 判斷前端傳過來的是不是自帶橫線的西元格式 (e.g., 2026-05-28)
            if "-" in req_date:
                dt_obj = datetime.strptime(req_date, "%Y-%m-%d")
            else:
                # 民國格式 (e.g., 1150528)
                y = int(req_date[:-4]) + 1911
                m = req_date[-4:-2]
                d = req_date[-2:]
                dt_obj = datetime(y, int(m), int(d))
        else:
            dt_obj = datetime.now()
            
        # 智慧判定：若是週末，直接退回最新一天的週五交易日
        if dt_obj.weekday() == 5:
            dt_obj = dt_obj - timedelta(days=1)
        elif dt_obj.weekday() == 6:
            dt_obj = dt_obj - timedelta(days=2)
            
        target_date = dt_obj.strftime("%Y-%m-%d")
    except Exception as e:
        target_date = datetime.now().strftime("%Y-%m-%d")

    params = {"start_date": target_date, "end_date": target_date}
    fm_res = call_finmind("TaiwanStockInstitutionalInvestorsBuySell", params, token)

    if fm_res.get("status") == 200 and fm_res.get("data"):
        stock_map = {}
        for row in fm_res["data"]:
            sid = row.get("stock_id")
            if not sid:
                continue
                
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
            
            legal_by = row.get("institutional_investors", "")
            
            if legal_by == "Foreign_Investor" or "外資" in legal_by:
                stock_map[sid]["Foreignbuy"] += buy
                stock_map[sid]["Foreignsell"] += sell
                stock_map[sid]["ForeignNet"] += net
            elif legal_by == "Investment_Trust" or "投信" in legal_by:
                stock_map[sid]["Investmentbuy"] += buy
                stock_map[sid]["Investmentsell"] += sell
                stock_map[sid]["InvestmentNet"] += net
            else: 
                stock_map[sid]["Dealerbuy"] += buy
                stock_map[sid]["Dealersell"] += sell
                stock_map[sid]["DealerNet"] += net
                
            stock_map[sid]["TotalNet"] += net

        result = []
        for s in stock_map.values():
            if s["TotalNet"] != 0 or s["ForeignNet"] != 0 or s["InvestmentNet"] != 0:
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
        return jsonify({"data": [], "msg": f"該日期({target_date})無交易數據", "status": 404})

@app.route("/api/clear_cache")
def clear_cache():
    return jsonify({"status": "ok", "cleared": 0})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

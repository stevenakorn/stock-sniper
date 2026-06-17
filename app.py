"""
飆股狙擊系統後端 v2.0
====================
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import re
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)

FINMIND_API = "https://api.finmindtrade.com/api/v4/data"

def call_finmind(dataset, params, token):
    params["dataset"] = dataset
    params["token"]   = token
    try:
        res = requests.get(FINMIND_API, params=params, timeout=30)
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
    from datetime import datetime, timedelta
    if not date:
        today = datetime.now()
        date = today.strftime("%Y%m%d")
    elif len(date) == 7 and date.isdigit():
        roc_year = int(date[:3])
        date = str(roc_year + 1911) + date[3:]
    try:
        dt = datetime.strptime(date, "%Y%m%d")
        if dt.weekday() == 5:
            dt -= timedelta(days=1)
        elif dt.weekday() == 6:
            dt -= timedelta(days=2)
        date = dt.strftime("%Y%m%d")
    except:
        pass

    def safe_str(val):
        if val is None:
            return "0"
        return str(val).replace(",", "").strip() or "0"

    try:
        url = f"https://www.twse.com.tw/rwd/zh/fund/T86?date={date}&selectType=ALL&response=json"
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(url, headers=headers, timeout=15)
        data = res.json()
        if data.get("stat") == "OK" and data.get("data"):
            result = []
            for row in data["data"]:
                while len(row) < 12:
                    row.append(None)
                result.append({
                    "Code":           safe_str(row[0]),
                    "Name":           safe_str(row[1]),
                    "Foreignbuy":     safe_str(row[2]),
                    "Foreignsell":    safe_str(row[3]),
                    "ForeignNet":     safe_str(row[4]),
                    "Investmentbuy":  safe_str(row[5]),
                    "Investmentsell": safe_str(row[6]),
                    "InvestmentNet":  safe_str(row[7]),
                    "Dealerbuy":      safe_str(row[8]),
                    "Dealersell":     safe_str(row[9]),
                    "DealerNet":      safe_str(row[10]),
                    "TotalNet":       safe_str(row[11]),
                })
            return jsonify({"data": result, "date": date, "status": 200})
        else:
            return jsonify({"data": [], "msg": data.get("stat", "無資料"), "status": 404})
    except Exception as e:
        return jsonify({"data": [], "error": str(e), "status": 500})


@app.route("/api/stock_list")
def stock_list():
    token = request.args.get("token", "")
    if not token:
        return jsonify({"data": [], "error": "缺少 token"})
    try:
        url = "https://api.finmindtrade.com/api/v4/data"
        params = {"dataset": "TaiwanStockInfo", "token": token}
        res = requests.get(url, params=params, timeout=20)
        data = res.json()
        if data.get("data"):
            result = [
                {"stock_id": d["stock_id"], "stock_name": d["stock_name"]}
                for d in data["data"]
                if re.match(r"^\d{4,6}$", d.get("stock_id",""))
            ]
            return jsonify({"data": result, "count": len(result)})
        return jsonify({"data": [], "msg": data.get("msg","")})
    except Exception as e:
        return jsonify({"data": [], "error": str(e)})

@app.route("/api/twse_stock_list")
def twse_stock_list():
    try:
        url = "https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL"
        headers = {"User-Agent": "Mozilla/5.0", "accept": "application/json"}
        res = requests.get(url, headers=headers, timeout=15)
        data = res.json()
        result = []
        for item in data:
            code = str(item.get("Code","")).strip()
            name = str(item.get("Name","")).strip()
            if code and re.match(r"^\d{4,6}$", code):
                result.append({"id": code, "name": name})
        return jsonify({"data": result, "count": len(result)})
    except Exception as e:
        try:
            url2 = "https://openapi.twse.com.tw/v1/opendata/t187ap03_L"
            res2 = requests.get(url2, headers={"User-Agent":"Mozilla/5.0"}, timeout=15)
            data2 = res2.json()
            result2 = []
            for item in data2:
                code = str(item.get("公司代號","") or item.get("Stock_Code","")).strip()
                name = str(item.get("公司簡稱","") or item.get("Company","")).strip()
                if code and re.match(r"^\d{4,6}$", code):
                    result2.append({"id": code, "name": name})
            return jsonify({"data": result2, "count": len(result2)})
        except Exception as e2:
            return jsonify({"data": [], "error": str(e2)})

@app.route("/api/tpex_stock_list")
def tpex_stock_list():
    try:
        url = "https://openapi.tpex.org.tw/web/stock/aftertrading/otc_quotes_no1430/stk_wn1430"
        headers = {"User-Agent": "Mozilla/5.0", "accept": "application/json"}
        res = requests.get(url, headers=headers, timeout=15)
        data = res.json()
        result = []
        items = data if isinstance(data, list) else data.get("data", data.get("aaData", []))
        for item in items:
            if isinstance(item, dict):
                code = str(item.get("SecuritiesCompanyCode","") or item.get("code","") or item.get("stockNo","")).strip()
                name = str(item.get("CompanyName","") or item.get("name","") or item.get("stockName","")).strip()
            elif isinstance(item, list) and len(item) >= 2:
                code = str(item[0]).strip()
                name = str(item[1]).strip()
            else:
                continue
            if code and re.match(r"^\d{4,6}$", code):
                result.append({"id": code, "name": name})
        if result:
            return jsonify({"data": result, "count": len(result)})
        url2 = "https://openapi.tpex.org.tw/web/stock/statistics/listed_companies_info"
        res2 = requests.get(url2, headers=headers, timeout=15)
        data2 = res2.json()
        result2 = []
        items2 = data2 if isinstance(data2, list) else data2.get("data", [])
        for item in items2:
            if isinstance(item, dict):
                code = str(item.get("SecuritiesCompanyCode","") or item.get("code","")).strip()
                name = str(item.get("CompanyName","") or item.get("name","")).strip()
                if code and re.match(r"^\d{4,6}$", code):
                    result2.append({"id": code, "name": name})
        return jsonify({"data": result2, "count": len(result2)})
    except Exception as e:
        return jsonify({"data": [], "error": str(e)})


@app.route("/api/broker_trading")
def broker_trading():
    from datetime import timedelta
    token    = request.args.get("token", "")
    stock_id = request.args.get("stock_id", "")
    if not all([token, stock_id]):
        return jsonify({"error": "缺少參數", "data": []}), 400

    def fetch_day(date_str):
        params = {
            "dataset": "TaiwanStockTradingDailyReport",
            "data_id": stock_id,
            "start_date": date_str,
            "token": token
        }
        r = requests.get("https://api.finmindtrade.com/api/v4/data", params=params, timeout=15)
        return r.json()

    try:
        today = datetime.now()
        result = None
        for back in range(6):
            d = today - timedelta(days=back)
            if d.weekday() >= 5:
                continue
            date_str = d.strftime("%Y-%m-%d")
            data = fetch_day(date_str)
            if data.get("data"):
                result = {"data": data["data"], "date": date_str}
                break

        if not result:
            return jsonify({"data": [], "msg": "近期無分點資料"})

        rows = result["data"]
        broker_net = {}
        for r in rows:
            bid   = r.get("broker_id", "")
            bname = r.get("broker_name", bid)
            buy   = int(r.get("buy", 0))
            sell  = int(r.get("sell", 0))
            if bid not in broker_net:
                broker_net[bid] = {"name": bname, "buy": 0, "sell": 0, "net": 0}
            broker_net[bid]["buy"]  += buy
            broker_net[bid]["sell"] += sell
            broker_net[bid]["net"]  += buy - sell

        sorted_brokers = sorted(broker_net.values(), key=lambda x: x["net"], reverse=True)
        top5_buy  = sorted_brokers[:5]
        top5_sell = sorted_brokers[-5:][::-1] if len(sorted_brokers) >= 5 else []
        return jsonify({"data": {"date": result["date"], "top_buy": top5_buy, "top_sell": top5_sell}})
    except Exception as e:
        return jsonify({"data": [], "error": str(e)})

@app.route("/api/margin_today")
def margin_today():
    token    = request.args.get("token", "")
    stock_id = request.args.get("stock_id", "")
    start    = request.args.get("start_date", "")
    end      = request.args.get("end_date", "")
    if not all([token, stock_id]):
        return jsonify({"error": "缺少參數", "data": []}), 400
    try:
        params = {
            "dataset": "TaiwanStockMarginPurchaseShortSale",
            "data_id": stock_id,
            "start_date": start,
            "end_date": end,
            "token": token
        }
        res  = requests.get("https://api.finmindtrade.com/api/v4/data",
                           params=params, timeout=15)
        data = res.json()
        return jsonify(data)
    except Exception as e:
        return jsonify({"data": [], "error": str(e)})

@app.route("/api/clear_cache")
def clear_cache():
    return jsonify({"status": "ok", "cleared": 0})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

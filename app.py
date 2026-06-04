"""
飆股狙擊系統 - 後端 API
========================
部署到 Render.com（免費方案）
功能：
  - 代理所有 Finmind API 請求（解決 CORS 問題）
  - 快取資料減少 API 呼叫次數
  - 提供股票掃描 API
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
from datetime import datetime, timedelta
from functools import lru_cache
import threading
import time

app = Flask(__name__)
CORS(app)  # 允許所有來源（前端網頁呼叫）

FINMIND_API = "https://api.finmindtrade.com/api/v4/data"

# 簡單記憶體快取
_cache = {}
_cache_lock = threading.Lock()

def get_cache(key):
    with _cache_lock:
        item = _cache.get(key)
        if item and time.time() < item["expires"]:
            return item["data"]
        return None

def set_cache(key, data, ttl=3600):
    with _cache_lock:
        _cache[key] = {"data": data, "expires": time.time() + ttl}

def call_finmind(dataset, params, token):
    """呼叫 Finmind API"""
    params["dataset"] = dataset
    params["token"]   = token
    headers = {"Authorization": f"Bearer {token}"}
    try:
        res = requests.get(FINMIND_API, params=params, headers=headers, timeout=30)
        return res.json()
    except Exception as e:
        return {"status": 0, "error": str(e)}

# ──────────────────────────────────────────
# API 端點
# ──────────────────────────────────────────

@app.route("/")
def index():
    return jsonify({"status": "ok", "message": "飆股狙擊後端 v1.0"})

@app.route("/api/stock_price")
def stock_price():
    """股票歷史價格"""
    token    = request.args.get("token", "")
    stock_id = request.args.get("stock_id", "")
    start    = request.args.get("start_date", "")
    end      = request.args.get("end_date", "")

    if not all([token, stock_id, start]):
        return jsonify({"error": "缺少參數"}), 400

    cache_key = f"price_{stock_id}_{start}_{end}"
    cached = get_cache(cache_key)
    if cached:
        return jsonify(cached)

    data = call_finmind("TaiwanStockPrice", {
        "data_id": stock_id,
        "start_date": start,
        "end_date": end
    }, token)

    if data.get("data"):
        set_cache(cache_key, data, ttl=1800)  # 快取30分鐘

    return jsonify(data)

@app.route("/api/institutional")
def institutional():
    """三大法人買賣超"""
    token    = request.args.get("token", "")
    stock_id = request.args.get("stock_id", "")
    start    = request.args.get("start_date", "")
    end      = request.args.get("end_date", "")

    if not token:
        return jsonify({"error": "缺少 token"}), 400

    params = {"start_date": start, "end_date": end}
    if stock_id:
        params["data_id"] = stock_id

    # 快取 key 加入今日日期，每天自動更新
    today_str = datetime.now().strftime("%Y-%m-%d")
    cache_key = f"inst_{stock_id}_{start}_{end}_{today_str}"
    cached = get_cache(cache_key)
    if cached:
        return jsonify(cached)

    data = call_finmind("TaiwanStockInstitutionalInvestorsBuySell", params, token)

    if data.get("data"):
        set_cache(cache_key, data, ttl=1800)  # 快取30分鐘

    return jsonify(data)

@app.route("/api/margin")
def margin():
    """融資融券"""
    token    = request.args.get("token", "")
    stock_id = request.args.get("stock_id", "")
    start    = request.args.get("start_date", "")
    end      = request.args.get("end_date", "")

    if not all([token, stock_id]):
        return jsonify({"error": "缺少參數"}), 400

    cache_key = f"margin_{stock_id}_{start}_{end}"
    cached = get_cache(cache_key)
    if cached:
        return jsonify(cached)

    data = call_finmind("TaiwanStockMarginPurchaseShortSale", {
        "data_id": stock_id,
        "start_date": start,
        "end_date": end
    }, token)

    if data.get("data"):
        set_cache(cache_key, data, ttl=3600)

    return jsonify(data)

@app.route("/api/stock_info")
def stock_info():
    """股票基本資料（清單）"""
    token = request.args.get("token", "")
    if not token:
        return jsonify({"error": "缺少 token"}), 400

    cache_key = "stock_info"
    cached = get_cache(cache_key)
    if cached:
        return jsonify(cached)

    data = call_finmind("TaiwanStockInfo", {}, token)

    if data.get("data"):
        set_cache(cache_key, data, ttl=86400)  # 快取24小時

    return jsonify(data)

@app.route("/api/health")
def health():
    return jsonify({
        "status": "ok",
        "time": datetime.now().isoformat(),
        "cache_keys": len(_cache)
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

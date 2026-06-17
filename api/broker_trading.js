export default async function handler(req, res) {
  const { token, stock_id } = req.query;
  if (!token || !stock_id) {
    return res.status(400).json({ error: "缺少參數", data: [] });
  }

  async function fetchDay(date) {
    const url = `https://api.finmindtrade.com/api/v4/data?dataset=TaiwanStockTradingDailyReport&data_id=${stock_id}&start_date=${date}&token=${token}`;
    const r = await fetch(url);
    return r.json();
  }

  // 先查券商代碼名稱對照表
  async function fetchBrokerInfo() {
    const url = `https://api.finmindtrade.com/api/v4/data?dataset=TaiwanSecuritiesTraderInfo&token=${token}`;
    try {
      const r = await fetch(url);
      const d = await r.json();
      const map = {};
      if (d.data) d.data.forEach(b => { map[b.securities_trader_id] = b.securities_trader; });
      return map;
    } catch(e) { return {}; }
  }

  try {
    // 找最近交易日
    const today = new Date();
    let result = null;
    for (let back = 0; back <= 5; back++) {
      const d = new Date(today);
      d.setDate(d.getDate() - back);
      if (d.getDay() === 0 || d.getDay() === 6) continue;
      const dateStr = d.toISOString().split('T')[0];
      const data = await fetchDay(dateStr);
      if (data.data && data.data.length > 0) {
        result = { data: data.data, date: dateStr };
        break;
      }
    }

    if (!result) {
      return res.status(200).json({ data: [], msg: "近期無分點資料" });
    }

    // 平行抓券商名稱對照
    const brokerInfoMap = await fetchBrokerInfo();

    const rows = result.data;
    const brokerNet = {};
    for (const r of rows) {
      const bid   = r.broker_id || "";
      // name 欄位可能為空，從對照表補
      const bname = (r.name && r.name.trim()) || brokerInfoMap[bid] || bid;
      // buy/sell 是股數，除以1000轉張數
      const buy  = Math.round(parseInt(r.buy  || 0) / 1000);
      const sell = Math.round(parseInt(r.sell || 0) / 1000);
      if (!brokerNet[bid]) brokerNet[bid] = { name: bname, buy: 0, sell: 0, net: 0 };
      brokerNet[bid].buy  += buy;
      brokerNet[bid].sell += sell;
      brokerNet[bid].net  += buy - sell;
    }

    // 過濾掉名稱為空或代號的
    const sorted = Object.values(brokerNet)
      .filter(b => b.name && b.name !== "")
      .sort((a, b) => b.net - a.net);

    return res.status(200).json({
      data: {
        date: result.date,
        top_buy:  sorted.slice(0, 5),
        top_sell: sorted.slice(-5).reverse(),
      }
    });
  } catch (err) {
    return res.status(500).json({ error: err.message, data: [] });
  }
}

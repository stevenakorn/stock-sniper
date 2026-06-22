export default async function handler(req, res) {
  const { token, stock_id } = req.query;
  if (!token || !stock_id) {
    return res.status(400).json({ error: "缺少參數", data: [] });
  }

  async function fetchDay(date) {
    // 欄位：securities_trader, securities_trader_id, buy, sell, price, date, stock_id
    const url = `https://api.finmindtrade.com/api/v4/data?dataset=TaiwanStockTradingDailyReport&data_id=${stock_id}&start_date=${date}&token=${token}`;
    const r = await fetch(url);
    return r.json();
  }

  try {
    // 往前找最近7天（跳週末），因為分點資料有1-2天延遲
    const today = new Date();
    let result = null;
    for (let back = 1; back <= 7; back++) {  // 從昨天開始找（當天資料未更新）
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

    const rows = result.data;
    const brokerNet = {};
    for (const r of rows) {
      // 正確欄位名稱
      const bid   = r.securities_trader_id || r.broker_id || "";
      const bname = r.securities_trader     || r.broker_name || r.name || bid;
      // buy/sell 單位是股數，除以1000轉張數
      const buy  = Math.round(parseInt(r.buy  || 0) / 1000);
      const sell = Math.round(parseInt(r.sell || 0) / 1000);
      if (!brokerNet[bid]) brokerNet[bid] = { name: bname, buy: 0, sell: 0, net: 0 };
      brokerNet[bid].buy  += buy;
      brokerNet[bid].sell += sell;
      brokerNet[bid].net  += buy - sell;
    }

    const sorted = Object.values(brokerNet)
      .filter(b => b.name && b.name.trim() !== "" && b.net !== 0)
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

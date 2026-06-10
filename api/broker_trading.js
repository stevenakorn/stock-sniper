export default async function handler(req, res) {
  const { token, stock_id, start_date, end_date } = req.query;

  if (!token || !stock_id) {
    return res.status(400).json({ error: "缺少參數", data: [] });
  }

  const url = `https://api.finmindtrade.com/api/v4/data?dataset=TaiwanStockBrokerBuySell&data_id=${stock_id}&start_date=${start_date || ""}&end_date=${end_date || ""}&token=${token}`;

  try {
    const response = await fetch(url, {
      headers: { "Authorization": `Bearer ${token}` }
    });
    const data = await response.json();

    if (!data.data || !data.data.length) {
      return res.status(200).json({ data: [], msg: data.msg || "無資料" });
    }

    const rows = data.data;
    const dates = [...new Set(rows.map(r => r.date))].sort().reverse();
    const latest = dates[0];
    const todayRows = rows.filter(r => r.date === latest);

    const brokerNet = {};
    for (const r of todayRows) {
      const bid = r.broker_id || "";
      const bname = r.broker_name || bid;
      const buy = parseInt(r.buy || 0);
      const sell = parseInt(r.sell || 0);
      if (!brokerNet[bid]) brokerNet[bid] = { name: bname, buy: 0, sell: 0, net: 0 };
      brokerNet[bid].buy += buy;
      brokerNet[bid].sell += sell;
      brokerNet[bid].net += buy - sell;
    }

    const sorted = Object.values(brokerNet).sort((a, b) => b.net - a.net);
    return res.status(200).json({
      data: {
        date: latest,
        top_buy: sorted.slice(0, 5),
        top_sell: sorted.slice(-5).reverse(),
      }
    });
  } catch (err) {
    return res.status(500).json({ error: err.message, data: [] });
  }
}

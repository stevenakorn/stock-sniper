export default async function handler(req, res) {
  const { stock_id } = req.query;
  if (!stock_id) {
    return res.status(400).json({ error: "缺少 stock_id", data: [] });
  }

  function fmtDate(d) {
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, "0");
    const day = String(d.getDate()).padStart(2, "0");
    return `${y}${m}${day}`;
  }

  async function fetchTWSE(dateStr) {
    const url = `https://www.twse.com.tw/rwd/zh/fund/TWT44U?date=${dateStr}&stockNo=${stock_id}&response=json`;
    const r = await fetch(url, { headers: { "User-Agent": "Mozilla/5.0" } });
    const d = await r.json();
    if (d.stat === "OK" && d.data && d.data.length > 0) {
      return { data: d.data, date: dateStr };
    }
    return null;
  }

  try {
    const today = new Date();
    let result = null;
    for (let back = 0; back <= 7; back++) {
      const d = new Date(today);
      d.setDate(d.getDate() - back);
      if (d.getDay() === 0 || d.getDay() === 6) continue;
      const dateStr = fmtDate(d);
      const data = await fetchTWSE(dateStr);
      if (data) { result = data; break; }
    }

    if (!result) {
      return res.status(200).json({ data: [], msg: "TWSE 近期無分點資料" });
    }

    // 實際欄位：["","券商代號","券商名稱","買進股數","賣出股數","買賣超股數"]
    // row[0]=空, row[1]=代號, row[2]=名稱, row[3]=買進, row[4]=賣出, row[5]=買賣超
    const brokers = [];
    for (const row of result.data) {
      try {
        if (row.length < 6) continue;
        const name  = String(row[2]).trim();
        const buyS  = String(row[3]).replace(/,/g, "").trim();
        const sellS = String(row[4]).replace(/,/g, "").trim();
        const netS  = String(row[5]).replace(/,/g, "").trim();
        if (!/^-?\d+$/.test(buyS) || !/^-?\d+$/.test(netS)) continue;
        const buy  = Math.round(parseInt(buyS)  / 1000);
        const sell = Math.round(parseInt(sellS) / 1000);
        const net  = Math.round(parseInt(netS)  / 1000);
        if (name && net !== 0) brokers.push({ name, buy, sell, net });
      } catch(e) { continue; }
    }

    const sorted = brokers.sort((a, b) => b.net - a.net);
    const ds = result.date;
    const fmtedDate = `${ds.slice(0,4)}-${ds.slice(4,6)}-${ds.slice(6,8)}`;

    return res.status(200).json({
      data: {
        date: fmtedDate,
        top_buy:  sorted.slice(0, 5),
        top_sell: sorted.slice(-5).reverse(),
      }
    });
  } catch (err) {
    return res.status(500).json({ error: err.message, data: [] });
  }
}

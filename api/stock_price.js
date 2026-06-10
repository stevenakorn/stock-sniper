export default async function handler(req, res) {
  const { token, stock_id, start_date, end_date } = req.query;

  if (!token || !stock_id || !start_date) {
    return res.status(400).json({ error: "缺少參數", data: [] });
  }

  const url = `https://api.finmindtrade.com/api/v4/data?dataset=TaiwanStockPrice&data_id=${stock_id}&start_date=${start_date}&end_date=${end_date || ""}&token=${token}`;

  try {
    const response = await fetch(url, {
      headers: { "Authorization": `Bearer ${token}` }
    });
    const data = await response.json();
    return res.status(200).json(data);
  } catch (err) {
    return res.status(500).json({ error: err.message, data: [] });
  }
}

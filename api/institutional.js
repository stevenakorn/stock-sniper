export default async function handler(req, res) {
  const { token, stock_id, start_date, end_date } = req.query;

  if (!token) {
    return res.status(400).json({ error: "缺少 token", data: [] });
  }

  let url = `https://api.finmindtrade.com/api/v4/data?dataset=TaiwanStockInstitutionalInvestorsBuySell&start_date=${start_date || ""}&end_date=${end_date || ""}&token=${token}`;
  if (stock_id) url += `&data_id=${stock_id}`;

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

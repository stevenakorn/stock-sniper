export default async function handler(req, res) {
  let { date } = req.query; 
  const token = process.env.FINMIND_TOKEN;

  if (!token) return res.status(400).json({ error: "Token 未設定" });
  if (!date) date = new Date().toISOString().split('T')[0];

  async function fetchWithFallback(currentDate, retries = 3) {
    if (retries === 0) return null;

    // 將 token 移至 header 較為規範
    const url = `https://api.finmindtrade.com/api/v4/data?dataset=TaiwanStockInstitutionalInvestorsBuySell&start_date=${currentDate}&end_date=${currentDate}`;
    
    try {
      const response = await fetch(url, {
        headers: { "Authorization": `Bearer ${token}` }
      });
      const data = await response.json();

      if (data && Array.isArray(data.data) && data.data.length > 0) {
        return { data: data.data, date: currentDate };
      }
      
      // 日期回推邏輯
      const d = new Date(currentDate + "T00:00:00Z");
      d.setUTCDate(d.getUTCDate() - 1);
      const prevDate = d.toISOString().split('T')[0];
      
      return await fetchWithFallback(prevDate, retries - 1);
    } catch (err) {
      return null;
    }
  }

  const result = await fetchWithFallback(date);
  
  if (!result) {
    res.status(404).json({ error: "找不到最近的交易日資料", status: 404 });
  } else {
    res.status(200).json(result);
  }
}

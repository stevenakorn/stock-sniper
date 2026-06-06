export default async function handler(req, res) {
  let { date } = req.query; // 傳入的 date 格式為 YYYY-MM-DD
  const token = process.env.FINMIND_TOKEN;

  if (!token) {
    return res.status(400).json({ error: "無效 Token (環境變數未載入)" });
  }

  // 自動日期回推函式：若 API 沒資料，最多嘗試往前推 5 天 (應付連假)
  async function fetchWithFallback(currentDate, retries = 5) {
    if (retries === 0) return null;

    const url = `https://api.finmindtrade.com/api/v4/data?token=${token}&dataset=TaiwanStockInstitutionalInvestorsBuySell&start_date=${currentDate}&end_date=${currentDate}`;
    
    const response = await fetch(url);
    const data = await response.json();

    // 如果沒資料，往前推一天再試
    if (!data.data || data.data.length === 0) {
      const d = new Date(currentDate);
      d.setDate(d.getDate() - 1);
      const prevDate = d.toISOString().split('T')[0];
      return await fetchWithFallback(prevDate, retries - 1);
    }
    
    return data;
  }

  try {
    const result = await fetchWithFallback(date);
    if (!result) {
      res.status(404).json({ error: "找不到最近的交易日資料" });
    } else {
      res.status(200).json(result);
    }
  } catch (error) {
    res.status(500).json({ error: "Failed to fetch data" });
  }
}

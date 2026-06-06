export default async function handler(req, res) {
  // 接收前端傳來的 YYYY-MM-DD 日期
  let { date } = req.query; 
  const token = process.env.FINMIND_TOKEN;

  if (!token) {
    return res.status(400).json({ error: "Token 未設定" });
  }

  // 自動回推日期功能：若無資料，自動往前找最近的交易日
  async function fetchWithFallback(currentDate, retries = 5) {
    if (retries === 0) return null;

    // 對接 FinMind InstitutionalInvestorsBuySell 資料集
    const url = `https://api.finmindtrade.com/api/v4/data?token=${token}&dataset=TaiwanStockInstitutionalInvestorsBuySell&start_date=${currentDate}&end_date=${currentDate}`;
    
    try {
      const response = await fetch(url);
      const data = await response.json();

      // 如果有資料且格式正確，直接回傳
      if (data && data.data && data.data.length > 0) {
        return { data: data.data, date: currentDate };
      }
      
      // 無資料，往前推一天
      const d = new Date(currentDate);
      d.setDate(d.getDate() - 1);
      return await fetchWithFallback(d.toISOString().split('T')[0], retries - 1);
    } catch (err) {
      return null;
    }
  }

  const result = await fetchWithFallback(date);
  if (!result) {
    res.status(404).json({ error: "找不到最近的交易日資料" });
  } else {
    // 關鍵：將 FinMind 的結構整理成前端 renderMoneyFlowData 認得的格式
    // 這裡我們直接把 result.data 丟回去
    res.status(200).json(result);
  }
}

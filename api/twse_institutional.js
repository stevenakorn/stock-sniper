export default async function handler(req, res) {
  let { date } = req.query; 
  const token = process.env.FINMIND_TOKEN;

  if (!token) {
    return res.status(400).json({ error: "Token 未設定" });
  }

  // 自動回推日期功能：若無資料，自動往前找最近的交易日
  async function fetchWithFallback(currentDate, retries = 5) {
    if (retries === 0) return null;

    const url = `https://api.finmindtrade.com/api/v4/data?token=${token}&dataset=TaiwanStockInstitutionalInvestorsBuySell&start_date=${currentDate}&end_date=${currentDate}`;
    
    try {
      const response = await fetch(url);
      const data = await response.json();

      // 【修正點】：檢查是否為空陣列 []
      if (data && Array.isArray(data.data) && data.data.length > 0) {
        return { data: data.data, date: currentDate };
      }
      
      // 若資料為空陣列，則強制往前推一天
      console.log(`日期 ${currentDate} 無交易資料，嘗試往前一天...`);
      const d = new Date(currentDate);
      d.setDate(d.getDate() - 1);
      
      // 確保日期格式正確
      const prevDate = d.toISOString().split('T')[0];
      return await fetchWithFallback(prevDate, retries - 1);
      
    } catch (err) {
      return null;
    }
  }

  const result = await fetchWithFallback(date);
  
  if (!result) {
    res.status(404).json({ error: "找不到最近的交易日資料" });
  } else {
    res.status(200).json(result);
  }
}

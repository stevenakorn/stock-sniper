export default async function handler(req, res) {
  // 1. 取得日期參數與 Token (從環境變數讀取)
  let { date } = req.query;
  const token = process.env.FINMIND_TOKEN;

  // 檢查 Token 是否存在
  if (!token) {
    return res.status(400).json({ error: "後端通道未獲取付費 Token 金鑰", status: 400 });
  }

  // 若沒給日期，預設今天
  if (!date) {
    date = new Date().toISOString().split('T')[0];
  }

  // 核心功能：若無資料，自動往前找最近的交易日
  async function fetchWithFallback(currentDate, retries = 5) {
    if (retries <= 0) return null;

    // 將 Token 放入 Header 請求
    const url = `https://api.finmindtrade.com/api/v4/data?dataset=TaiwanStockInstitutionalInvestorsBuySell&start_date=${currentDate}&end_date=${currentDate}`;
    
    try {
      const response = await fetch(url, {
        headers: { "Authorization": `Bearer ${token}` }
      });
      const data = await response.json();

      // 如果有資料，直接回傳
      if (data && Array.isArray(data.data) && data.data.length > 0) {
        return { data: data.data, date: currentDate, status: 200 };
      }
      
      // 無資料，日期往前推一天
      console.log(`日期 ${currentDate} 無交易資料，嘗試往前尋找...`);
      const d = new Date(currentDate + "T00:00:00Z");
      d.setUTCDate(d.getUTCDate() - 1);
      const prevDate = d.toISOString().split('T')[0];
      
      return await fetchWithFallback(prevDate, retries - 1);
      
    } catch (err) {
      console.error("API 請求錯誤:", err);
      return null;
    }
  }

  // 執行撈取
  const result = await fetchWithFallback(date);
  
  if (!result) {
    res.status(404).json({ 
      data: [], 
      error: "找不到最近的交易日資料", 
      status: 404 
    });
  } else {
    res.status(200).json(result);
  }
}

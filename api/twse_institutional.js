export default async function handler(req, res) {
  // 1. 取得日期與 Token
  let { date } = req.query;
  // 確保這裡讀取的環境變數名稱與 Vercel 後台設定完全一致
  const token = process.env.FINMIND_TOKEN;

  // 2. 錯誤檢查：Token 是否設定
  if (!token) {
    return res.status(400).json({ 
      error: "後端通道未獲取付費 Token 金鑰", 
      status: 400 
    });
  }

  // 若沒給日期，強制設為今天
  if (!date) {
    date = new Date().toISOString().split('T')[0];
  }

  // 3. 核心功能：自動回推交易日機制
  async function fetchWithFallback(currentDate, retries = 5) {
    if (retries <= 0) return null;

    // 使用 Authorization Header 請求，比網址參數更穩定
    const url = `https://api.finmindtrade.com/api/v4/data?dataset=TaiwanStockInstitutionalInvestorsBuySell&start_date=${currentDate}&end_date=${currentDate}`;
    
    try {
      const response = await fetch(url, {
        headers: { "Authorization": `Bearer ${token}` }
      });
      const data = await response.json();

      // 檢查是否成功抓到資料
      if (data && Array.isArray(data.data) && data.data.length > 0) {
        return { data: data.data, date: currentDate, status: 200 };
      }
      
      // 無資料：自動將日期往前推一天
      console.log(`日期 ${currentDate} 無交易資料，嘗試往前推一天...`);
      const d = new Date(currentDate + "T00:00:00Z");
      d.setUTCDate(d.getUTCDate() - 1);
      const prevDate = d.toISOString().split('T')[0];
      
      return await fetchWithFallback(prevDate, retries - 1);
      
    } catch (err) {
      console.error("API 請求發生錯誤:", err);
      return null;
    }
  }

  // 4. 執行與回應
  const result = await fetchWithFallback(date);
  
  if (!result) {
    res.status(404).json({ 
      data: [], 
      msg: "找不到最近的交易日資料", 
      status: 404 
    });
  } else {
    res.status(200).json(result);
  }
}

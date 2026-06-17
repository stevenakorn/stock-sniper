// 注意：請將 YOUR_ACTUAL_TOKEN_HERE 替換為你申請到的真實 FinMind Token
const MY_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoic3RldmVuMDMyMyIsImVtYWlsIjoic3RldmVuYWtvcm5AZ21haWwuY29tIiwidG9rZW5fdmVyc2lvbiI6M30.mKQypMoJAkh9x9C6-cFDIJdFriFuCURqw9H5AqebALE";

export default async function handler(req, res) {
  let { date } = req.query;
  
  // 直接使用寫死的 Token，繞過環境變數問題
  const token = MY_TOKEN;

  // 若沒給日期，預設今天
  if (!date) {
    date = new Date().toISOString().split('T')[0];
  }

  // 核心功能：若無資料，自動往前找最近的交易日
  async function fetchWithFallback(currentDate, retries = 5) {
    if (retries <= 0) return null;

    // 使用寫死的 token 進行請求
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

  // 執行撈取
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

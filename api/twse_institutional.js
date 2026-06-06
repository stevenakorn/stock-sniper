export default async function handler(req, res) {
  const token = process.env.FINMIND_TOKEN; 
  
  // 診斷用：直接告訴我你抓到了什麼
  if (!token) {
    return res.status(400).json({ 
        error: "無效 Token", 
        debug: "token 變數為空，請檢查環境變數是否已 Redeploy" 
    });
  }

  // 診斷用：確認 Token 是不是長度正確 (不要印出完整 Token 以免外洩)
  if (token.length < 10) {
      return res.status(400).json({ error: "Token 長度異常，請檢查是否複製完整" });
  }

  const { date } = req.query;
  const url = `https://api.finmindtrade.com/api/v4/data?token=${token}&dataset=TaiwanStockInstitutionalInvestorsBuySell&start_date=${date}&end_date=${date}`;

  try {
    const response = await fetch(url);
    const data = await response.json();
    res.status(200).json(data);
  } catch (error) {
    res.status(500).json({ error: "Failed to fetch data" });
  }
}

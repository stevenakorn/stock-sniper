// api/twse_institutional.js
export default async function handler(req, res) {
  const { date } = req.query;
  // 記得去 Vercel 設定頁面添加 FINMIND_TOKEN 這個環境變數
  const token = process.env.FINMIND_TOKEN; 

  const url = `https://api.finmindtrade.com/api/v4/data?token=${token}&dataset=TaiwanStockInstitutionalInvestorsBuySell&start_date=${date}&end_date=${date}`;

  try {
    const response = await fetch(url);
    const data = await response.json();
    res.status(200).json(data);
  } catch (error) {
    res.status(500).json({ error: "Failed to fetch data" });
  }
}

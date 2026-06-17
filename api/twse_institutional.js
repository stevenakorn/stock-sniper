const MY_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoic3RldmVuMDMyMyIsImVtYWlsIjoic3RldmVuYWtvcm5AZ21haWwuY29tIiwidG9rZW5fdmVyc2lvbiI6M30.mKQypMoJAkh9x9C6-cFDIJdFriFuCURqw9H5AqebALE";

export default async function handler(req, res) {
  let { date } = req.query;

  const token = MY_TOKEN;

  if (!date) {
    date = new Date().toISOString().split('T')[0];
  }

  async function fetchWithFallback(currentDate, retries = 5) {
    if (retries <= 0) return null;

    const url = `https://api.finmindtrade.com/api/v4/data?dataset=TaiwanStockInstitutionalInvestorsBuySell&start_date=${currentDate}&end_date=${currentDate}&token=${token}`;

    try {
      const response = await fetch(url);
      const data = await response.json();

      if (data && Array.isArray(data.data) && data.data.length > 0) {
        return { data: data.data, date: currentDate, status: 200 };
      }

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

const axios = require('axios');

module.exports = async (req, res) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET');
  const { stock_id, date, token } = req.query;
  
  try {
    const url = `https://api.finmindtrade.com/api/v4/data?dataset=TaiwanStockDailyBuySell&data_id=${stock_id}&start_date=${date}&end_date=${date}&token=${token}`;
    const response = await axios.get(url, { timeout: 10000 });
    return res.status(200).json(response.data);
  } catch (error) {
    return res.status(500).json({ error: "後端抓取分點失敗", message: error.message });
  }
};

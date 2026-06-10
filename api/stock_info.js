const axios = require('axios');

module.exports = async (req, res) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET');
  const { token } = req.query;
  
  try {
    const url = `https://api.finmindtrade.com/api/v4/data?dataset=TaiwanStockInfo&token=${token}`;
    const response = await axios.get(url, { timeout: 15000 });
    return res.status(200).json(response.data);
  } catch (error) {
    return res.status(500).json({ error: "後端抓取清單失敗" });
  }
};

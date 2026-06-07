async function fetchStockData(stockId) {
    const end   = new Date();
    const start = new Date();
    start.setDate(start.getDate() - 90);
    const fmt = d => d.toISOString().split("T")[0];

    // 修改：將 API 路徑明確指向你的後端
    const url = `${BACKEND_URL}/api/stock_price?token=${token}&stock_id=${stockId}&start_date=${fmt(start)}&end_date=${fmt(end)}`;

    try {
        const res = await fetch(url);
        const json = await res.json();
        
        // 【檢查點】如果這裡一直回傳 null，請看 Console 的 log
        if (!json.data || json.data.length < 20) {
            console.log(`個股 ${stockId} 回傳資料不足，長度:`, json.data ? json.data.length : 0);
            return null;
        }
        
        const rows = json.data;
        return {
            close: rows.map(r => parseFloat(r.close)),
            open:  rows.map(r => parseFloat(r.open)),
            high:  rows.map(r => parseFloat(r.max)),
            low:   rows.map(r => parseFloat(r.min)),
            volume: rows.map(r => parseFloat(r.Trading_Volume)),
            date:  rows.map(r => r.date),
        };
    } catch(e) {
        console.error(`個股 ${stockId} 請求失敗:`, e);
        return null;
    }
}

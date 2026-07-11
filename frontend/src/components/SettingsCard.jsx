function SettingsCard({ url, setUrl, basePath, setBasePath, loading, handleParse }) {
  return (
    <div style={{ 
      padding: '20px', 
      backgroundColor: '#f8fafc', 
      borderRadius: '8px', 
      border: '1px solid #e2e8f0',
      marginBottom: '25px' 
    }}>
      <div style={{ marginBottom: '15px' }}>
        <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold', color: '#4a5568' }}>
          動畫首頁網址：
        </label>
        <input
          type="text"
          placeholder="請貼上動畫首頁網址..."
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          style={{ width: '400px', padding: '8px', marginRight: '10px', borderRadius: '4px', border: '1px solid #cbd5e0' }}
          disabled={loading}
        />
        <button 
          onClick={handleParse} 
          disabled={loading} 
          style={{ padding: '8px 16px', borderRadius: '4px', cursor: loading ? 'not-allowed' : 'pointer' }}
        >
          {loading ? '解析中...' : '開始解析'}
        </button>
      </div>

      <div>
        <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold', color: '#4a5568' }}>
          本機儲存路徑：
        </label>
        <input
          type="text"
          placeholder="例如: D:\Anime\"
          value={basePath}
          onChange={(e) => setBasePath(e.target.value)} 
          style={{ width: '505px', padding: '8px', borderRadius: '4px', border: '1px solid #cbd5e0' }}
        />
      </div>
    </div>
  );
}

export default SettingsCard;
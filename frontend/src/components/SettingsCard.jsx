function SettingsCard({ url, setUrl, loading, handleParse }) {
  return (
    <div className="bg-white rounded-2xl shadow-xs border border-slate-100 p-6 mb-6">
      <label className="block text-sm font-semibold text-slate-700 mb-1.5">
        🔗 Anime1 動畫首頁網址
      </label>
      <div className="flex gap-2">
        <input
          type="text"
          placeholder="請貼上動畫首頁網址（例如：https://anime1.me/category/...）"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          className="flex-1 px-3.5 py-2 bg-slate-50/50 border border-slate-200 rounded-xl text-slate-900 placeholder-slate-400 focus:outline-hidden focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 transition-all text-sm disabled:opacity-60 disabled:cursor-not-allowed"
          disabled={loading}
        />
        <button
          onClick={handleParse}
          disabled={loading}
          className="px-5 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-100 disabled:text-slate-400 text-white font-medium rounded-xl transition-colors text-sm shadow-xs disabled:cursor-not-allowed cursor-pointer flex items-center justify-center min-w-[96px]"
        >
          {loading ? (
            <div className="flex items-center gap-1.5">
              <span className="w-4 h-4 border-2 border-slate-400 border-t-white rounded-full animate-spin"></span>
              <span>解析中</span>
            </div>
          ) : (
            '開始解析'
          )}
        </button>
      </div>
    </div>
  );
}

export default SettingsCard;
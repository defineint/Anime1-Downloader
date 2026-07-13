function EpisodeList({ 
  animeTitle, 
  episodes, 
  episodeTasks, 
  handleDownloadAll, 
  hasAnyAvailableEpisode, 
  submitDownloadTask 
}) {
  return (
    <div className="bg-white rounded-2xl shadow-xs border border-slate-100 p-6">
      {/* 頂部標題與「下載全部」區塊 */}
      {animeTitle && (
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-100 pb-4 mb-5">
          <div className="flex items-center gap-2">
            <span className="w-2 h-5 bg-blue-600 rounded-full"></span>
            <h3 className="text-base font-bold text-slate-800">當前動畫：{animeTitle}</h3>
          </div>
          <button
            onClick={handleDownloadAll}
            disabled={!hasAnyAvailableEpisode || episodes.length === 0}
            className="w-full sm:w-auto px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-100 disabled:text-slate-400 text-white text-sm font-semibold rounded-xl transition-all shadow-xs disabled:cursor-not-allowed cursor-pointer"
          >
            下載全部集數
          </button>
        </div>
      )}

      <h4 className="text-sm font-semibold text-slate-500 mb-3">
        解析結果清單
      </h4>

      {episodes.length === 0 ? (
        <div className="text-center py-8 border-2 border-dashed border-slate-100 rounded-xl">
          <p className="text-sm text-slate-400">目前空空如也，請在上方輸入網址解析。</p>
        </div>
      ) : (
        <ul className="divide-y divide-slate-100">
          {episodes.map((ep, index) => {
            const task = episodeTasks[ep.name];
            const isButtonDisabled = task?.status === 'downloading' || task?.status === 'pending' || task?.status === 'completed';

            // 根據不同下載狀態，動態分配按鈕的 Tailwind Class 樣式
            let btnStyle = "px-3 py-1.5 text-xs font-medium rounded-lg transition-all cursor-pointer bg-slate-100 hover:bg-slate-200 text-slate-700";
            if (task?.status === 'completed') {
              btnStyle = "px-3 py-1.5 text-xs font-semibold rounded-lg bg-emerald-50 text-emerald-600 border border-emerald-100 cursor-not-allowed";
            } else if (task?.status === 'downloading' || task?.status === 'pending') {
              btnStyle = "px-3 py-1.5 text-xs font-semibold rounded-lg bg-blue-50 text-blue-600 border border-blue-100 cursor-not-allowed animate-pulse";
            }

            return (
              <li key={index} className="py-3.5 flex flex-col md:flex-row md:items-center justify-between gap-3">
                {/* 左側：集數名稱與按鈕 */}
                <div className="flex items-center justify-between flex-1 md:mr-6">
                  <span className="text-sm font-medium text-slate-800">{ep.name}</span>
                  <button 
                    onClick={() => submitDownloadTask([ep])}
                    disabled={isButtonDisabled}
                    className={btnStyle}
                  >
                    {task?.status === 'completed' ? '已完成' : (task?.status === 'downloading' || task?.status === 'pending' ? '處理中...' : '下載此集')}
                  </button>
                </div>

                {/* 右側：下載進度條與數據回報 */}
                {task && (
                  <div className="flex items-center gap-3 w-full md:max-w-xs bg-slate-50 p-2 rounded-xl border border-slate-100">
                    {/* 進度條骨架 */}
                    <div className="flex-1 bg-slate-200/70 rounded-full h-2 overflow-hidden">
                      <div 
                        style={{ width: `${task.progress}%` }} 
                        className={`h-full rounded-full transition-all duration-300 ${
                          task.status === 'completed' ? 'bg-emerald-500' : 'bg-blue-500'
                        }`}
                      ></div>
                    </div>
                    {/* 狀態文字 */}
                    <span className="text-xs font-bold text-slate-600 min-w-[75px] text-right">
                      {task.status === 'pending' && '等待中'}
                      {task.status === 'downloading' && `${task.progress}%`}
                      {task.status === 'completed' && '完成'}
                    </span>
                  </div>
                )}
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}

export default EpisodeList;
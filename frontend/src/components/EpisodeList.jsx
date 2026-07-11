function EpisodeList({ 
  animeTitle, 
  episodes, 
  episodeTasks, 
  handleDownloadAll, 
  hasAnyAvailableEpisode, 
  submitDownloadTask 
}) {
  return (
    <div>
      {animeTitle && (
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', maxWidth: '600px', marginBottom: '15px' }}>
          <h3 style={{ color: '#2b6cb0', margin: 0 }}>當前動畫：{animeTitle}</h3>
          <button
            onClick={handleDownloadAll}
            disabled={!hasAnyAvailableEpisode || episodes.length === 0}
            style={{ 
              padding: '8px 16px', 
              backgroundColor: hasAnyAvailableEpisode ? '#3182ce' : '#cbd5e0', 
              color: '#fff', 
              border: 'none', 
              borderRadius: '4px', 
              cursor: hasAnyAvailableEpisode ? 'pointer' : 'not-allowed' 
            }}
          >
            下載全部集數
          </button>
        </div>
      )}

      <h3>解析結果清單：</h3>
      {episodes.length === 0 ? (
        <p style={{ color: '#888' }}>目前沒有資料。</p>
      ) : (
        <ul style={{ paddingLeft: '0', listStyle: 'none' }}>
          {episodes.map((ep, index) => {
            const task = episodeTasks[ep.name];
            const isButtonDisabled = task?.status === 'downloading' || task?.status === 'pending' || task?.status === 'completed';

            return (
              <li key={index} style={{ padding: '12px', borderBottom: '1px solid #edf2f7', maxWidth: '600px' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                  <strong style={{ fontSize: '15px' }}>{ep.name}</strong> 
                  <button 
                    onClick={() => submitDownloadTask([ep])}
                    disabled={isButtonDisabled}
                    style={{ padding: '4px 12px', cursor: isButtonDisabled ? 'not-allowed' : 'pointer', borderRadius: '4px' }}
                  >
                    {task?.status === 'completed' ? '已完成' : (task?.status === 'downloading' || task?.status === 'pending' ? '處理中' : '下載此集')}
                  </button>
                </div>

                {task && (
                  <div style={{ display: 'flex', alignItems: 'center', gap: '15px' }}>
                    <div style={{ width: '100%', maxWidth: '300px', backgroundColor: '#e2e8f0', borderRadius: '4px', height: '8px', overflow: 'hidden' }}>
                      <div style={{ width: `${task.progress}%`, backgroundColor: task.status === 'completed' ? '#38a169' : '#3182ce', height: '100%', transition: 'width 0.2s' }}></div>
                    </div>
                    <span style={{ fontSize: '12px', minWidth: '50px', color: '#4a5568', fontWeight: 'bold' }}>
                      {task.status === 'pending' && '等待中'}
                      {task.status === 'downloading' && `下載中 ${task.progress}%`}
                      {task.status === 'completed' && '下載完成'}
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
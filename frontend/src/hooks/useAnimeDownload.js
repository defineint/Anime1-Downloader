import { useState, useEffect } from 'react';

export function useAnimeDownload() {
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [animeTitle, setAnimeTitle] = useState('');
  const [episodes, setEpisodes] = useState([]);
  const [basePath, setBasePath] = useState(() => localStorage.getItem('anime_download_path') || '');
  const [episodeTasks, setEpisodeTasks] = useState({});

  // 同步本地儲存路徑
  useEffect(() => {
    localStorage.setItem('anime_download_path', basePath);
  }, [basePath]);

  // 輪詢進度
  const startPolling = (taskId) => {
    if (!taskId) return;
    const intervalId = setInterval(async () => {
      try {
        const response = await fetch(`http://127.0.0.1:8000/api/progress/${taskId}`);
        if (!response.ok) {
          clearInterval(intervalId);
          return;
        }
        const data = await response.json();
        if (data.progress_map) {
          setEpisodeTasks((prev) => {
            const nextTasks = { ...prev };
            Object.entries(data.progress_map).forEach(([epName, epProgress]) => {
              nextTasks[epName] = {
                progress: epProgress,
                status: epProgress >= 100 ? 'completed' : 'downloading'
              };
            });
            return nextTasks;
          });
        }
        if (data.status === 'completed') clearInterval(intervalId);
      } catch (error) {
        console.error('輪詢進度出錯:', error);
        clearInterval(intervalId);
      }
    }, 1000);
  };

  // 初始化同步全域任務
  useEffect(() => {
    const syncActiveTasks = async () => {
      try {
        const response = await fetch('http://127.0.0.1:8000/api/active-tasks');
        if (!response.ok) return;
        const result = await response.json();
        if (result.status === 'success' && result.active_tasks) {
          Object.entries(result.active_tasks).forEach(([taskId, taskData]) => {
            if (!taskData || !taskData.progress_map) return;
            setEpisodeTasks((prev) => {
              const nextTasks = { ...prev };
              Object.entries(taskData.progress_map).forEach(([epName, epProgress]) => {
                nextTasks[epName] = {
                  progress: epProgress,
                  status: epProgress >= 100 ? 'completed' : 'downloading'
                };
              });
              return nextTasks;
            });
            startPolling(taskId);
          });
        }
      } catch (error) {
        console.error('初始化全域任務同步失敗:', error);
      }
    };
    syncActiveTasks();
  }, []);

  // 解析網址
  const handleParse = async () => {
    if (!url) return alert('請先輸入網址！');
    setLoading(true);
    try {
      const response = await fetch('http://127.0.0.1:8000/api/parse', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url }),
      });
      const result = await response.json();
      if (result.status === 'success' && result.data) {
        setAnimeTitle(result.data.title || '');
        setEpisodes(result.data.episodes || []);
        setEpisodeTasks((prev) => {
          const nextTasks = { ...prev };
          result.data.episodes.forEach(ep => {
            if (ep.is_existed) {
              nextTasks[ep.name] = { progress: 100, status: 'completed' };
            }
          });
          return nextTasks;
        });
      } else {
        alert('解析失敗！');
      }
    } catch (error) {
      alert('後端連線失敗！');
    } finally {
      setLoading(false);
    }
  };

  // 發送下載請求
  const submitDownloadTask = async (selectedEpisodes) => {
    if (!Array.isArray(selectedEpisodes) || selectedEpisodes.length === 0) return;
    if (!basePath) return alert('請先輸入本機儲存路徑！');

    setEpisodeTasks((prev) => {
      const nextTasks = { ...prev };
      selectedEpisodes.forEach(ep => {
        nextTasks[ep.name] = { progress: 0, status: 'pending' };
      });
      return nextTasks;
    });

    try {
      const payload = {
        anime_title: animeTitle,
        base_path: basePath,
        episodes: selectedEpisodes,
      };
      const response = await fetch('http://127.0.0.1:8000/api/download', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      const result = await response.json();
      if (result.status === 'success' && result.task_id) {
        startPolling(result.task_id);
      } else {
        alert('下載任務建立失敗');
      }
    } catch (error) {
      alert('無法連線到下載 API！');
    }
  };

  // 下載全部
  const handleDownloadAll = () => {
    const remainingEpisodes = episodes.filter(ep => {
      const task = episodeTasks[ep.name];
      return !task || (task.status !== 'downloading' && task.status !== 'pending' && task.status !== 'completed');
    });
    if (remainingEpisodes.length === 0) return alert('所有集數皆已在下載隊列中或已完成！');
    submitDownloadTask(remainingEpisodes);
  };

  // 檢查可用狀態
  const hasAnyAvailableEpisode = episodes.some(ep => {
    const task = episodeTasks[ep.name];
    return !task || (task.status !== 'downloading' && task.status !== 'pending' && task.status !== 'completed');
  });

  // 把 UI 渲染需要用到的變數和方法通通丟出去
  return {
    url, setUrl,
    loading,
    animeTitle,
    episodes,
    basePath, setBasePath,
    episodeTasks,
    handleParse,
    submitDownloadTask,
    handleDownloadAll,
    hasAnyAvailableEpisode
  };
}
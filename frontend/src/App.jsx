import { useAnimeDownload } from './hooks/useAnimeDownload';
import SettingsCard from './components/SettingsCard';
import EpisodeList from './components/EpisodeList';

function App() {
  const downloadBrain = useAnimeDownload();

  return (
    <div style={{ padding: '30px', fontFamily: 'sans-serif', maxWidth: '800px', margin: '0 auto' }}>
      <h2>anime1 動漫下載全端工具</h2>
      <hr style={{ border: 'none', borderTop: '1px solid #e2e8f0', margin: '20px 0' }} />
      
      {/* 區塊一：設定與網址輸入 */}
      <SettingsCard 
        url={downloadBrain.url}
        setUrl={downloadBrain.setUrl}
        basePath={downloadBrain.basePath}
        setBasePath={downloadBrain.setBasePath}
        loading={downloadBrain.loading}
        handleParse={downloadBrain.handleParse}
      />

      {/* 區塊二：解析結果與下載進度 */}
      <EpisodeList 
        animeTitle={downloadBrain.animeTitle}
        episodes={downloadBrain.episodes}
        episodeTasks={downloadBrain.episodeTasks}
        handleDownloadAll={downloadBrain.handleDownloadAll}
        hasAnyAvailableEpisode={downloadBrain.hasAnyAvailableEpisode}
        submitDownloadTask={downloadBrain.submitDownloadTask}
      />
    </div>
  );
}

export default App;
import React, { useState, useEffect, useRef } from 'react';
import { createRoot } from 'react-dom/client';

// Types mimicking the Pydantic schemas
interface ObservationInput {
  metric_code: string;
  recorded_at: string;
  value_numeric: number | null;
  value_text: string | null;
  raw_metadata: any;
}

const DEFAULT_USER_ID = "d290f1ee-6c54-4b01-90e6-d701748f0851";
const DEFAULT_API_URL = "http://localhost:8080";

const App = () => {
  const [activeTab, setActiveTab] = useState('ingestion');
  const [logs, setLogs] = useState<string[]>([]);
  const [apiUrl, setApiUrl] = useState(DEFAULT_API_URL);
  const [userId, setUserId] = useState(DEFAULT_USER_ID);
  const [healthStatus, setHealthStatus] = useState<'checking' | 'healthy' | 'error' | 'mock'>('checking');
  
  // Mock Mode State
  const [useMock, setUseMock] = useState(true);

  // Ingestion State
  const [batchSize, setBatchSize] = useState(500);
  const [ingesting, setIngesting] = useState(false);

  // Journal State
  const [journalContent, setJournalContent] = useState('Feeling great today! Low stress levels.');
  const [mood, setMood] = useState(8);

  // Media State
  const [filename, setFilename] = useState('lab_results_2024.pdf');
  const [fileType, setFileType] = useState('LabReport');
  
  const log = (msg: string | object) => {
    const timestamp = new Date().toLocaleTimeString();
    const content = typeof msg === 'object' ? JSON.stringify(msg, null, 2) : msg;
    setLogs(prev => [`[${timestamp}] ${content}`, ...prev]);
  };

  const checkHealth = async () => {
    if (useMock) {
        setHealthStatus('mock');
        return;
    }
    setHealthStatus('checking');
    try {
      const res = await fetch(`${apiUrl}/`);
      if (res.ok) setHealthStatus('healthy');
      else setHealthStatus('error');
    } catch (e) {
      setHealthStatus('error');
    }
  };

  useEffect(() => {
    checkHealth();
  }, [apiUrl, useMock]);

  // --- MOCK API HELPERS ---
  const mockDelay = (ms = 600) => new Promise(resolve => setTimeout(resolve, ms));

  const generateBatchData = (count: number): ObservationInput[] => {
    const metrics = ['HEALX_TEST_TOTAL', 'HEALX_VIT_D', 'HK_HR_RESTING', 'HK_VO2_MAX'];
    return Array.from({ length: count }).map(() => ({
      metric_code: metrics[Math.floor(Math.random() * metrics.length)],
      recorded_at: new Date().toISOString(),
      value_numeric: Number((Math.random() * 1000).toFixed(2)),
      value_text: null,
      raw_metadata: { source: 'Web Harness' }
    }));
  };

  const handleIngest = async () => {
    setIngesting(true);
    log(`Generating ${batchSize} synthetic records...`);
    
    try {
      const payload = {
        source_name: "Web Test Harness",
        data: generateBatchData(batchSize)
      };

      const start = performance.now();
      let responseDetails;

      if (useMock) {
        await mockDelay(800);
        responseDetails = { 
            processed: batchSize, 
            skipped_unknown_metrics: [], 
            source_id: 123 
        };
        log(`[MOCK] Simulated backend processing...`);
      } else {
        const res = await fetch(`${apiUrl}/observations/batch`, {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${userId}`
            },
            body: JSON.stringify(payload)
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const json = await res.json();
        responseDetails = json.details;
      }

      const end = performance.now();
      const duration = (end - start).toFixed(2);
      
      log(`✅ Batch Ingest Success! Took ${duration}ms. Processed: ${responseDetails.processed}`);

    } catch (e) {
      log(`❌ Error: ${e}`);
    } finally {
      setIngesting(false);
    }
  };

  const handleJournal = async () => {
     log(`Saving journal entry...`);
     try {
       let json;
       if (useMock) {
         await mockDelay(400);
         json = { status: "saved", id: "mock-uuid-" + Math.random().toString(36).substr(2, 9) };
         log(`[MOCK] Entry saved to local state.`);
       } else {
         const res = await fetch(`${apiUrl}/journal`, {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${userId}`
            },
            body: JSON.stringify({
                entry_date: new Date().toISOString().split('T')[0],
                content: journalContent,
                mood_score: mood,
                tags: ["demo", "web-harness"]
            })
         });
         if (!res.ok) throw new Error(`HTTP ${res.status}`);
         json = await res.json();
       }
       log(`✅ Journal Saved. ID: ${json.id}`);
     } catch (e) {
       log(`❌ Error: ${e}`);
     }
  };

  const handleMedia = async () => {
    log(`Requesting upload URL for ${filename}...`);
    try {
        let json;
        if (useMock) {
            await mockDelay(500);
            json = {
                upload_url: `https://storage.googleapis.com/fake-bucket/users/${userId}/${filename}?token=mock-token`,
                file_path: `users/${userId}/uploads/${filename}`
            };
            log(`[MOCK] Generated fake signed URL.`);
        } else {
            const res = await fetch(`${apiUrl}/media/upload-url`, {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${userId}`
            },
            body: JSON.stringify({
                filename: filename,
                file_type: fileType,
                content_type: "application/pdf"
            })
            });
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            json = await res.json();
        }
        
        log(`✅ Signed URL generated!`);
        log(json);
        // In a real app, we would now PUT the file to json.upload_url

    } catch (e) {
        log(`❌ Error: ${e}`);
    }
  };

  // Status Indicator Color
  const getStatusColor = () => {
      switch(healthStatus) {
          case 'healthy': return '#10b981';
          case 'error': return '#ef4444';
          case 'mock': return '#a855f7'; // Purple for mock
          default: return '#f59e0b';
      }
  };

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '2rem', display: 'grid', gridTemplateColumns: '1fr 350px', gap: '2rem' }}>
      
      {/* LEFT COLUMN: CONTROLS */}
      <div>
        <header style={{ marginBottom: '2rem', borderBottom: '1px solid #334155', paddingBottom: '1rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <h1 style={{ margin: 0, fontSize: '1.5rem', fontWeight: 600 }}>HealX Developer Console</h1>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.875rem' }}>
                    <div style={{ width: 8, height: 8, borderRadius: '50%', background: getStatusColor() }}></div>
                    <span style={{ color: '#94a3b8' }}>API: {healthStatus.toUpperCase()}</span>
                </div>
            </div>
            
            {/* Connection Settings */}
            <div style={{ marginTop: '1rem', background: '#1e293b', padding: '1rem', borderRadius: '8px', border: '1px solid #334155' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                     <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer', color: useMock ? '#fff' : '#94a3b8' }}>
                        <input type="checkbox" checked={useMock} onChange={e => setUseMock(e.target.checked)} />
                        <strong>Mock Backend (Demo Mode)</strong>
                     </label>
                </div>
                {!useMock && (
                    <div style={{ display: 'flex', gap: '1rem', marginTop: '0.5rem' }}>
                        <input 
                            value={apiUrl} 
                            onChange={e => setApiUrl(e.target.value)} 
                            style={{ background: '#0f172a', border: '1px solid #334155', color: '#fff', padding: '0.5rem', borderRadius: '4px', flex: 1 }} 
                            placeholder="http://localhost:8080"
                        />
                        <input 
                            value={userId} 
                            onChange={e => setUserId(e.target.value)} 
                            style={{ background: '#0f172a', border: '1px solid #334155', color: '#94a3b8', padding: '0.5rem', borderRadius: '4px', width: '300px' }} 
                            placeholder="User UUID"
                        />
                    </div>
                )}
                {useMock && <div style={{ fontSize: '0.8rem', color: '#94a3b8', marginTop: '0.25rem' }}>Running in browser-only mode. No backend required.</div>}
            </div>
        </header>

        {/* TABS */}
        <div style={{ display: 'flex', gap: '1rem', marginBottom: '1.5rem' }}>
            {['ingestion', 'journal', 'media'].map(tab => (
                <button 
                    key={tab}
                    onClick={() => setActiveTab(tab)}
                    style={{
                        background: activeTab === tab ? '#3b82f6' : 'transparent',
                        color: activeTab === tab ? '#fff' : '#94a3b8',
                        border: 'none',
                        padding: '0.5rem 1rem',
                        borderRadius: '6px',
                        cursor: 'pointer',
                        fontWeight: 500,
                        textTransform: 'capitalize'
                    }}
                >
                    {tab}
                </button>
            ))}
        </div>

        {/* TAB CONTENT */}
        <div style={{ background: '#1e293b', padding: '2rem', borderRadius: '8px', border: '1px solid #334155' }}>
            
            {activeTab === 'ingestion' && (
                <div>
                    <h2 style={{ marginTop: 0 }}>High-Throughput Ingestion</h2>
                    <p style={{ color: '#94a3b8' }}>Generate and send synthetic health records to test write performance.</p>
                    
                    <div style={{ margin: '2rem 0' }}>
                        <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.875rem', color: '#94a3b8' }}>Batch Size: {batchSize} rows</label>
                        <input 
                            type="range" 
                            min="100" 
                            max="5000" 
                            step="100" 
                            value={batchSize} 
                            onChange={e => setBatchSize(Number(e.target.value))}
                            style={{ width: '100%' }}
                        />
                    </div>

                    <button 
                        onClick={handleIngest}
                        disabled={ingesting}
                        style={{
                            background: ingesting ? '#334155' : '#10b981',
                            color: '#fff',
                            border: 'none',
                            padding: '0.75rem 1.5rem',
                            borderRadius: '6px',
                            cursor: ingesting ? 'not-allowed' : 'pointer',
                            fontSize: '1rem',
                            fontWeight: 600,
                            width: '100%'
                        }}
                    >
                        {ingesting ? 'Processing...' : 'Run Ingestion Test'}
                    </button>
                </div>
            )}

            {activeTab === 'journal' && (
                <div>
                     <h2 style={{ marginTop: 0 }}>Journal Entry</h2>
                     <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                        <div>
                            <label style={{ display: 'block', marginBottom: '0.5rem', color: '#94a3b8' }}>Mood (1-10)</label>
                            <input 
                                type="number" min="1" max="10" 
                                value={mood} 
                                onChange={e => setMood(Number(e.target.value))}
                                style={{ background: '#0f172a', border: '1px solid #334155', color: '#fff', padding: '0.5rem', borderRadius: '4px' }}
                            />
                        </div>
                        <div>
                            <label style={{ display: 'block', marginBottom: '0.5rem', color: '#94a3b8' }}>Content</label>
                            <textarea 
                                value={journalContent} 
                                onChange={e => setJournalContent(e.target.value)}
                                rows={6}
                                style={{ width: '100%', background: '#0f172a', border: '1px solid #334155', color: '#fff', padding: '0.5rem', borderRadius: '4px' }}
                            />
                        </div>
                        <button 
                            onClick={handleJournal}
                            style={{ background: '#8b5cf6', color: '#fff', border: 'none', padding: '0.75rem', borderRadius: '6px', cursor: 'pointer', fontWeight: 600 }}
                        >
                            Save Entry
                        </button>
                     </div>
                </div>
            )}

            {activeTab === 'media' && (
                <div>
                     <h2 style={{ marginTop: 0 }}>Secure Media Upload</h2>
                     <p style={{ color: '#94a3b8' }}>Generate a time-limited signed URL for direct-to-object-storage upload.</p>
                     
                     <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', marginTop: '1.5rem' }}>
                        <div>
                            <label style={{ display: 'block', marginBottom: '0.5rem', color: '#94a3b8' }}>File Name</label>
                            <input 
                                value={filename} 
                                onChange={e => setFilename(e.target.value)}
                                style={{ width: '100%', background: '#0f172a', border: '1px solid #334155', color: '#fff', padding: '0.5rem', borderRadius: '4px' }}
                            />
                        </div>
                        <div>
                             <label style={{ display: 'block', marginBottom: '0.5rem', color: '#94a3b8' }}>Category</label>
                             <select 
                                value={fileType}
                                onChange={e => setFileType(e.target.value)}
                                style={{ width: '100%', background: '#0f172a', border: '1px solid #334155', color: '#fff', padding: '0.5rem', borderRadius: '4px' }}
                             >
                                <option value="LabReport">Lab Report</option>
                                <option value="Scan">Scan (MRI/X-Ray)</option>
                                <option value="UserUpload">General Upload</option>
                             </select>
                        </div>
                        <button 
                            onClick={handleMedia}
                            style={{ background: '#ec4899', color: '#fff', border: 'none', padding: '0.75rem', borderRadius: '6px', cursor: 'pointer', fontWeight: 600 }}
                        >
                            Generate Signed URL
                        </button>
                     </div>
                </div>
            )}

        </div>
      </div>

      {/* RIGHT COLUMN: LOGS */}
      <div style={{ background: '#1e293b', borderRadius: '8px', border: '1px solid #334155', display: 'flex', flexDirection: 'column', height: 'calc(100vh - 4rem)', position: 'sticky', top: '2rem' }}>
        <div style={{ padding: '1rem', borderBottom: '1px solid #334155', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h3 style={{ margin: 0, fontSize: '1rem' }}>Live Logs</h3>
            <button onClick={() => setLogs([])} style={{ background: 'transparent', border: 'none', color: '#94a3b8', cursor: 'pointer', fontSize: '0.75rem' }}>Clear</button>
        </div>
        <div style={{ flex: 1, overflowY: 'auto', padding: '1rem', fontFamily: 'monospace', fontSize: '0.8rem', color: '#cbd5e1' }}>
            {logs.length === 0 && <span style={{ color: '#64748b' }}>Waiting for activity...</span>}
            {logs.map((log, i) => (
                <div key={i} style={{ marginBottom: '0.5rem', whiteSpace: 'pre-wrap', borderBottom: '1px dashed #334155', paddingBottom: '0.5rem' }}>{log}</div>
            ))}
        </div>
      </div>

    </div>
  );
};

const container = document.getElementById('root');
const root = createRoot(container!);
root.render(<App />);
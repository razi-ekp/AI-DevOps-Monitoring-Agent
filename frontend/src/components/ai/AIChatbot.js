import { useState, useRef, useEffect } from 'react';
import { Spinner } from '../ui';

const API = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export default function AIChatbot() {
  const [open, setOpen]       = useState(false);
  const [msgs, setMsgs]       = useState([
    { role: 'ai', content: 'Hi! Ask me anything about your infrastructure — "What happened?", "Why is CPU high?", "Show recent incidents".' }
  ]);
  const [input,    setInput]  = useState('');
  const [loading,  setLoading]= useState(false);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [msgs]);

  const send = async () => {
    if (!input.trim() || loading) return;
    const userMsg = input.trim();
    setInput('');
    const newMsgs = [...msgs, { role: 'user', content: userMsg }];
    setMsgs(newMsgs);
    setLoading(true);

    try {
      const apiMsgs = newMsgs
        .filter(m => m.role !== 'ai' || newMsgs.indexOf(m) > 0)
        .map(m => ({ role: m.role === 'ai' ? 'assistant' : 'user', content: m.content }));

      const res = await fetch(`${API}/api/ai/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ messages: apiMsgs }),
      });
      const data = await res.json();
      setMsgs(prev => [...prev, { role: 'ai', content: data.reply || 'No response.' }]);
    } catch {
      setMsgs(prev => [...prev, { role: 'ai', content: '⚠️ Could not reach the AI service. Check backend.' }]);
    } finally {
      setLoading(false);
    }
  };

  const onKey = (e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); } };

  return (
    <>
      {open && (
        <div className="chat-panel">
          <div className="chat-header">
            <span style={{ width: 7, height: 7, borderRadius: '50%', background: '#22c55e', boxShadow: '0 0 6px #22c55e', display: 'inline-block' }} />
            AI DevOps Assistant
            <button onClick={() => setOpen(false)} style={{ marginLeft: 'auto', background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', fontSize: 16 }}>×</button>
          </div>
          <div className="chat-messages">
            {msgs.map((m, i) => (
              <div key={i} className={`chat-msg ${m.role}`}>{m.content}</div>
            ))}
            {loading && (
              <div className="chat-msg ai" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <Spinner /> Thinking…
              </div>
            )}
            <div ref={bottomRef} />
          </div>
          <div className="chat-input-row">
            <input
              className="chat-input"
              placeholder="Ask about your infrastructure…"
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={onKey}
              autoFocus
            />
            <button className="chat-send" onClick={send} disabled={loading || !input.trim()}>
              Send
            </button>
          </div>
        </div>
      )}
      <button className="chat-fab" onClick={() => setOpen(o => !o)} title="AI Assistant">
        {open ? '×' : '🤖'}
      </button>
    </>
  );
}

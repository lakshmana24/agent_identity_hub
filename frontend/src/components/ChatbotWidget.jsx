import React, { useState } from 'react';
import { MessageSquare, X, Send, Bot, User, Sparkles } from 'lucide-react';
import { api } from '../api/client';

export const ChatbotWidget = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [question, setQuestion] = useState('');
  const [messages, setMessages] = useState([
    {
      sender: 'bot',
      text: 'Hello! I am your AIH Governance Assistant. Ask me about registered agents, owning teams, stale agent reports, or audit logs.'
    }
  ]);
  const [loading, setLoading] = useState(false);

  const handleSend = async (e) => {
    e.preventDefault();
    if (!question.trim() || loading) return;

    const userText = question.trim();
    setQuestion('');
    setMessages((prev) => [...prev, { sender: 'user', text: userText }]);
    setLoading(true);

    try {
      const res = await api.post('/chatbot/ask', { question: userText });
      setMessages((prev) => [...prev, { sender: 'bot', text: res.data.answer }]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { sender: 'bot', text: err.response?.data?.detail || 'Sorry, I encountered an error answering that query.' }
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ position: 'fixed', bottom: '1.5rem', right: '1.5rem', zIndex: 1000 }}>
      {!isOpen && (
        <button
          onClick={() => setIsOpen(true)}
          className="btn btn-primary"
          style={{
            borderRadius: '50px',
            padding: '0.85rem 1.25rem',
            boxShadow: '0 8px 24px rgba(59, 130, 246, 0.4)',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            fontSize: '0.9rem'
          }}
        >
          <Sparkles size={18} />
          <span>AI Insights Chat</span>
        </button>
      )}

      {isOpen && (
        <div
          className="glass-card"
          style={{
            width: '380px',
            height: '500px',
            display: 'flex',
            flexDirection: 'column',
            boxShadow: '0 12px 36px rgba(0, 0, 0, 0.6)',
            borderRadius: '16px',
            overflow: 'hidden',
            border: '1px solid var(--border-color)'
          }}
        >
          {/* Header */}
          <div
            style={{
              padding: '1rem 1.25rem',
              background: 'rgba(30, 41, 59, 0.9)',
              borderBottom: '1px solid var(--border-color)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between'
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Bot size={20} style={{ color: 'var(--accent-purple)' }} />
              <div>
                <div style={{ fontWeight: 700, fontSize: '0.9rem' }}>AIH Insights Chatbot</div>
                <div style={{ fontSize: '0.7rem', color: 'var(--text-dim)' }}>Read-only governance assistant</div>
              </div>
            </div>
            <button
              onClick={() => setIsOpen(false)}
              style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}
            >
              <X size={18} />
            </button>
          </div>

          {/* Messages Feed */}
          <div style={{ flex: 1, padding: '1rem', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            {messages.map((msg, idx) => (
              <div
                key={idx}
                style={{
                  display: 'flex',
                  justifyContent: msg.sender === 'user' ? 'flex-end' : 'flex-start',
                  gap: '0.5rem'
                }}
              >
                {msg.sender === 'bot' && <Bot size={16} style={{ color: 'var(--accent-purple)', marginTop: '0.2rem' }} />}
                <div
                  style={{
                    maxWidth: '82%',
                    padding: '0.65rem 0.85rem',
                    borderRadius: '12px',
                    fontSize: '0.825rem',
                    whiteSpace: 'pre-wrap',
                    lineHeight: '1.4',
                    background: msg.sender === 'user' ? 'var(--primary)' : 'rgba(30, 41, 59, 0.8)',
                    color: msg.sender === 'user' ? '#fff' : 'var(--text-main)',
                    border: msg.sender === 'bot' ? '1px solid var(--border-color)' : 'none'
                  }}
                >
                  {msg.text}
                </div>
                {msg.sender === 'user' && <User size={16} style={{ color: 'var(--accent-cyan)', marginTop: '0.2rem' }} />}
              </div>
            ))}
            {loading && (
              <div style={{ fontSize: '0.8rem', color: 'var(--text-dim)', fontStyle: 'italic', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                <Sparkles size={14} /> Querying AIH knowledge graph...
              </div>
            )}
          </div>

          {/* Input Bar */}
          <form onSubmit={handleSend} style={{ padding: '0.75rem', borderTop: '1px solid var(--border-color)', display: 'flex', gap: '0.5rem', background: 'rgba(15, 23, 42, 0.8)' }}>
            <input
              type="text"
              className="input-field"
              placeholder="Ask a question about AIH data..."
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              style={{ fontSize: '0.825rem', padding: '0.5rem 0.75rem' }}
            />
            <button type="submit" className="btn btn-primary" style={{ padding: '0.5rem 0.85rem' }} disabled={loading || !question.trim()}>
              <Send size={16} />
            </button>
          </form>
        </div>
      )}
    </div>
  );
};

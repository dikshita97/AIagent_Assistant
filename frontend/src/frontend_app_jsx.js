import React, { useState, useRef, useEffect } from 'react';
import { Send, Upload, X, Loader2, CheckCircle } from 'lucide-react';
import axios from 'axios';
import './App.css';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if ((!input.trim() && !file) || loading) return;

    const userMessage = {
      role: 'user',
      text: input,
      file: file ? { name: file.name, type: file.type } : null,
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    setLoading(true);

    try {
      const formData = new FormData();
      formData.append('text', input);
      if (file) {
        formData.append('file', file);
      }

      const response = await axios.post(`${API_URL}/api/process`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      const assistantMessage = {
        role: 'assistant',
        text: response.data.result,
        intent: response.data.intent,
        metadata: response.data.metadata,
        timestamp: new Date().toISOString()
      };

      setMessages(prev => [...prev, assistantMessage]);
      
    } catch (error) {
      const errorMessage = {
        role: 'assistant',
        text: `⚠️ Error: ${error.response?.data?.detail || error.message}\n\nPlease try again or rephrase your query.`,
        error: true,
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
      setInput('');
      setFile(null);
    }
  };

  const handleFileSelect = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      if (selectedFile.size > 10 * 1024 * 1024) {
        alert('File size must be less than 10MB');
        return;
      }
      setFile(selectedFile);
    }
  };

  const removeFile = () => {
    setFile(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const getFileIcon = (type) => {
    if (type?.startsWith('image/')) return '🖼️';
    if (type === 'application/pdf') return '📄';
    if (type?.startsWith('audio/')) return '🎵';
    return '📎';
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <div className="app-container">
      {/* Header */}
      <header className="app-header">
        <div className="header-content">
          <h1 className="header-title">Agentic Multi-Modal Assistant</h1>
          <p className="header-subtitle">
            Upload files or type your query. I'll understand and execute the task autonomously.
          </p>
        </div>
      </header>

      {/* Messages Container */}
      <main className="messages-container">
        <div className="messages-content">
          {messages.length === 0 && (
            <div className="welcome-screen">
              <div className="welcome-icon">
                <CheckCircle size={32} />
              </div>
              <h2 className="welcome-title">Ready to assist you</h2>
              <p className="welcome-text">
                Upload images, PDFs, or audio files, or paste text. I'll detect your intent and execute the right task.
              </p>
              <div className="feature-grid">
                <div className="feature-card">
                  <div className="feature-title">📄 Text & Files</div>
                  <div className="feature-desc">Extract, analyze, summarize</div>
                </div>
                <div className="feature-card">
                  <div className="feature-title">🎯 Smart Intent</div>
                  <div className="feature-desc">Auto-detects your goal</div>
                </div>
                <div className="feature-card">
                  <div className="feature-title">💬 Clarification</div>
                  <div className="feature-desc">Asks when unclear</div>
                </div>
                <div className="feature-card">
                  <div className="feature-title">⚡ Autonomous</div>
                  <div className="feature-desc">Plans and executes</div>
                </div>
              </div>
            </div>
          )}

          {messages.map((msg, idx) => (
            <div key={idx} className={`message-wrapper ${msg.role}`}>
              <div className={`message-bubble ${msg.role} ${msg.error ? 'error' : ''}`}>
                {msg.role === 'user' && msg.file && (
                  <div className="message-file-info">
                    <span>{getFileIcon(msg.file.type)}</span>
                    <span className="file-name">{msg.file.name}</span>
                  </div>
                )}
                <div className="message-text">
                  {msg.text.split('\n').map((line, i) => (
                    <p key={i}>{line}</p>
                  ))}
                </div>
                {msg.intent && msg.role === 'assistant' && (
                  <div className="message-metadata">
                    Intent: {msg.intent.replace(/_/g, ' ')}
                  </div>
                )}
              </div>
            </div>
          ))}

          {loading && (
            <div className="message-wrapper assistant">
              <div className="message-bubble assistant loading">
                <div className="loading-content">
                  <Loader2 className="spinner" size={16} />
                  <span>Processing your request...</span>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      </main>

      {/* Input Area */}
      <footer className="input-container">
        <div className="input-content">
          {file && (
            <div className="file-preview">
              <span>{getFileIcon(file.type)}</span>
              <span className="file-preview-name">{file.name}</span>
              <button onClick={removeFile} className="file-remove-btn">
                <X size={16} />
              </button>
            </div>
          )}
          
          <div className="input-row">
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileSelect}
              accept="image/*,.pdf,audio/*"
              className="file-input-hidden"
            />
            <button
              onClick={() => fileInputRef.current?.click()}
              className="upload-btn"
              disabled={loading}
            >
              <Upload size={16} />
              Upload
            </button>
            
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Type your message or upload a file..."
              className="text-input"
              disabled={loading}
            />
            
            <button
              onClick={handleSubmit}
              disabled={loading || (!input.trim() && !file)}
              className="send-btn"
            >
              <Send size={16} />
              Send
            </button>
          </div>
          
          <div className="input-hint">
            Supports: Images (JPG/PNG), PDFs, Audio (MP3/WAV/M4A), Text, YouTube URLs
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;
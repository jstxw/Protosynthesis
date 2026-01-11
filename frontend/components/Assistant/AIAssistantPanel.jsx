import React, { useState, useEffect, useRef } from 'react';
import { apiClient } from '../../services/api';
import './AIAssistantPanel.css';

const AIAssistantPanel = ({ currentNodes, selectedNode }) => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isExpanded, setIsExpanded] = useState(true);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Quick action buttons
  const quickActions = [
    { label: 'Add Node', query: 'How do I add a new node to my workflow?' },
    { label: 'Connect Nodes', query: 'How do I connect two nodes together?' },
    { label: 'Best Practices', query: 'What are the best practices for building workflows?' },
    { label: 'Debug Help', query: 'My workflow isn\'t working. How can I debug it?' }
  ];

  const sendMessage = async (messageText = null) => {
    const textToSend = messageText || input;

    if (!textToSend.trim() || isLoading) return;

    const userMessage = { role: 'user', content: textToSend };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await apiClient.post('/ai/chat', {
        message: textToSend,
        chatHistory: messages.map(m => ({ role: m.role, content: m.content })),
        workflowContext: {
          currentNodes: currentNodes || [],
          selectedNode: selectedNode
        }
      });

      const assistantMessage = {
        role: 'assistant',
        content: response.data.response,
        sources: response.data.sources
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Chat error:', error);
      const errorMessage = {
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again or rephrase your question.'
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleQuickAction = (action) => {
    sendMessage(action.query);
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className={`ai-assistant-panel ${isExpanded ? 'expanded' : 'collapsed'}`}>
      <div className="assistant-header">
        <div className="header-left">
          <span className="assistant-icon">🤖</span>
          <h3>AI Assistant</h3>
        </div>
        <button
          className="toggle-btn"
          onClick={() => setIsExpanded(!isExpanded)}
          title={isExpanded ? 'Collapse' : 'Expand'}
        >
          {isExpanded ? '→' : '←'}
        </button>
      </div>

      {isExpanded && (
        <>
          <div className="quick-actions">
            {quickActions.map((action, i) => (
              <button
                key={i}
                onClick={() => handleQuickAction(action)}
                className="quick-action-btn"
                disabled={isLoading}
              >
                {action.label}
              </button>
            ))}
          </div>

          <div className="messages-container">
            {messages.length === 0 && (
              <div className="welcome-message">
                <p>👋 Hi! I'm your workflow assistant.</p>
                <p>Ask me anything about:</p>
                <ul>
                  <li>Adding and connecting nodes</li>
                  <li>API configurations</li>
                  <li>Workflow best practices</li>
                  <li>Troubleshooting issues</li>
                </ul>
              </div>
            )}

            {messages.map((msg, i) => (
              <div key={i} className={`message ${msg.role}`}>
                <div className="message-avatar">
                  {msg.role === 'user' ? '👤' : '🤖'}
                </div>
                <div className="message-content">
                  <div className="message-text">{msg.content}</div>
                  {msg.sources && msg.sources.length > 0 && (
                    <div className="message-sources">
                      <span className="sources-label">Sources:</span>
                      {msg.sources.slice(0, 2).map((s, idx) => (
                        <span key={idx} className="source-tag">
                          {s.id.replace('node_', '').replace(/_/g, ' ')}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}

            {isLoading && (
              <div className="message assistant loading">
                <div className="message-avatar">🤖</div>
                <div className="message-content">
                  <div className="typing-indicator">
                    <span></span>
                    <span></span>
                    <span></span>
                  </div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          <div className="input-container">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask me anything about workflows..."
              disabled={isLoading}
              rows="2"
            />
            <button
              onClick={() => sendMessage()}
              disabled={isLoading || !input.trim()}
              className="send-btn"
            >
              <span>▲</span>
            </button>
          </div>

          <div className="powered-by">
            Powered by Moorcheh AI
          </div>
        </>
      )}
    </div>
  );
};

export default AIAssistantPanel;

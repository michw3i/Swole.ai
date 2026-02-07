// src/components/ChatBox.jsx
import { useState, useRef, useEffect } from 'react';
import './ChatBox.css';

function ChatBox({ messages, setMessages, uploadedImage }) {
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Function to format message text with markdown-like styling
  const formatMessage = (text) => {
    // Split by newlines to preserve structure
    const lines = text.split('\n');
    
    return lines.map((line, index) => {
      // Headers (##)
      if (line.startsWith('###')) {
        return <h4 key={index} style={{ margin: '12px 0 8px 0', fontSize: '1em', fontWeight: '600' }}>{line.replace(/^###\s*/, '')}</h4>;
      }
      if (line.startsWith('##')) {
        return <h3 key={index} style={{ margin: '16px 0 10px 0', fontSize: '1.1em', fontWeight: '700' }}>{line.replace(/^##\s*/, '')}</h3>;
      }
      if (line.startsWith('#')) {
        return <h2 key={index} style={{ margin: '18px 0 12px 0', fontSize: '1.2em', fontWeight: '800' }}>{line.replace(/^#\s*/, '')}</h2>;
      }
      
      // Bullet points
      if (line.trim().startsWith('- ') || line.trim().startsWith('• ')) {
        return (
          <li key={index} style={{ marginLeft: '20px', marginBottom: '6px' }}>
            {formatInlineMarkdown(line.replace(/^[\s-•]+/, ''))}
          </li>
        );
      }
      
      // Numbered lists
      if (/^\d+\./.test(line.trim())) {
        return (
          <li key={index} style={{ marginLeft: '20px', marginBottom: '6px', listStyleType: 'decimal' }}>
            {formatInlineMarkdown(line.replace(/^\d+\.\s*/, ''))}
          </li>
        );
      }
      
      // Empty lines
      if (line.trim() === '') {
        return <br key={index} />;
      }
      
      // Regular paragraphs
      return (
        <p key={index} style={{ margin: '8px 0', lineHeight: '1.6' }}>
          {formatInlineMarkdown(line)}
        </p>
      );
    });
  };

  // Format inline markdown (bold, italic, code)
  const formatInlineMarkdown = (text) => {
    const parts = [];
    let currentText = text;
    let key = 0;

    while (currentText.length > 0) {
      // Bold (**text** or __text__)
      const boldMatch = currentText.match(/(\*\*|__)(.*?)\1/);
      if (boldMatch && boldMatch.index === 0) {
        parts.push(<strong key={key++}>{boldMatch[2]}</strong>);
        currentText = currentText.slice(boldMatch[0].length);
        continue;
      }

      // Italic (*text* or _text_)
      const italicMatch = currentText.match(/(\*|_)(.*?)\1/);
      if (italicMatch && italicMatch.index === 0) {
        parts.push(<em key={key++}>{italicMatch[2]}</em>);
        currentText = currentText.slice(italicMatch[0].length);
        continue;
      }

      // Inline code (`text`)
      const codeMatch = currentText.match(/`([^`]+)`/);
      if (codeMatch && codeMatch.index === 0) {
        parts.push(
          <code key={key++} style={{ 
            background: '#f4f4f4', 
            padding: '2px 6px', 
            borderRadius: '4px',
            fontFamily: 'monospace',
            fontSize: '0.9em'
          }}>
            {codeMatch[1]}
          </code>
        );
        currentText = currentText.slice(codeMatch[0].length);
        continue;
      }

      // Find next special character
      const nextSpecial = currentText.search(/[\*_`]/);
      if (nextSpecial === -1) {
        parts.push(currentText);
        break;
      }

      // Add text before special character
      if (nextSpecial > 0) {
        parts.push(currentText.slice(0, nextSpecial));
        currentText = currentText.slice(nextSpecial);
      } else {
        // Single special character, just add it
        parts.push(currentText[0]);
        currentText = currentText.slice(1);
      }
    }

    return parts;
  };

  const sendMessage = async () => {
    if (!input.trim()) return;

    const userMessage = {
      role: 'user',
      content: input
    };

    setMessages([...messages, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const response = await fetch('http://localhost:8000/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          messages: [...messages, userMessage],
          image: uploadedImage
        })
      });

      if (!response.ok) {
        throw new Error('Chat request failed');
      }

      const data = await response.json();
      
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: data.content
      }]);
    } catch (error) {
      console.error('Error:', error);
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.'
      }]);
    }

    setLoading(false);
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="chatbox-container">
      <div className="messages-container">
        {messages.length === 0 && (
          <div className="welcome-message">
            👋 Hi! I'm your AI fitness trainer. Ask me anything about workouts, nutrition, or fitness goals!
          </div>
        )}
        {messages.map((msg, index) => (
          <div key={index} className={`message ${msg.role}`}>
            <div className="message-content">
              {msg.role === 'assistant' ? formatMessage(msg.content) : msg.content}
            </div>
          </div>
        ))}
        {loading && (
          <div className="message assistant">
            <div className="message-content loading">
              <span className="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </span>
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
          placeholder="Ask about workouts, nutrition, or fitness goals..."
          rows="3"
        />
        <button 
          onClick={sendMessage}
          disabled={loading || !input.trim()}
        >
          Send
        </button>
      </div>
    </div>
  );
}

export default ChatBox;
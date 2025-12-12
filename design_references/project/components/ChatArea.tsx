import { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Moon, Sun, PanelLeftClose, PanelLeft } from 'lucide-react';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

interface ChatAreaProps {
  isDarkMode: boolean;
  onToggleTheme: () => void;
  isSidebarOpen: boolean;
  onToggleSidebar: () => void;
}

export function ChatArea({ isDarkMode, onToggleTheme, isSidebarOpen, onToggleSidebar }: ChatAreaProps) {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      role: 'assistant',
      content: 'Hello! I\'m your RAG-powered assistant. Upload documents in the sidebar and I\'ll help you find information from them.',
      timestamp: new Date()
    }
  ]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = () => {
    if (!input.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsTyping(true);

    // Simulate AI response
    setTimeout(() => {
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: 'This is a simulated response. In a real implementation, this would analyze your uploaded documents and provide relevant information based on your query.',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, assistantMessage]);
      setIsTyping(false);
    }, 1000);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex-1 flex flex-col">
      {/* Header */}
      <div className={`px-6 py-4 ${isDarkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'} border-b`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button
              onClick={onToggleSidebar}
              className={`p-2 rounded-lg transition-colors ${
                isDarkMode 
                  ? 'bg-gray-700 hover:bg-gray-600 text-gray-300' 
                  : 'bg-gray-100 hover:bg-gray-200 text-gray-700'
              }`}
              aria-label="Toggle sidebar"
            >
              {isSidebarOpen ? <PanelLeftClose className="w-5 h-5" /> : <PanelLeft className="w-5 h-5" />}
            </button>
            <div>
              <h1 className={isDarkMode ? 'text-white' : 'text-gray-900'}>RAG Chatbot</h1>
              <p className={`text-sm ${isDarkMode ? 'text-gray-400' : 'text-gray-500'}`}>Ask questions about your uploaded documents</p>
            </div>
          </div>
          <button
            onClick={onToggleTheme}
            className={`p-2 rounded-lg transition-colors ${
              isDarkMode 
                ? 'bg-gray-700 hover:bg-gray-600 text-yellow-400' 
                : 'bg-gray-100 hover:bg-gray-200 text-gray-700'
            }`}
            aria-label="Toggle theme"
          >
            {isDarkMode ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
          </button>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-6">
        <div className="max-w-3xl mx-auto space-y-6">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex gap-4 ${message.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}
            >
              <div className={`flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center ${
                message.role === 'user' ? 'bg-blue-600' : isDarkMode ? 'bg-gray-700' : 'bg-gray-200'
              }`}>
                {message.role === 'user' ? (
                  <User className="w-5 h-5 text-white" />
                ) : (
                  <Bot className={`w-5 h-5 ${isDarkMode ? 'text-gray-300' : 'text-gray-700'}`} />
                )}
              </div>
              <div className={`flex-1 ${message.role === 'user' ? 'flex justify-end' : ''}`}>
                <div className={`inline-block max-w-2xl rounded-2xl px-5 py-3 ${
                  message.role === 'user'
                    ? 'bg-blue-600 text-white'
                    : isDarkMode 
                      ? 'bg-gray-800 border border-gray-700 text-gray-100'
                      : 'bg-white border border-gray-200 text-gray-900'
                }`}>
                  <p className="whitespace-pre-wrap">{message.content}</p>
                </div>
              </div>
            </div>
          ))}
          
          {isTyping && (
            <div className="flex gap-4">
              <div className={`flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center ${
                isDarkMode ? 'bg-gray-700' : 'bg-gray-200'
              }`}>
                <Bot className={`w-5 h-5 ${isDarkMode ? 'text-gray-300' : 'text-gray-700'}`} />
              </div>
              <div className={`rounded-2xl px-5 py-3 ${
                isDarkMode ? 'bg-gray-800 border border-gray-700' : 'bg-white border border-gray-200'
              }`}>
                <div className="flex gap-1">
                  <div className={`w-2 h-2 rounded-full animate-bounce ${isDarkMode ? 'bg-gray-500' : 'bg-gray-400'}`} style={{ animationDelay: '0ms' }}></div>
                  <div className={`w-2 h-2 rounded-full animate-bounce ${isDarkMode ? 'bg-gray-500' : 'bg-gray-400'}`} style={{ animationDelay: '150ms' }}></div>
                  <div className={`w-2 h-2 rounded-full animate-bounce ${isDarkMode ? 'bg-gray-500' : 'bg-gray-400'}`} style={{ animationDelay: '300ms' }}></div>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input Area */}
      <div className={`px-6 py-4 ${isDarkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'} border-t`}>
        <div className="max-w-3xl mx-auto">
          <div className="flex gap-3 items-end">
            <div className={`flex-1 rounded-2xl border transition-all ${
              isDarkMode 
                ? 'bg-gray-700 border-gray-600 focus-within:border-blue-500 focus-within:ring-2 focus-within:ring-blue-500/20'
                : 'bg-gray-50 border-gray-200 focus-within:border-blue-500 focus-within:ring-2 focus-within:ring-blue-100'
            }`}>
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Ask a question about your documents..."
                rows={1}
                className={`w-full bg-transparent px-5 py-3 resize-none outline-none max-h-32 ${
                  isDarkMode ? 'text-white placeholder-gray-500' : 'text-gray-900 placeholder-gray-500'
                }`}
                style={{ minHeight: '52px' }}
              />
            </div>
            <button
              onClick={handleSend}
              disabled={!input.trim()}
              className="flex-shrink-0 w-12 h-12 bg-blue-600 text-white rounded-xl hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors flex items-center justify-center"
            >
              <Send className="w-5 h-5" />
            </button>
          </div>
          <p className={`text-xs mt-2 text-center ${isDarkMode ? 'text-gray-600' : 'text-gray-400'}`}>
            Press Enter to send, Shift + Enter for new line
          </p>
        </div>
      </div>
    </div>
  );
}
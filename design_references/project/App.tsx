import { useState } from 'react';
import { Sidebar } from './components/Sidebar';
import { ChatArea } from './components/ChatArea';

export default function App() {
  const [uploadedFiles, setUploadedFiles] = useState<Array<{ id: string; name: string; size: number; uploadedAt: Date }>>([]);
  const [isDarkMode, setIsDarkMode] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);

  const handleFileUpload = (files: FileList | null) => {
    if (!files) return;
    
    const newFiles = Array.from(files).map(file => ({
      id: Math.random().toString(36).substr(2, 9),
      name: file.name,
      size: file.size,
      uploadedAt: new Date()
    }));
    
    setUploadedFiles(prev => [...prev, ...newFiles]);
  };

  const handleDeleteFile = (id: string) => {
    setUploadedFiles(prev => prev.filter(file => file.id !== id));
  };

  return (
    <div className={`flex h-screen ${isDarkMode ? 'bg-gray-900' : 'bg-gray-50'}`}>
      {isSidebarOpen && (
        <Sidebar 
          uploadedFiles={uploadedFiles}
          onFileUpload={handleFileUpload}
          onDeleteFile={handleDeleteFile}
          isDarkMode={isDarkMode}
        />
      )}
      <ChatArea 
        isDarkMode={isDarkMode}
        onToggleTheme={() => setIsDarkMode(!isDarkMode)}
        isSidebarOpen={isSidebarOpen}
        onToggleSidebar={() => setIsSidebarOpen(!isSidebarOpen)}
      />
    </div>
  );
}
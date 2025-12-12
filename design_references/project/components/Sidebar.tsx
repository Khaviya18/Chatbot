import { Upload, File, X, FolderOpen } from 'lucide-react';
import { useRef } from 'react';

interface UploadedFile {
  id: string;
  name: string;
  size: number;
  uploadedAt: Date;
}

interface SidebarProps {
  uploadedFiles: UploadedFile[];
  onFileUpload: (files: FileList | null) => void;
  onDeleteFile: (id: string) => void;
  isDarkMode: boolean;
}

export function Sidebar({ uploadedFiles, onFileUpload, onDeleteFile, isDarkMode }: SidebarProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    onFileUpload(e.dataTransfer.files);
  };

  return (
    <div className={`w-80 flex flex-col ${isDarkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'} border-r`}>
      <div className={`p-6 ${isDarkMode ? 'border-gray-700' : 'border-gray-200'} border-b`}>
        <h2 className={isDarkMode ? 'text-white' : 'text-gray-900'}>Knowledge Base</h2>
        <p className={`text-sm ${isDarkMode ? 'text-gray-400' : 'text-gray-500'}`}>Upload documents for RAG processing</p>
      </div>

      <div className="p-6">
        <div
          onDragOver={handleDragOver}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
            isDarkMode 
              ? 'border-gray-600 hover:border-blue-500 hover:bg-blue-500/10' 
              : 'border-gray-300 hover:border-blue-400 hover:bg-blue-50/50'
          }`}
        >
          <Upload className={`w-10 h-10 mx-auto mb-3 ${isDarkMode ? 'text-gray-500' : 'text-gray-400'}`} />
          <p className={`mb-1 ${isDarkMode ? 'text-gray-300' : 'text-gray-700'}`}>Click to upload or drag and drop</p>
          <p className={`text-sm ${isDarkMode ? 'text-gray-500' : 'text-gray-500'}`}>PDF, TXT, DOC, DOCX</p>
          <input
            ref={fileInputRef}
            type="file"
            multiple
            className="hidden"
            onChange={(e) => onFileUpload(e.target.files)}
            accept=".pdf,.txt,.doc,.docx"
          />
        </div>
      </div>

      <div className="flex-1 overflow-y-auto px-6 pb-6">
        <div className="flex items-center justify-between mb-3">
          <h3 className={`text-sm ${isDarkMode ? 'text-gray-300' : 'text-gray-700'}`}>Uploaded Files</h3>
          <span className={`text-sm ${isDarkMode ? 'text-gray-500' : 'text-gray-500'}`}>{uploadedFiles.length}</span>
        </div>
        
        {uploadedFiles.length === 0 ? (
          <div className="text-center py-8">
            <FolderOpen className={`w-12 h-12 mx-auto mb-2 ${isDarkMode ? 'text-gray-600' : 'text-gray-300'}`} />
            <p className={`text-sm ${isDarkMode ? 'text-gray-600' : 'text-gray-400'}`}>No files uploaded yet</p>
          </div>
        ) : (
          <div className="space-y-2">
            {uploadedFiles.map((file) => (
              <div
                key={file.id}
                className={`rounded-lg p-3 transition-colors group ${
                  isDarkMode ? 'bg-gray-700/50 hover:bg-gray-700' : 'bg-gray-50 hover:bg-gray-100'
                }`}
              >
                <div className="flex items-start gap-3">
                  <File className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
                  <div className="flex-1 min-w-0">
                    <p className={`text-sm truncate ${isDarkMode ? 'text-gray-200' : 'text-gray-900'}`}>{file.name}</p>
                    <p className={`text-xs mt-0.5 ${isDarkMode ? 'text-gray-500' : 'text-gray-500'}`}>
                      {formatFileSize(file.size)}
                    </p>
                  </div>
                  <button
                    onClick={() => onDeleteFile(file.id)}
                    className={`opacity-0 group-hover:opacity-100 transition-opacity p-1 rounded ${
                      isDarkMode ? 'hover:bg-gray-600' : 'hover:bg-gray-200'
                    }`}
                  >
                    <X className={`w-4 h-4 ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`} />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
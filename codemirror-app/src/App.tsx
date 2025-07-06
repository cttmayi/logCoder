import React, { useState, useEffect } from 'react';
import CodeEditor from './components/CodeEditor';
import './App.css';
// @ts-ignore
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
// @ts-ignore
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { ReactElement } from 'react';

// API基础URL
const API_BASE_URL = 'http://localhost:8000/api';

// 常量定义
const CONSTANTS = {
  FILE_EXTENSIONS: {
    PYTHON: '.py',
    JSONL: '.jsonl'
  },
  DEFAULT_NEW_FILE: 'new.py',
  MAX_DIR_NAME_LENGTH: 32,
  MAX_FILE_NAME_LENGTH: 64,
  LOGIN_EXPIRY_HOURS: 24,
  CODE_FOLD_THRESHOLD: 5
};

// 工具函数
const utils = {
  // 检查是否为游客用户
  isGuestUser: (username: string) => username === 'guest',
  
  // 格式化时间
  formatTime: (timestamp: number) => {
    const now = Date.now();
    const hours = Math.max(0, Math.floor((timestamp - now) / (1000 * 60 * 60)));
    return hours;
  },
  
  // 验证文件名
  validateFileName: (fileName: string, extension: string) => {
    if (!fileName.trim()) return '文件名不能为空';
    if (!fileName.endsWith(extension)) return `文件名必须以 ${extension} 结尾`;
    return null;
  },
  
  // 检查文件是否已存在
  isFileExists: (dirs: any[], dirName: string, fileName: string) => {
    const dir = dirs.find(d => d.name === dirName);
    return dir && dir.files.some((f: any) => f.name === fileName);
  },
  
  // 检查目录是否已存在
  isDirExists: (dirs: any[], dirName: string) => {
    return dirs.some(d => d.name === dirName);
  }
};

// 通用API调用函数
const apiCall = {
  // 通用GET请求
  async get(endpoint: string) {
    try {
      const response = await fetch(`${API_BASE_URL}${endpoint}`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error(`GET ${endpoint} failed:`, error);
      throw error;
    }
  },

  // 通用POST请求
  async post(endpoint: string, data: any) {
    try {
      const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error(`POST ${endpoint} failed:`, error);
      throw error;
    }
  },

  // 通用PUT请求
  async put(endpoint: string, data: any) {
    try {
      const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error(`PUT ${endpoint} failed:`, error);
      throw error;
    }
  },

  // 通用DELETE请求
  async delete(endpoint: string) {
    try {
      const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        method: 'DELETE',
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error(`DELETE ${endpoint} failed:`, error);
      throw error;
    }
  }
};

// 登录表单组件
interface LoginFormProps {
  onLogin: (username: string, password: string) => void;
  loading: boolean;
  error: string;
}

function LoginForm({ onLogin, loading, error }: LoginFormProps) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (username.trim() && password.trim()) {
      onLogin(username.trim(), password);
    }
  };

  const handleGuestLogin = () => {
    onLogin('guest', '');
  };

  return (
    <form onSubmit={handleSubmit} className="login-form">
      <div className="form-group">
        <label htmlFor="username">用户名</label>
        <input
          type="text"
          id="username"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          placeholder="请输入用户名"
          disabled={loading}
          required
        />
      </div>
      <div className="form-group">
        <label htmlFor="password">密码</label>
        <input
          type="password"
          id="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="请输入密码"
          disabled={loading}
          required
        />
      </div>
      {error && <div className="login-error">{error}</div>}
      <div className="login-buttons">
        <button type="submit" disabled={loading || !username.trim() || !password.trim()}>
          {loading ? '登录中...' : '登录'}
        </button>
        <button 
          type="button" 
          className="guest-login-btn" 
          onClick={handleGuestLogin}
          disabled={loading}
        >
          {loading ? '登录中...' : '游客登录'}
        </button>
      </div>
    </form>
  );
}

// 登录API
const loginUser = async (username: string, password: string) => {
  try {
    const response = await apiCall.post('/login', { username, password });
    return response;
  } catch (error) {
    console.error('Login failed:', error);
    return { success: false, message: '登录请求失败' };
  }
};

// 真实API调用函数
const fetchPythonDirs = async () => {
  try {
    return await apiCall.get('/dirs');
  } catch (error) {
    console.error('Failed to fetch directories:', error);
    // 如果API不可用，抛出错误而不是返回默认数据
    throw new Error('无法获取目录列表，请检查后端服务是否正常运行');
  }
};

// 真实API调用，按目录和文件名加载内容
const fetchFileContent = async (dir: string, file: string) => {
  try {
    const data = await apiCall.get(`/file/${dir}/${file}`);
    return data.content || '';
  } catch (error) {
    console.error('Failed to fetch file content:', error);
    // 如果API不可用，返回默认内容
    return `# ${file}\n# Content from ${dir}/${file}\ndef main():\n    print('Hello from ${dir}/${file}')\n`;
  }
};

// 真实API调用，保存文件内容
const saveFileContent = async (dir: string, file: string, content: string) => {
  try {
    const result = await apiCall.post(`/file/${dir}/${file}`, { content });
    console.log('File saved successfully:', result);
    return true;
  } catch (error) {
    console.error('Failed to save file:', error);
    alert(`保存失败: ${error}`);
    return false;
  }
};

// 真实API调用，上传文件
const uploadFile = async (file: File) => {
  try {
    const result = await apiCall.post('/upload', { fileName: file.name });
    console.log('File uploaded successfully:', result);
    return true;
  } catch (error) {
    console.error('Failed to upload file:', error);
    alert(`上传失败: ${error}`);
    return false;
  }
};

// 真实API调用，保存目录名
const saveDirName = async (oldName: string, newName: string) => {
  try {
    const result = await apiCall.put(`/dir/${oldName}`, { newName });
    console.log('Directory renamed successfully:', result);
    return true;
  } catch (error) {
    console.error('Failed to rename directory:', error);
    alert(`重命名失败: ${error}`);
    return false;
  }
};

// 真实API调用，删除目录
const deleteDir = async (dirName: string) => {
  try {
    const result = await apiCall.delete(`/dir/${dirName}`);
    if (result.success) {
      return true;
    } else {
      alert(`删除失败: ${result.message || '未知错误'}`);
      return false;
    }
  } catch (error) {
    alert(`删除失败: ${error}`);
    return false;
  }
};

// 真实API调用，创建目录
const createDirectory = async (name: string) => {
  try {
    const result = await apiCall.post('/dir', { name });
    console.log('Directory created successfully:', result);
    return true;
  } catch (error) {
    console.error('Failed to create directory:', error);
    alert(`创建目录失败: ${error}`);
    return false;
  }
};

// 真实API调用，创建文件
const createFile = async (dirName: string, fileName: string) => {
  try {
    const result = await apiCall.post(`/file/${dirName}`, { fileName });
    console.log('File created successfully:', result);
    return true;
  } catch (error) {
    console.error('Failed to create file:', error);
    alert(`创建文件失败: ${error}`);
    return false;
  }
};

// AI对话API
const aiChat = async (
  message: string,
  currentFile: string | null,
  currentCode: string,
  currentDir: string | null,
  messages: {role: 'user'|'ai', content: string}[]
) => {
  try {
    const response = await apiCall.post('/ai_chat', {
      message,
      currentFile,
      currentCode,
      currentDir,
      messages
    });
    return response;
  } catch (error) {
    console.error('AI chat failed:', error);
    return { success: false, explanation: 'AI请求失败' };
  }
};

// 代码执行API
const executeFile = async (dir: string, file: string, content: string) => {
  try {
    const response = await apiCall.post('/execute', {
      type: 'file',
      dir,
      file,
      content
    });
    return response;
  } catch (error) {
    console.error('Execute file failed:', error);
    return { success: false, message: '执行失败' };
  }
};

// AI消息组件，支持Markdown和代码块高亮
function AIMessage({ content, foldedMap, setFoldedMap, msgKey }: { content: string, foldedMap: { [key: string]: boolean }, setFoldedMap: React.Dispatch<React.SetStateAction<{ [key: string]: boolean }>>, msgKey: string }) {
  // 代码块折叠支持
  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      components={{
        code({node, inline, className, children, ...props}: any): ReactElement {
          const match = /language-(\w+)/.exec(className || '');
          const codeKey = `codeblock-${msgKey}-${node.position?.start.line ?? 0}`;
          const codeStr = String(children).replace(/^\n+|\n+$/g, '');
          const lines = codeStr.split('\n');
          const isFolded = foldedMap[codeKey] !== false && lines.length > 5;
          const displayCode = isFolded ? lines.slice(0, 5).join('\n') + '\n...' : codeStr;
          if (inline) {
            return <code className={className} {...props}>{children}</code>;
          }
          return (
            <div style={{ position: 'relative', margin: '8px 0' }}>
              <SyntaxHighlighter
                language={match ? match[1] : 'python'}
                style={vscDarkPlus}
                customStyle={{ borderRadius: 6, fontSize: '0.98em', margin: 0 }}
              >
                {displayCode}
              </SyntaxHighlighter>
              {lines.length > 5 && (
                <button
                  style={{
                    position: 'absolute',
                    right: 12,
                    bottom: 8,
                    fontSize: '0.9em',
                    background: '#222',
                    color: '#fff',
                    border: 'none',
                    borderRadius: 4,
                    padding: '2px 8px',
                    cursor: 'pointer',
                    opacity: 0.8,
                  }}
                  onClick={() => setFoldedMap(prev => ({ ...prev, [codeKey]: !isFolded }))}
                >
                  {isFolded ? '展开全部' : '收起'}
                </button>
              )}
            </div>
          );
        },
      }}
    >
      {content}
    </ReactMarkdown>
  );
}

function App() {
  const [isLoggedIn, setIsLoggedIn] = useState<boolean>(false);
  const [showLogin, setShowLogin] = useState<boolean>(true);
  const [loginLoading, setLoginLoading] = useState<boolean>(false);
  const [loginError, setLoginError] = useState<string>('');
  const [currentUsername, setCurrentUsername] = useState<string>('');
  const [loginToken, setLoginToken] = useState<string>('');
  const [loginExpiryTime, setLoginExpiryTime] = useState<number>(0);

  // 检查登录状态持久化
  useEffect(() => {
    const savedLogin = localStorage.getItem('logcoder_login');
    if (savedLogin) {
      try {
        const loginData = JSON.parse(savedLogin);
        const now = Date.now();
        const oneDay = 24 * 60 * 60 * 1000; // 1天的毫秒数
        
        // 检查是否在1天内
        if (loginData.timestamp && (now - loginData.timestamp) < oneDay) {
          setIsLoggedIn(true);
          setShowLogin(false);
          setCurrentUsername(loginData.username || '');
          setLoginToken(loginData.token || '');
          setLoginExpiryTime(loginData.timestamp + oneDay);
          setStatusMessage('欢迎回来！');
        } else {
          // 超过1天，清除过期数据
          localStorage.removeItem('logcoder_login');
        }
      } catch (error) {
        console.error('解析登录数据失败:', error);
        localStorage.removeItem('logcoder_login');
      }
    }
  }, []);

  // 清除过期登录状态的工具函数
  const clearExpiredLogin = () => {
    const savedLogin = localStorage.getItem('logcoder_login');
    if (savedLogin) {
      try {
        const loginData = JSON.parse(savedLogin);
        const now = Date.now();
        const oneDay = 24 * 60 * 60 * 1000;
        
        if (loginData.timestamp && (now - loginData.timestamp) >= oneDay) {
          localStorage.removeItem('logcoder_login');
          console.log('已清除过期的登录状态');
        }
      } catch (error) {
        localStorage.removeItem('logcoder_login');
      }
    }
  };

  // 组件初始化时清除过期登录状态
  useEffect(() => {
    clearExpiredLogin();
  }, []);

  const [code, setCode] = useState<string>('');
  const [messages, setMessages] = useState<{role: 'user'|'ai', content: string}[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [dirs, setDirs] = useState<any[]>([]);
  const [expandedDirs, setExpandedDirs] = useState<string[]>([]);
  const [activeFile, setActiveFile] = useState<{dir: string, file: string}|null>(null);
  const [execLoading, setExecLoading] = useState<string | null>(null); // 'file' | 'dir' | 'all' | null
  const [fileLoading, setFileLoading] = useState(false);
  const [saveLoading, setSaveLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState<Array<{name: string, relativePath: string, content: string}>>([]);
  const [lastSavedCode, setLastSavedCode] = useState<string>('');
  const [showUnsavedModal, setShowUnsavedModal] = useState<null | {dir: string, file: string}>(null);
  const [editDirModal, setEditDirModal] = useState<null | {oldName: string, newName: string}>(null);
  const [deleteDirPending, setDeleteDirPending] = useState<string | null>(null);
  const [foldedMap, setFoldedMap] = useState<{ [key: string]: boolean }>({});
  const [uploadedJsonName, setUploadedJsonName] = useState<string | null>(null);
  const [uploadedJsonContent, setUploadedJsonContent] = useState<string | null>(null);
  const [uploadedJsonlName, setUploadedJsonlName] = useState<string | null>(null);
  const [uploadedJsonlUploading, setUploadedJsonlUploading] = useState<boolean>(false);
  const chatEndRef = React.useRef<HTMLDivElement | null>(null);
  const [contextMenu, setContextMenu] = useState<null | { x: number, y: number, dir: string }>(null);
  const [fileContextMenu, setFileContextMenu] = useState<null | { x: number, y: number, dir: string, file: string }>(null);
  const [editFileModal, setEditFileModal] = useState<null | { dir: string, oldName: string, newName: string }>(null);
  const [deleteFilePending, setDeleteFilePending] = useState<null | { dir: string, file: string }>(null);
  const [statusMessage, setStatusMessage] = useState<string>('');
  const [treeContextMenu, setTreeContextMenu] = useState<{ x: number, y: number } | null>(null);
  const [createDirModal, setCreateDirModal] = useState<boolean>(false);
  const [createDirName, setCreateDirName] = useState<string>('');
  const [createDirError, setCreateDirError] = useState<string>('');
  const [createFileModal, setCreateFileModal] = useState<{ dirName: string, fileName: string } | null>(null);
  const [createFileError, setCreateFileError] = useState<string>('');
  const [saveFileModal, setSaveFileModal] = useState<{ dirName: string, fileName: string } | null>(null);
  const [saveFileError, setSaveFileError] = useState<string>('');
  const [errorModal, setErrorModal] = useState<{ title: string, message: string } | null>(null);

  // 检查是否为游客用户
  const isGuestUser = () => utils.isGuestUser(currentUsername);

  // 登录处理函数
  const handleLogin = async (username: string, password: string) => {
    setLoginLoading(true);
    setLoginError('');
    
    try {
      const result = await loginUser(username, password);
      if (result.success) {
        setIsLoggedIn(true);
        setShowLogin(false);
        setCurrentUsername(username);
        setLoginToken(result.token || '');
        setStatusMessage('登录成功！');
        // 保存登录状态到localStorage
        const loginData = {
          username: username,
          token: result.token || '',
          timestamp: Date.now(),
        };
        localStorage.setItem('logcoder_login', JSON.stringify(loginData));
        setLoginExpiryTime(Date.now() + CONSTANTS.LOGIN_EXPIRY_HOURS * 60 * 60 * 1000);
      } else {
        setLoginError(result.message || '登录失败');
      }
    } catch (error) {
      setLoginError('登录请求失败');
    } finally {
      setLoginLoading(false);
    }
  };

  // 登出处理函数
  const handleLogout = () => {
    setIsLoggedIn(false);
    setShowLogin(true);
    setCurrentUsername('');
    setLoginToken('');
    setLoginExpiryTime(0);
    setStatusMessage('已登出');
    // 清除localStorage中的登录数据
    localStorage.removeItem('logcoder_login');
  };

  useEffect(() => {
    fetchPythonDirs().then(dlist => {
      setDirs(dlist);
      if (dlist.length > 0 && dlist[0].files.length > 0) {
        setExpandedDirs([dlist[0].name]);
        setActiveFile({ dir: dlist[0].name, file: dlist[0].files[0].name });
        setFileLoading(true);
        fetchFileContent(dlist[0].name, dlist[0].files[0].name).then(content => {
          setCode(content);
          setLastSavedCode(content);
          setFileLoading(false);
        });
      } else if (dlist.length > 0) {
        setExpandedDirs([dlist[0].name]);
      }
    }).catch(error => {
      console.error('Failed to fetch directories on initialization:', error);
      setStatusMessage('无法获取目录列表，请检查后端服务是否正常运行');
      // 设置空的目录列表，避免界面错误
      setDirs([]);
    });
  }, []);

  useEffect(() => {
    if (chatEndRef.current) {
      chatEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 's') {
        e.preventDefault();
        handleSave();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [activeFile, code, saveLoading]);

  const handleDirClick = (dirName: string) => {
    setExpandedDirs(expandedDirs => {
      if (expandedDirs.includes(dirName)) {
        // 如果要收起当前目录，自动展开下一个或第一个
        const idx = dirs.findIndex(d => d.name === dirName);
        const nextIdx = (idx + 1 < dirs.length) ? idx + 1 : (dirs.length > 1 ? 0 : -1);
        if (nextIdx !== -1) {
          return [dirs[nextIdx].name];
        } else {
          return [dirName]; // 只有一个目录时不能收起
        }
      } else {
        return [dirName];
      }
    });
    
    // 展开目录时自动加载第一个文件
    const dir = dirs.find(d => d.name === dirName);
    if (dir) {
      if (dir.files.length > 0) {
        // 有文件时加载第一个文件
        const firstFile = dir.files[0];
        setActiveFile({ dir: dirName, file: firstFile.name });
        setFileLoading(true);
        fetchFileContent(dirName, firstFile.name).then(content => {
          setCode(content);
          setLastSavedCode(content);
          setFileLoading(false);
        });
      } else {
        // 没有文件时清空编辑器
        setActiveFile(null);
        setCode('');
        setLastSavedCode('');
      }
    }
  };

  const handleFileClick = (dirName: string, fileName: string) => {
    setActiveFile({ dir: dirName, file: fileName });
    setFileLoading(true);
    fetchFileContent(dirName, fileName).then(content => {
      setCode(content);
      setLastSavedCode(content);
      setFileLoading(false);
    });
  };

  // 切换文件前检测未保存
  const trySwitchFile = (dirName: string, fileName: string) => {
    // 首次加载时允许直接切换
    if (lastSavedCode === '' && code !== '') {
      setLastSavedCode(code);
      handleFileClick(dirName, fileName);
      return;
    }
    if (code !== lastSavedCode) {
      setShowUnsavedModal({ dir: dirName, file: fileName });
      return;
    }
    handleFileClick(dirName, fileName);
  };

  // 取消修改并切换
  const discardAndSwitch = () => {
    if (showUnsavedModal) {
      handleFileClick(showUnsavedModal.dir, showUnsavedModal.file);
      setShowUnsavedModal(null);
    }
  };

  // 保存修改并切换
  const saveAndSwitch = async () => {
    if (!activeFile || !showUnsavedModal) return;
    setSaveLoading(true);
    await saveFileContent(activeFile.dir, activeFile.file, code);
    setSaveLoading(false);
    setLastSavedCode(code);
    handleFileClick(showUnsavedModal.dir, showUnsavedModal.file);
    setShowUnsavedModal(null);
  };

  // 替换handleSend
  const handleSend = async () => {
    if (!input.trim()) return;
    const newMessages: {role: 'user'|'ai', content: string}[] = [...messages, { role: 'user', content: input }];
    setMessages(newMessages);
    setLoading(true);
    try {
      const currentDir = expandedDirs.length > 0 ? expandedDirs[0] : null;
      const result = await aiChat(input, activeFile ? `${activeFile.dir}/${activeFile.file}` : null, code, currentDir, newMessages);
      if (result && result.success) {
        setMessages(msgs => [...msgs, { role: 'ai', content: result.explanation }]);
        if (result.code) {
          setCode(result.code);
          setLastSavedCode(result.code);
        }
        // 检查AI回复是否包含代码块且有日志上传，自动执行当前文件
        const hasCodeBlock = /```[\s\S]*?```/.test(result.explanation || '');
        if (hasCodeBlock && uploadedFiles.length > 0 && activeFile) {
          // 自动执行当前文件
          const payload = { type: 'file', dir: activeFile.dir, file: activeFile.file, content: result.code || code, uploadedFiles: uploadedFiles.map(f => ({ relativePath: f.relativePath, content: f.content })), currentDir };
          const execResult = await apiCall.post('/execute', payload);
          const output = (execResult.result === null || execResult.result === undefined || execResult.result === '' || execResult.result === 'None') ? '无输出' : execResult.result;
          setMessages(msgs => [
            ...msgs,
            {
              role: 'ai',
              content: `# 执行结果\n${output}`,
            },
          ]);
        }
      } else {
        setMessages(msgs => [...msgs, { role: 'ai', content: result.explanation || 'AI生成失败' }]);
      }
    } catch (error) {
      setMessages(msgs => [...msgs, { role: 'ai', content: `AI请求失败: ${error}` }]);
    }
    setLoading(false);
    setInput('');
  };

  // 替换execute函数
  const execute = async (type: 'file' | 'dir' | 'all') => {
    setExecLoading(type);
    let payload: any = undefined;
    const uploadedFilePayload = uploadedFiles.map(f => ({ relativePath: f.relativePath, content: f.content }));
    let currentDir = expandedDirs.length > 0 ? expandedDirs[0] : null;
    if (type === 'file') {
      if (activeFile) {
        payload = { type: 'file', dir: activeFile.dir, file: activeFile.file, content: code, uploadedFiles: uploadedFilePayload, currentDir: currentDir };
        const result = await apiCall.post('/execute', payload);
        setStatusMessage(result?.message || '');
        if (result && result.success) {
          const output = (result.result === null || result.result === undefined || result.result === '' || result.result === 'None') ? '无输出' : result.result;
          setMessages(msgs => [
            ...msgs,
            {
              role: 'ai',
              content: `# 执行结果\n${output}`,
            },
          ]);
        } else {
          // 显示错误提示框
          setErrorModal({
            title: '执行失败',
            message: result?.message || '执行过程中发生未知错误'
          });
        }
      } else {
        // 没有选中文件时，弹窗输入文件名，保存到当前展开目录并自动执行
        if (!currentDir) {
          setExecLoading(null);
          setStatusMessage('请先展开一个目录');
          return;
        }
        // 显示保存文件弹窗
        setSaveFileModal({ dirName: currentDir, fileName: '' });
        setSaveFileError('');
        setExecLoading(null);
      }
    } else if (type === 'dir') {
      const currentDir = expandedDirs.length > 0 ? expandedDirs[0] : null;
      if (!currentDir) {
        setExecLoading(null);
        return;
      }
      payload = { type: 'dir', dir: currentDir, uploadedFiles: uploadedFilePayload };
      const result = await apiCall.post('/execute', payload);
      setStatusMessage(result?.message || '');
      if (result && result.success) {
        const output = (result.result === null || result.result === undefined || result.result === '' || result.result === 'None') ? '无输出' : result.result;
        setMessages(msgs => [
          ...msgs,
          {
            role: 'ai',
            content: `# 执行结果\n${output}`,
          },
        ]);
      } else {
        // 显示错误提示框
        setErrorModal({
          title: '执行失败',
          message: result?.message || '执行过程中发生未知错误'
        });
      }
    } else if (type === 'all') {
      payload = { type: 'all', dirs: dirs.map(d => ({ name: d.name, files: d.files.map((f: any) => f.name) })), uploadedFiles: uploadedFilePayload };
      const result = await apiCall.post('/execute', payload);
      setStatusMessage(result?.message || '');
      if (result && result.success) {
        const output = (result.result === null || result.result === undefined || result.result === '' || result.result === 'None') ? '无输出' : result.result;
        setMessages(msgs => [
          ...msgs,
          {
            role: 'ai',
            content: `# 执行结果\n${output}`,
          },
        ]);
      } else {
        // 显示错误提示框
        setErrorModal({
          title: '执行失败',
          message: result?.message || '执行过程中发生未知错误'
        });
      }
    }
    setExecLoading(null);
  };

  // 右键菜单事件
  const handleDirContextMenu = (e: React.MouseEvent, dirName: string) => {
    e.preventDefault();
    e.stopPropagation();
    if (isGuestUser()) {
      setStatusMessage('游客用户无法进行文件操作');
      return;
    }
    // 关闭其他所有菜单
    closeFileContextMenu();
    closeTreeContextMenu();
    setExpandedDirs([dirName]);
    setContextMenu({ x: e.clientX, y: e.clientY, dir: dirName });
  };
  
  // 关闭右键菜单
  const closeContextMenu = () => setContextMenu(null);
  const closeTreeContextMenu = () => setTreeContextMenu(null);

  // 文件树空白区域右键菜单事件
  const handleTreeContextMenu = (e: React.MouseEvent) => {
    // 检查是否点击在目录或文件上，如果是则不处理
    const target = e.target as HTMLElement;
    if (target.closest('.dir-name') || target.closest('.file-tab')) {
      return;
    }
    
    e.preventDefault();
    e.stopPropagation();
    if (isGuestUser()) {
      setStatusMessage('游客用户无法进行文件操作');
      return;
    }
    // 关闭其他所有菜单
    closeContextMenu();
    closeFileContextMenu();
    setTreeContextMenu({ x: e.clientX, y: e.clientY });
  };

  // 创建目录菜单项处理
  const handleCreateDirectory = () => {
    closeTreeContextMenu();
    handleAddDir();
  };

  // 右键菜单操作
  const handleContextRename = () => {
    if (contextMenu) {
      setEditDirModal({ oldName: contextMenu.dir, newName: contextMenu.dir });
      closeContextMenu();
    }
  };
  const handleContextDelete = () => {
    if (contextMenu) {
      setDeleteDirPending(contextMenu.dir);
      closeContextMenu();
    }
  };
  const handleContextUploadJsonl = () => {
    if (contextMenu) {
      // 触发隐藏的input
      const input = document.getElementById(`jsonl-upload-input-${contextMenu.dir}`) as HTMLInputElement;
      if (input) input.click();
      closeContextMenu();
    }
  };
  const handleContextCreateFile = () => {
    if (contextMenu) {
      // 展开目录
      setExpandedDirs([contextMenu.dir]);
      // 创建新文件
      handleAddFileInDir(contextMenu.dir);
      closeContextMenu();
    }
  };

  // 在指定目录下创建新文件
  const handleAddFileInDir = async (dirName: string) => {
    setCreateFileModal({ dirName, fileName: '' });
    setCreateFileError('');
  };

  // 文件右键菜单事件
  const handleFileContextMenu = (e: React.MouseEvent, dirName: string, fileName: string) => {
    e.preventDefault();
    e.stopPropagation();
    if (isGuestUser()) {
      setStatusMessage('游客用户无法进行文件操作');
      return;
    }
    // 关闭其他所有菜单
    closeContextMenu();
    closeTreeContextMenu();
    setFileContextMenu({ x: e.clientX, y: e.clientY, dir: dirName, file: fileName });
  };
  const closeFileContextMenu = () => setFileContextMenu(null);

  // 文件右键菜单操作
  const handleFileContextRename = () => {
    if (fileContextMenu) {
      setEditFileModal({ dir: fileContextMenu.dir, oldName: fileContextMenu.file, newName: fileContextMenu.file });
      closeFileContextMenu();
    }
  };
  const handleFileContextDelete = () => {
    if (fileContextMenu) {
      setDeleteFilePending({ dir: fileContextMenu.dir, file: fileContextMenu.file });
      closeFileContextMenu();
    }
  };

  // 文件重命名API
  const renameFile = async (dir: string, oldName: string, newName: string) => {
    try {
      const result = await apiCall.post(`/file/${encodeURIComponent(dir)}/${encodeURIComponent(oldName)}/rename`, { newName });
      if (result.success) {
        const updatedDirs = await fetchPythonDirs();
        setDirs(updatedDirs);
        alert('文件重命名成功！');
      } else {
        alert('重命名失败: ' + (result.message || '未知错误'));
      }
    } catch (err) {
      alert('重命名失败: ' + err);
    }
  };
  // 文件删除API
  const deleteFile = async (dir: string, file: string) => {
    try {
      const result = await apiCall.delete(`/file/${encodeURIComponent(dir)}/${encodeURIComponent(file)}`);
      if (result.success) {
        // 强制重新获取目录结构，确保界面更新
        try {
          const updatedDirs = await fetchPythonDirs();
          setDirs(updatedDirs);
          
          // 检查当前激活的文件是否就是被删除的文件
          if (activeFile && activeFile.dir === dir && activeFile.file === file) {
            // 如果删除的是当前激活的文件，取消激活并清空编辑器
            setActiveFile(null);
            setCode('');
            setLastSavedCode('');
          }
          
          // 检查删除后目录是否还有文件
          const updatedDir = updatedDirs.find((d: any) => d.name === dir);
          if (updatedDir && updatedDir.files.length === 0) {
            // 如果目录为空，清空编辑器并取消激活文件
            setActiveFile(null);
            setCode('');
            setLastSavedCode('');
          }
          
          setStatusMessage('文件删除成功！');
        } catch (fetchError) {
          console.error('Failed to refresh directories after delete:', fetchError);
          setStatusMessage('文件删除成功，但界面更新失败');
        }
      } else {
        setStatusMessage('删除失败: ' + (result.message || '未知错误'));
      }
    } catch (err) {
      setStatusMessage('删除失败: ' + err);
    }
  };

  // 保存文件
  const handleSave = async () => {
    if (!activeFile) return;
    if (isGuestUser()) {
      setStatusMessage('游客用户无法保存文件');
      return;
    }
    setSaveLoading(true);
    await saveFileContent(activeFile.dir, activeFile.file, code);
    setSaveLoading(false);
    setLastSavedCode(code);
  };

  // 检查文件是否重复
  const isFileDuplicate = (fileName: string, content: string): { isDuplicate: boolean; reason: string } => {
    const existingFile = uploadedFiles.find(file => {
      // 检查文件名是否相同
      if (file.name === fileName) {
        return true;
      }
      
      // 检查文件内容是否相同
      if (file.content === content) {
        return true;
      }
      
      return false;
    });

    if (!existingFile) {
      return { isDuplicate: false, reason: '' };
    }

    if (existingFile.name === fileName) {
      return { isDuplicate: true, reason: '文件名重复' };
    } else {
      return { isDuplicate: true, reason: '文件内容重复' };
    }
  };

  // 上传文件处理
  const handleFileInput = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || e.target.files.length === 0) return;
    const file = e.target.files[0];
    
    // 检查文件类型：允许 .txt, .log, text/* 和没有后缀的文件
    const fileName = file.name.toLowerCase();
    const hasValidExtension = fileName.endsWith('.txt') || fileName.endsWith('.log');
    const hasNoExtension = !fileName.includes('.');
    const isTextFile = file.type.startsWith('text/');
    
    if (!hasValidExtension && !hasNoExtension && !isTextFile) {
      alert('只支持上传 .txt、.log 文件或没有后缀的文本文件');
      e.target.value = '';
      return;
    }
    
    setUploading(true);
    const content = await new Promise<string>((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => resolve(reader.result as string);
      reader.onerror = reject;
      reader.readAsText(file);
    });
    setUploading(false);

    // 检查重复文件
    const duplicateResult = isFileDuplicate(file.name, content);
    if (duplicateResult.isDuplicate) {
      alert(`该文件已上传过，原因是：${duplicateResult.reason}`);
      e.target.value = '';
      return;
    }

    setUploadedFiles(files => ([...files, { name: file.name, relativePath: file.name, content }]));
    await uploadFile(file);
    e.target.value = '';
  };

  const handleDrop = async (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    if (!e.dataTransfer.files || e.dataTransfer.files.length === 0) return;
    const file = e.dataTransfer.files[0];
    if (!file) return;
    
    // 检查文件类型：允许 .txt, .log, text/* 和没有后缀的文件
    const fileName = file.name.toLowerCase();
    const hasValidExtension = fileName.endsWith('.txt') || fileName.endsWith('.log');
    const hasNoExtension = !fileName.includes('.');
    const isTextFile = file.type.startsWith('text/');
    
    if (!hasValidExtension && !hasNoExtension && !isTextFile) {
      alert('只支持上传 .txt、.log 文件或没有后缀的文本文件');
      return;
    }
    
    setUploading(true);
    
    // 读取文件内容
    const content = await new Promise<string>((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => resolve(reader.result as string);
      reader.onerror = reject;
      reader.readAsText(file);
    });
    
    // 检查重复文件
    const duplicateResult = isFileDuplicate(file.name, content);
    if (duplicateResult.isDuplicate) {
      alert(`该文件已上传过，原因是：${duplicateResult.reason}`);
      setUploading(false);
      return;
    }

    await uploadFile(file);
    setUploadedFiles(files => ([...files, { name: file.name, relativePath: file.name, content }]));
    setUploading(false);
  };
  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
  };
  const handleDeleteUploaded = (name: string) => {
    setUploadedFiles(files => files.filter(f => f.name !== name));
  };

  const handleAddFile = async () => {
    if (expandedDirs.length === 0) {
      alert('请先展开一个目录再添加文件');
      return;
    }
    const dirName = expandedDirs[0]; // 只在第一个展开目录下添加
    let fileName = prompt('请输入新文件名（如 newfile.py）：');
    if (!fileName) return;
    fileName = fileName.trim();
    if (!fileName.endsWith('.py')) {
      alert('文件名必须以 .py 结尾');
      return;
    }
    // 检查是否已存在
    const dir = dirs.find(d => d.name === dirName);
    if (dir && utils.isFileExists(dirs, dirName, fileName)) {
      alert('该文件已存在');
      return;
    }
    
    // 调用API创建文件
    const success = await createFile(dirName, fileName);
    if (success) {
      // 重新获取目录结构
      const updatedDirs = await fetchPythonDirs();
      setDirs(updatedDirs);
      setActiveFile({ dir: dirName, file: fileName });
      setCode('');
    }
  };

  const handleEditDir = async (oldName: string) => {
    setEditDirModal({ oldName, newName: oldName });
  };

  const handleEditDirInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    setEditDirModal(modal => modal ? { ...modal, newName: e.target.value } : modal);
  };

  const handleEditDirCancel = () => setEditDirModal(null);

  const handleEditDirConfirm = async () => {
    if (!editDirModal) return;
    const { oldName, newName } = editDirModal;
    const trimmed = newName.trim();
    if (!trimmed || trimmed === oldName) return setEditDirModal(null);
    if (utils.isDirExists(dirs, trimmed)) {
      alert('该目录名已存在');
      return;
    }
    
    const success = await saveDirName(oldName, trimmed);
    if (success) {
      // 重新获取目录结构
      const updatedDirs = await fetchPythonDirs();
      setDirs(updatedDirs);
      setExpandedDirs(expandedDirs => expandedDirs.map(n => n === oldName ? trimmed : n).filter((n): n is string => !!n));
      setActiveFile(activeFile => {
        if (activeFile && activeFile.dir === oldName) {
          return { dir: trimmed, file: activeFile.file };
        }
        return activeFile;
      });
    }
    setEditDirModal(null);
  };

  const handleDeleteDir = async (dirName: string) => {
    setEditDirModal(null);
    setDeleteDirPending(dirName);
  };

  const handleDeleteDirConfirm = async () => {
    if (!deleteDirPending) return;
    
    const success = await deleteDir(deleteDirPending);
    if (success) {
      // 重新获取目录结构
      const updatedDirs = await fetchPythonDirs();
      setDirs(updatedDirs);
      setExpandedDirs(expandedDirs => expandedDirs.filter(n => n !== deleteDirPending));
      setActiveFile(activeFile => (activeFile && activeFile.dir === deleteDirPending) ? null : activeFile);
    }
    setDeleteDirPending(null);
  };

  const handleDeleteDirCancel = () => setDeleteDirPending(null);

  // 添加目录
  const handleAddDir = async () => {
    setCreateDirModal(true);
  };

  const handleCreateDirConfirm = async () => {
    if (!createDirName.trim()) {
      setCreateDirError('请输入目录名称');
      return;
    }
    
    const dirName = createDirName.trim();
    // 检查是否已存在
    if (utils.isDirExists(dirs, dirName)) {
      setCreateDirError('该目录已存在');
      return;
    }
    
    // 调用API创建目录
    const success = await createDirectory(dirName);
    if (success) {
      // 重新获取目录结构
      const updatedDirs = await fetchPythonDirs();
      setDirs(updatedDirs);
      setCreateDirModal(false);
      setCreateDirName('');
      setCreateDirError('');
    }
  };

  const handleCreateDirCancel = () => {
    setCreateDirModal(false);
    setCreateDirName('');
    setCreateDirError('');
  };

  const handleCreateFileCancel = () => {
    setCreateFileModal(null);
    setCreateFileError('');
  };

  const handleSaveFileConfirm = async () => {
    if (!saveFileModal) return;
    const { dirName, fileName } = saveFileModal;
    if (!fileName.trim()) {
      setSaveFileError('文件名不能为空');
      return;
    }
    // 自动添加 .py 后缀（如果没有的话）
    let finalFileName = fileName.trim();
    if (!finalFileName.endsWith('.py')) {
      finalFileName += '.py';
    }
    if (utils.isFileExists(dirs, dirName, finalFileName)) {
      setSaveFileError('该文件已存在');
      return;
    }
    // 保存文件
    setSaveLoading(true);
    await saveFileContent(dirName, finalFileName, code);
    setSaveLoading(false);
    // 刷新目录树并激活新文件
    const updatedDirs = await fetchPythonDirs();
    setDirs(updatedDirs);
    setActiveFile({ dir: dirName, file: finalFileName });
    setLastSavedCode(code);
    // 自动执行新文件
    const uploadedFilePayload = uploadedFiles.map(f => ({ relativePath: f.relativePath, content: f.content }));
    const payload = { type: 'file', dir: dirName, file: finalFileName, content: code, uploadedFiles: uploadedFilePayload, currentDir: dirName };
    const result = await apiCall.post('/execute', payload);
    setStatusMessage(result?.message || '');
    if (result && result.success) {
      setMessages(msgs => [
        ...msgs,
        {
          role: 'ai',
          content: `# 执行结果\n${result.result || ''}`,
        },
      ]);
    } else {
      // 显示错误提示框
      setErrorModal({
        title: '执行失败',
        message: result?.message || '执行过程中发生未知错误'
      });
    }
    setSaveFileModal(null);
    setSaveFileError('');
  };

  const handleSaveFileCancel = () => {
    setSaveFileModal(null);
    setSaveFileError('');
  };

  return (
    <div className="split-container" onClick={() => { 
      closeContextMenu(); 
      closeFileContextMenu(); 
      closeTreeContextMenu(); 
    }}>
      <div className="left-panel">
        {!isLoggedIn ? (
          <div className="login-section">
            <h2>登录</h2>
            <LoginForm onLogin={handleLogin} loading={loginLoading} error={loginError} />
          </div>
        ) : (
          <>
            <div className="user-info">
              <div className="user-info-left">
                <span className="welcome-text">欢迎，{currentUsername}！</span>
                {loginExpiryTime > 0 && (
                  <span className="login-expiry">
                    有效期：{Math.max(0, Math.floor((loginExpiryTime - Date.now()) / (1000 * 60 * 60)))}小时
                  </span>
                )}
              </div>
              <button className="logout-btn-small" onClick={handleLogout}>登出</button>
            </div>
            <div
              className={uploading ? 'upload-area uploading' : 'upload-area'}
              onDrop={handleDrop}
              onDragOver={handleDragOver}
            >
              <input
                type="file"
                style={{ display: 'none' }}
                id="file-upload-input"
                onChange={handleFileInput}
                disabled={uploading}
              />
              <label htmlFor="file-upload-input" className="upload-label">
                {uploading ? '上传中...' : '选择或拖拽日志上传'}
              </label>
            </div>
            {uploadedFiles.length > 0 && (
              <div className="uploaded-list">
                {uploadedFiles.map(f => (
                  <div className="uploaded-item" key={f.name}>
                    <span className="upload-icon">📄</span> {f.name}
                    <span className="delete-upload" onClick={() => handleDeleteUploaded(f.name)}>✖</span>
                  </div>
                ))}
              </div>
            )}
            <div className="file-tree" onContextMenu={handleTreeContextMenu}>
              {dirs.map(dir => (
                <div key={dir.name} className="dir-group">
                  <div
                    className={expandedDirs.includes(dir.name) ? 'dir-name expanded' : 'dir-name'}
                    onClick={() => handleDirClick(dir.name)}
                    onContextMenu={e => handleDirContextMenu(e, dir.name)}
                  >
                    <span>{expandedDirs.includes(dir.name) ? '▼' : '▶'}</span> {dir.name}
                    <input
                      id={`jsonl-upload-input-${dir.name}`}
                      type="file"
                      accept=".jsonl,application/jsonl"
                      style={{ display: 'none' }}
                      onChange={e => {
                        const file = e.target.files?.[0];
                        if (!file) return;
                        if (!file.name.endsWith('.jsonl')) {
                          alert('只支持上传 .jsonl 文件');
                          return;
                        }
                        const reader = new FileReader();
                        reader.onload = async (evt) => {
                          const content = evt.target?.result as string;
                          try {
                            const formData = new FormData();
                            formData.append('jsonl_content', content);
                            const resp = await fetch(`${API_BASE_URL}/dir/${encodeURIComponent(dir.name)}/upload_jsonl`, {
                              method: 'POST',
                              body: formData,
                            });
                            const result = await resp.json();
                            if (result.success) {
                              alert('JSONL文件上传并保存成功！');
                            } else {
                              alert('上传失败: ' + (result.message || '未知错误'));
                            }
                          } catch (err) {
                            alert('上传失败: ' + err);
                          }
                        };
                        reader.readAsText(file);
                      }}
                    />
                    {/* 右键菜单 */}
                    {contextMenu && contextMenu.dir === dir.name && !fileContextMenu && !treeContextMenu && (
                      <div
                        className="context-menu"
                        style={{ position: 'fixed', top: contextMenu.y, left: contextMenu.x, zIndex: 2000 }}
                        onClick={e => e.stopPropagation()}
                      >
                        <div className="context-menu-item" onClick={handleContextUploadJsonl}>上传日志格式</div>
                        <div className="context-menu-item" onClick={handleContextCreateFile}>新建文件</div>
                        <div className="context-menu-item" onClick={handleContextRename}>重命名</div>
                        <div className="context-menu-item context-menu-danger" onClick={handleContextDelete}>删除目录</div>
                      </div>
                    )}
                  </div>
                  {expandedDirs.includes(dir.name) && (
                    <div className="file-list">
                      {dir.files.map((file: any) => (
                        <button
                          key={file.name}
                          className={activeFile && activeFile.dir === dir.name && activeFile.file === file.name ? 'file-tab active' : 'file-tab'}
                          onClick={() => trySwitchFile(dir.name, file.name)}
                          onContextMenu={e => handleFileContextMenu(e, dir.name, file.name)}
                        >
                          {file.name}
                        </button>
                      ))}
                      {/* 文件右键菜单 */}
                      {fileContextMenu && fileContextMenu.dir === dir.name && utils.isFileExists(dirs, dir.name, fileContextMenu.file) && !contextMenu && !treeContextMenu && (
                        <div
                          className="context-menu"
                          style={{ position: 'fixed', top: fileContextMenu.y, left: fileContextMenu.x, zIndex: 2000 }}
                          onClick={e => e.stopPropagation()}
                        >
                          <div className="context-menu-item" onClick={handleFileContextRename}>重命名</div>
                          <div className="context-menu-item context-menu-danger" onClick={handleFileContextDelete}>删除文件</div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ))}
              {/* 文件树空白区域右键菜单 */}
              {treeContextMenu && !contextMenu && !fileContextMenu && (
                <div
                  className="context-menu"
                  style={{ position: 'fixed', top: treeContextMenu.y, left: treeContextMenu.x, zIndex: 2000 }}
                  onClick={e => e.stopPropagation()}
                >
                  <div className="context-menu-item" onClick={handleCreateDirectory}>增加目录</div>
                </div>
              )}
            </div>
          </>
        )}
      </div>
      <div className="middle-panel">
        <h2>代码编辑器</h2>
        <div className="codemirror-wrapper">
          <CodeEditor code={code} setCode={setCode} />
          {fileLoading && <div className="file-loading-mask">文件加载中...</div>}
        </div>
        <div className="exec-btn-group">
          <button
            onClick={() => execute('file')}
            disabled={!!execLoading}
          >
            {execLoading === 'file' ? '执行中...' : '执行当前文件'}
          </button>
          <button
            onClick={() => execute('dir')}
            disabled={!activeFile || !!execLoading}
          >
            {execLoading === 'dir' ? '执行中...' : '执行当前目录'}
          </button>
          <button
            onClick={() => execute('all')}
            disabled={!!execLoading}
          >
            {execLoading === 'all' ? '执行中...' : '执行全部目录'}
          </button>
          <button
            className="save-btn"
            onClick={handleSave}
            disabled={!activeFile || saveLoading || isGuestUser()}
            style={{ minWidth: 90, marginLeft: 12 }}
            title={isGuestUser() ? '游客用户无法保存文件' : ''}
          >
            {saveLoading ? '保存中...' : '保存文件'}
          </button>
        </div>
      </div>
      <div className="right-panel">
        <h2>AI 对话</h2>
        <div className="chat-tip">
          💡 AI回复解释显示在对话框中，代码自动写入编辑器。执行结果也会显示在对话中。
        </div>
        <div className="chat-box">
          {messages.map((msg, idx) => (
            <div key={idx} className={msg.role === 'user' ? 'msg-user' : 'msg-ai'}>
              <span className="msg-avatar">{msg.role === 'user' ? '你' : <span style={{fontWeight:'bold'}}>🤖</span>}</span>
              <div>
                {/* <span className="msg-nick">{msg.role === 'user' ? '你' : 'AI'}：</span> */}
                <AIMessage content={msg.content} foldedMap={foldedMap} setFoldedMap={setFoldedMap} msgKey={String(idx)} />
              </div>
            </div>
          ))}
          {loading && <div className="msg-ai"><span className="msg-avatar"><span style={{fontWeight:'bold'}}>🤖</span></span><div>AI 正在思考...</div></div>}
          <div ref={chatEndRef} />
        </div>
        <div className="chat-input-row">
          <textarea
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSend();
              }
            }}
            placeholder="输入你的问题..."
            disabled={loading}
            rows={2}
            className="chat-textarea"
          />
          <button onClick={handleSend} disabled={loading || !input.trim()}>发送</button>
          <button onClick={() => setMessages([])} disabled={loading} style={{marginLeft: 8}}>清除对话</button>
        </div>
      </div>
      {/* 未保存更改提示弹窗 */}
      {showUnsavedModal && (
        <div className="unsaved-modal-mask">
          <div className="unsaved-modal">
            <div className="unsaved-modal-title">有未保存的更改</div>
            <div className="unsaved-modal-desc">是否保存当前更改？</div>
            <div className="unsaved-modal-btns">
              <button onClick={discardAndSwitch} disabled={saveLoading}>取消修改</button>
              <button onClick={saveAndSwitch} disabled={saveLoading}>{saveLoading ? '保存中...' : '保存修改'}</button>
            </div>
          </div>
        </div>
      )}
      {/* 目录名编辑弹窗（只保留重命名） */}
      {editDirModal && (
        <div className="unsaved-modal-mask">
          <div className="unsaved-modal">
            <div className="unsaved-modal-title">修改目录名称</div>
            <input
              className="edit-dir-input"
              value={editDirModal.newName}
              onChange={handleEditDirInput}
              onKeyDown={e => {
                if (e.key === 'Enter') {
                  e.preventDefault();
                  handleEditDirConfirm();
                } else if (e.key === 'Escape') {
                  e.preventDefault();
                  handleEditDirCancel();
                }
              }}
              autoFocus
              maxLength={32}
            />
            <div className="unsaved-modal-btns">
              <button onClick={handleEditDirCancel}>取消</button>
              <button onClick={handleEditDirConfirm}>确定</button>
            </div>
          </div>
        </div>
      )}
      {/* 删除目录确认弹窗 */}
      {deleteDirPending && (
        <div className="unsaved-modal-mask">
          <div className="unsaved-modal">
            <div className="unsaved-modal-title">确认删除目录</div>
            <div className="unsaved-modal-desc">确定要删除目录"{deleteDirPending}"及其下所有文件吗？</div>
            <div className="unsaved-modal-btns">
              <button onClick={handleDeleteDirCancel}>取消</button>
              <button className="delete-dir-btn-modal" onClick={handleDeleteDirConfirm}>删除</button>
            </div>
          </div>
        </div>
      )}
      {/* 文件重命名弹窗 */}
      {editFileModal && (
        <div className="unsaved-modal-mask">
          <div className="unsaved-modal">
            <div className="unsaved-modal-title">重命名文件</div>
            <input
              className="edit-dir-input"
              value={editFileModal.newName}
              onChange={e => setEditFileModal(modal => modal ? { ...modal, newName: e.target.value } : modal)}
              onKeyDown={e => {
                if (e.key === 'Enter') {
                  e.preventDefault();
                  // 触发文件重命名确认逻辑
                  if (editFileModal) {
                    const { dir, oldName, newName } = editFileModal;
                    if (!newName.trim() || newName === oldName) {
                      setEditFileModal(null);
                      return;
                    }
                    renameFile(dir, oldName, newName.trim()).then(() => {
                      setEditFileModal(null);
                    });
                  }
                } else if (e.key === 'Escape') {
                  e.preventDefault();
                  setEditFileModal(null);
                }
              }}
              autoFocus
              maxLength={64}
            />
            <div className="unsaved-modal-btns">
              <button onClick={() => setEditFileModal(null)}>取消</button>
              <button onClick={async () => {
                if (!editFileModal) return;
                const { dir, oldName, newName } = editFileModal;
                if (!newName.trim() || newName === oldName) {
                  setEditFileModal(null);
                  return;
                }
                await renameFile(dir, oldName, newName.trim());
                setEditFileModal(null);
              }}>确定</button>
            </div>
          </div>
        </div>
      )}
      {/* 文件删除确认弹窗 */}
      {deleteFilePending && (
        <div className="unsaved-modal-mask">
          <div className="unsaved-modal">
            <div className="unsaved-modal-title">确认删除文件</div>
            <div className="unsaved-modal-desc">确定要删除文件"{deleteFilePending.file}"吗？此操作不可撤销。</div>
            <div className="unsaved-modal-btns">
              <button onClick={() => setDeleteFilePending(null)}>取消</button>
              <button 
                className="delete-dir-btn-modal" 
                onClick={async () => {
                  if (!deleteFilePending) return;
                  await deleteFile(deleteFilePending.dir, deleteFilePending.file);
                  setDeleteFilePending(null);
                }}
              >
                删除
              </button>
            </div>
          </div>
        </div>
      )}
      {/* 创建目录弹窗 */}
      {createDirModal && (
        <div className="unsaved-modal-mask">
          <div className="unsaved-modal">
            <div className="unsaved-modal-title">创建新目录</div>
            <input
              className="edit-dir-input"
              value={createDirName}
              onChange={e => setCreateDirName(e.target.value)}
              onKeyDown={e => {
                if (e.key === 'Enter') {
                  e.preventDefault();
                  handleCreateDirConfirm();
                } else if (e.key === 'Escape') {
                  e.preventDefault();
                  handleCreateDirCancel();
                }
              }}
              placeholder="请输入目录名称"
              autoFocus
              maxLength={32}
            />
            {createDirError && <div className="unsaved-modal-error">{createDirError}</div>}
            <div className="unsaved-modal-btns">
              <button onClick={handleCreateDirCancel}>取消</button>
              <button onClick={handleCreateDirConfirm} disabled={!createDirName.trim() || createDirError !== ''}>确定</button>
            </div>
          </div>
        </div>
      )}
      {/* 创建文件弹窗 */}
      {createFileModal && (
        <div className="unsaved-modal-mask">
          <div className="unsaved-modal">
            <div className="unsaved-modal-title">创建新文件</div>
            <input
              className="edit-dir-input"
              value={createFileModal.fileName}
              onChange={e => setCreateFileModal(modal => modal ? { ...modal, fileName: e.target.value } : modal)}
              onKeyDown={e => {
                if (e.key === 'Enter') {
                  e.preventDefault();
                  // 触发创建文件的确认逻辑
                  if (createFileModal) {
                    const { dirName, fileName } = createFileModal;
                    if (!fileName.trim()) {
                      setCreateFileError('文件名不能为空');
                      return;
                    }
                    // 自动添加 .py 后缀（如果没有的话）
                    let finalFileName = fileName.trim();
                    if (!finalFileName.endsWith('.py')) {
                      finalFileName += '.py';
                    }
                    if (utils.isFileExists(dirs, dirName, finalFileName)) {
                      setCreateFileError('该文件已存在');
                      return;
                    }
                    createFile(dirName, finalFileName).then(success => {
                      if (success) {
                        fetchPythonDirs().then(updatedDirs => {
                          setDirs(updatedDirs);
                          setActiveFile({ dir: dirName, file: finalFileName });
                          setCode('');
                          setLastSavedCode('');
                          setCreateFileModal(null);
                          setCreateFileError('');
                        });
                      } else {
                        setCreateFileError('创建文件失败');
                      }
                    });
                  }
                } else if (e.key === 'Escape') {
                  e.preventDefault();
                  handleCreateFileCancel();
                }
              }}
              placeholder="请输入文件名（如 newfile 或 newfile.py）"
              autoFocus
              maxLength={64}
            />
            {createFileError && <div className="unsaved-modal-error">{createFileError}</div>}
            <div className="unsaved-modal-btns">
              <button onClick={handleCreateFileCancel}>取消</button>
              <button onClick={async () => {
                if (!createFileModal) return;
                const { dirName, fileName } = createFileModal;
                if (!fileName.trim()) {
                  setCreateFileError('文件名不能为空');
                  return;
                }
                // 自动添加 .py 后缀（如果没有的话）
                let finalFileName = fileName.trim();
                if (!finalFileName.endsWith('.py')) {
                  finalFileName += '.py';
                }
                if (utils.isFileExists(dirs, dirName, finalFileName)) {
                  setCreateFileError('该文件已存在');
                  return;
                }
                const success = await createFile(dirName, finalFileName);
                if (success) {
                  const updatedDirs = await fetchPythonDirs();
                  setDirs(updatedDirs);
                  setActiveFile({ dir: dirName, file: finalFileName });
                  setCode('');
                  setLastSavedCode('');
                  setCreateFileModal(null);
                  setCreateFileError('');
                } else {
                  setCreateFileError('创建文件失败');
                }
              }}>确定</button>
            </div>
          </div>
        </div>
      )}
      {/* 保存文件弹窗 */}
      {saveFileModal && (
        <div className="unsaved-modal-mask">
          <div className="unsaved-modal">
            <div className="unsaved-modal-title">保存文件</div>
            <input
              className="edit-dir-input"
              value={saveFileModal.fileName}
              onChange={e => setSaveFileModal(modal => modal ? { ...modal, fileName: e.target.value } : modal)}
              onKeyDown={e => {
                if (e.key === 'Enter') {
                  e.preventDefault();
                  handleSaveFileConfirm();
                } else if (e.key === 'Escape') {
                  e.preventDefault();
                  handleSaveFileCancel();
                }
              }}
              placeholder="请输入文件名（如 newfile 或 newfile.py）"
              autoFocus
              maxLength={64}
            />
            {saveFileError && <div className="unsaved-modal-error">{saveFileError}</div>}
            <div className="unsaved-modal-btns">
              <button onClick={handleSaveFileCancel}>取消</button>
              <button onClick={handleSaveFileConfirm} disabled={!saveFileModal.fileName.trim() || saveFileError !== ''}>确定</button>
            </div>
          </div>
        </div>
      )}
      {/* 错误提示框 */}
      {errorModal && (
        <div className="unsaved-modal-mask">
          <div className="unsaved-modal error-modal">
            <div className="unsaved-modal-title error-title">
              <span className="error-icon">⚠️</span>
              {errorModal.title}
            </div>
            <div className="error-message">
              {errorModal.message}
            </div>
            <div className="unsaved-modal-btns">
              <button 
                className="error-confirm-btn" 
                onClick={() => setErrorModal(null)}
                onKeyDown={e => {
                  if (e.key === 'Enter' || e.key === 'Escape') {
                    e.preventDefault();
                    setErrorModal(null);
                  }
                }}
                autoFocus
              >
                确定
              </button>
            </div>
          </div>
        </div>
      )}
      {/* 状态栏 */}
      <div className="status-bar">
        <span className="status-icon">💡</span>
        <span className="status-message">{statusMessage}</span>
      </div>
    </div>
  );
}

export default App;

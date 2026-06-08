import React, { useMemo, useState } from 'react';
import { createRoot } from 'react-dom/client';
import {
  Bot,
  CheckCircle2,
  Cpu,
  FileText,
  KeyRound,
  Laptop,
  LoaderCircle,
  MessageSquareText,
  Play,
  RotateCcw,
  Send,
  Settings,
  TerminalSquare,
  Wifi,
} from 'lucide-react';
import './styles.css';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000';

const providers = [
  { id: 'mock', label: 'Mock', model: '', baseUrl: '' },
  { id: 'openai', label: 'OpenAI', model: 'gpt-5.2', baseUrl: 'https://api.openai.com/v1' },
  { id: 'gemini', label: 'Gemini', model: 'gemini-2.5-flash', baseUrl: 'https://generativelanguage.googleapis.com/v1beta' },
  { id: 'claude', label: 'Claude', model: 'claude-sonnet-4-5-20250929', baseUrl: 'https://api.anthropic.com/v1' },
  { id: 'ollama', label: 'Ollama', model: 'llama3.2', baseUrl: 'http://localhost:11434/api/chat' },
  { id: 'lmstudio', label: 'LM Studio', model: 'local-model', baseUrl: 'http://localhost:1234/v1' },
];

const defaultSettings = Object.fromEntries(
  providers.map((provider) => [
    provider.id,
    {
      model: provider.model,
      baseUrl: provider.baseUrl,
      apiKey: '',
      anthropicVersion: '2023-06-01',
    },
  ]),
);

const demoInputs = [
  {
    title: '짧은 인사',
    body: '안녕, 너는 어떤 챗봇 베이스야?',
  },
  {
    title: '코드 질문',
    body: 'React에서 설정창을 단순하게 만드는 방법을 알려줘.',
  },
  {
    title: '명령어',
    body: '/help',
  },
];

function detectOS() {
  const platform = navigator.platform.toLowerCase();
  if (platform.includes('win')) return 'windows';
  if (platform.includes('mac')) return 'macos';
  return 'other';
}

function App() {
  const detectedOS = useMemo(() => detectOS(), []);
  const [osTarget, setOsTarget] = useState(detectedOS);
  const [provider, setProvider] = useState('mock');
  const [settings, setSettings] = useState(defaultSettings);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [message, setMessage] = useState(demoInputs[0].body);
  const [answer, setAnswer] = useState('');
  const [references, setReferences] = useState([]);
  const [status, setStatus] = useState('ready');
  const [error, setError] = useState('');
  const [checkResult, setCheckResult] = useState(null);

  const currentSettings = settings[provider] || defaultSettings.mock;
  const providerLabel = providers.find((item) => item.id === provider)?.label || provider;

  function updateSetting(key, value) {
    setSettings((previous) => ({
      ...previous,
      [provider]: {
        ...previous[provider],
        [key]: value,
      },
    }));
  }

  async function sendMessage(nextMessage = message) {
    const trimmed = nextMessage.trim();
    if (!trimmed) return;
    setStatus('loading');
    setError('');
    setAnswer('');
    setReferences([]);
    try {
      const response = await fetch(`${API_BASE}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: trimmed, provider, settings: currentSettings }),
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.error || '요청에 실패했습니다.');
      }
      setAnswer(data.answer || '');
      setReferences(data.references || []);
      setStatus('done');
    } catch (requestError) {
      setError(requestError.message);
      setStatus('error');
    }
  }

  async function checkProvider() {
    setCheckResult({ status: 'loading', message: '점검 중입니다.' });
    try {
      const response = await fetch(`${API_BASE}/api/providers/check`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ provider, settings: currentSettings }),
      });
      const data = await response.json();
      setCheckResult({
        status: data.ready ? 'ready' : 'missing',
        message: data.message,
        detail: `${data.provider} · ${data.model || 'model 없음'} · ${data.baseUrl || 'local mock'}`,
      });
    } catch (requestError) {
      setCheckResult({ status: 'error', message: requestError.message });
    }
  }

  function runDemo(input) {
    setMessage(input.body);
    sendMessage(input.body);
  }

  return (
    <main className="appShell">
      <section className="topBar">
        <div className="brandBlock">
          <div className="brandMark" aria-hidden="true">
            <Bot size={28} />
          </div>
          <div>
            <h1>agent_base</h1>
            <p>여러 LLM API를 갈아 끼울 수 있는 간단 챗봇 베이스</p>
          </div>
        </div>

        <div className="runState" aria-live="polite">
          {status === 'loading' ? <LoaderCircle className="spin" size={18} /> : <CheckCircle2 size={18} />}
          <span>{status === 'loading' ? '응답 생성 중' : '실행 준비 완료'}</span>
        </div>
      </section>

      <section className="controlBand" aria-label="실행 설정">
        <div className="controlGroup">
          <label>
            <Laptop size={17} />
            OS
          </label>
          <div className="segmented">
            {['windows', 'macos', 'other'].map((item) => (
              <button
                key={item}
                className={osTarget === item ? 'active' : ''}
                type="button"
                onClick={() => setOsTarget(item)}
                title={`${item} 실행 안내 선택`}
              >
                {item}
              </button>
            ))}
          </div>
        </div>

        <div className="controlGroup">
          <label>
            <Cpu size={17} />
            Provider
          </label>
          <select
            value={provider}
            onChange={(event) => {
              setProvider(event.target.value);
              setCheckResult(null);
            }}
          >
            {providers.map((item) => (
              <option key={item.id} value={item.id}>
                {item.label}
              </option>
            ))}
          </select>
        </div>

        <button className="settingsButton" type="button" onClick={() => setSettingsOpen((value) => !value)}>
          <Settings size={17} />
          Settings
        </button>

        <div className="commandHint">
          <TerminalSquare size={17} />
          <span>{osTarget === 'windows' ? 'start_windows.bat' : './start_mac.sh'}</span>
        </div>
      </section>

      {settingsOpen ? (
        <section className="settingsPanel" aria-label="Provider 설정">
          <div className="settingsHeader">
            <div>
              <h2>{providerLabel} 설정</h2>
              <p>값은 현재 브라우저 화면에서만 사용하고 저장하지 않습니다.</p>
            </div>
            <button className="secondaryButton" type="button" onClick={checkProvider}>
              <Wifi size={18} />
              Check
            </button>
          </div>

          <div className="settingsGrid">
            <label>
              <span>Model</span>
              <input
                value={currentSettings.model}
                onChange={(event) => updateSetting('model', event.target.value)}
                placeholder="model name"
                disabled={provider === 'mock'}
              />
            </label>
            <label>
              <span>Base URL</span>
              <input
                value={currentSettings.baseUrl}
                onChange={(event) => updateSetting('baseUrl', event.target.value)}
                placeholder="https://..."
                disabled={provider === 'mock'}
              />
            </label>
            <label>
              <span>API Key</span>
              <input
                type="password"
                value={currentSettings.apiKey}
                onChange={(event) => updateSetting('apiKey', event.target.value)}
                placeholder={provider === 'ollama' || provider === 'lmstudio' ? 'optional' : 'required'}
                disabled={provider === 'mock' || provider === 'ollama'}
              />
            </label>
            {provider === 'claude' ? (
              <label>
                <span>Anthropic Version</span>
                <input
                  value={currentSettings.anthropicVersion}
                  onChange={(event) => updateSetting('anthropicVersion', event.target.value)}
                  placeholder="2023-06-01"
                />
              </label>
            ) : null}
          </div>

          {checkResult ? (
            <div className={`checkBox ${checkResult.status}`}>
              <KeyRound size={17} />
              <div>
                <strong>{checkResult.message}</strong>
                {checkResult.detail ? <span>{checkResult.detail}</span> : null}
              </div>
            </div>
          ) : null}
        </section>
      ) : null}

      <section className="workspace">
        <div className="editorPane">
          <div className="paneHeader">
            <div>
              <h2>메시지</h2>
              <p>챗봇에게 보낼 질문 또는 /help 명령어</p>
            </div>
            <button className="ghostButton" type="button" onClick={() => setMessage('')} title="입력 지우기">
              <RotateCcw size={17} />
              Reset
            </button>
          </div>

          <textarea
            spellCheck="false"
            value={message}
            onChange={(event) => setMessage(event.target.value)}
            aria-label="챗봇 메시지 입력"
          />

          <div className="actionRow">
            <button className="primaryButton" type="button" onClick={() => sendMessage()} disabled={status === 'loading'}>
              {status === 'loading' ? <LoaderCircle className="spin" size={18} /> : <Send size={18} />}
              Send
            </button>
            <button className="secondaryButton" type="button" onClick={() => setMessage('/help')}>
              <FileText size={18} />
              Help
            </button>
          </div>
        </div>

        <div className="resultPane">
          <div className="paneHeader">
            <div>
              <h2>응답</h2>
              <p>{providerLabel} 결과</p>
            </div>
            <MessageSquareText size={22} />
          </div>

          {error ? <div className="errorBox">{error}</div> : null}
          <pre className="answerBox">{answer || '아직 응답이 없습니다.'}</pre>

          {references.length > 0 ? (
            <div className="references">
              <h3>참고 문서</h3>
              {references.map((reference) => (
                <pre key={reference}>{reference}</pre>
              ))}
            </div>
          ) : null}
        </div>
      </section>

      <section className="demoBand" aria-label="데모 입력">
        <div className="demoIntro">
          <Play size={19} />
          <span>Demo</span>
        </div>
        {demoInputs.map((input) => (
          <button key={input.title} type="button" onClick={() => runDemo(input)}>
            {input.title}
          </button>
        ))}
      </section>
    </main>
  );
}

createRoot(document.getElementById('root')).render(<App />);

import React, { useMemo, useState } from 'react';
import { createRoot } from 'react-dom/client';
import {
  Bot,
  Bug,
  CheckCircle2,
  Cpu,
  FileText,
  Laptop,
  LoaderCircle,
  Play,
  RotateCcw,
  Send,
  TerminalSquare,
} from 'lucide-react';
import './styles.css';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000';

const demoInputs = [
  {
    title: '콜론 누락',
    body: `if score >= 60\n    print("pass")`,
  },
  {
    title: '들여쓰기 오류',
    body: `for i in range(3):\nprint(i)`,
  },
  {
    title: '괄호 누락',
    body: `print("hello"`,
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
  const [message, setMessage] = useState(demoInputs[0].body);
  const [answer, setAnswer] = useState('');
  const [references, setReferences] = useState([]);
  const [status, setStatus] = useState('ready');
  const [error, setError] = useState('');

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
        body: JSON.stringify({ message: trimmed, provider }),
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
            <p>Python 문법 오류를 Mock 엔진으로 먼저 분석하는 학습용 Agent</p>
          </div>
        </div>

        <div className="runState" aria-live="polite">
          {status === 'loading' ? <LoaderCircle className="spin" size={18} /> : <CheckCircle2 size={18} />}
          <span>{status === 'loading' ? '분석 중' : '실행 준비 완료'}</span>
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
            Engine
          </label>
          <select value={provider} onChange={(event) => setProvider(event.target.value)}>
            <option value="mock">mock</option>
            <option value="openai">openai</option>
            <option value="ollama">ollama</option>
          </select>
        </div>

        <div className="commandHint">
          <TerminalSquare size={17} />
          <span>{osTarget === 'windows' ? 'start_windows.bat' : './start_mac.sh'}</span>
        </div>
      </section>

      <section className="workspace">
        <div className="editorPane">
          <div className="paneHeader">
            <div>
              <h2>입력</h2>
              <p>Python 코드, 에러 메시지, 또는 /help 명령어</p>
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
            aria-label="분석할 Python 코드 입력"
          />

          <div className="actionRow">
            <button className="primaryButton" type="button" onClick={() => sendMessage()} disabled={status === 'loading'}>
              {status === 'loading' ? <LoaderCircle className="spin" size={18} /> : <Send size={18} />}
              Analyze
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
              <p>{provider} 엔진 결과</p>
            </div>
            <Bug size={22} />
          </div>

          {error ? <div className="errorBox">{error}</div> : null}
          <pre className="answerBox">{answer || '아직 분석 결과가 없습니다.'}</pre>

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


# agent_base

`agent_base`는 Windows와 macOS에서 실행 가능한 간단 챗봇 베이스입니다.

기본 Mock 모드는 API 키 없이 동작합니다. 설정 창에서 OpenAI, Gemini, Claude, Ollama, LM Studio로 Provider를 바꿔 연결 파이프라인을 확인할 수 있습니다.

## 빠른 실행

### Windows PowerShell

```powershell
git clone <YOUR_REPOSITORY_URL>
cd agent_base
.\start_windows.bat
```

만약 `py`가 없다면:

```powershell
python start.py
```

### macOS

```bash
git clone <YOUR_REPOSITORY_URL>
cd agent_base
chmod +x start_mac.sh
./start_mac.sh
```

또는:

```bash
python3 start.py
```

실행 후 브라우저에서 아래 주소를 엽니다.

```txt
http://127.0.0.1:5173
```

## 실행 흐름

`start.py`는 시작할 때 OS와 엔진을 선택합니다.

```txt
OS: windows / macos / other
Engine: mock / openai / gemini / claude / ollama / lmstudio
```

기본값은 현재 OS 자동 감지와 `mock` 엔진입니다.

## 필요한 프로그램

- Python 3.10 이상
- Node.js 20 이상
- npm

처음 실행할 때 `frontend/node_modules`가 없으면 `start.py`가 자동으로 `npm install`을 실행합니다.

## 폴더 구조

```txt
agent_base/
├─ backend/
│  ├─ server.py
│  ├─ config.py
│  ├─ agent/
│  ├─ data/
│  └─ docs/knowledge/
├─ frontend/
│  ├─ package.json
│  └─ src/
├─ docs/
├─ start.py
├─ start_mac.sh
├─ start_windows.bat
├─ .env.example
└─ render.yaml
```

## GUI 설정 창

상단 `Settings` 버튼을 누르면 현재 Provider의 최소 설정만 입력할 수 있습니다.

```txt
Model
Base URL
API Key
Anthropic Version(Claude만)
```

입력한 API Key는 브라우저 저장소나 파일에 저장하지 않고, 현재 요청에만 사용합니다. `Check` 버튼은 모델명, URL, API Key 필요 여부를 점검합니다.

## API

```txt
GET  /api/health
POST /api/chat
```

`POST /api/chat` 예시:

```json
{
  "message": "안녕, 너는 어떤 챗봇 베이스야?",
  "provider": "mock",
  "settings": {
    "model": "",
    "baseUrl": "",
    "apiKey": ""
  }
}
```

Provider 설정 점검:

```txt
POST /api/providers/check
GET  /api/providers
```

## Agent 명령어

GUI 입력창 또는 API 메시지에 아래 명령어를 넣을 수 있습니다.

```txt
/help
/clear
/note 오늘 배운 내용
/read backend/docs/knowledge/chatbot_base.md
/files backend/docs/knowledge
```

## 엔진 선택

### mock

API 키 없이 실행됩니다. `ast.parse` 기반으로 Python 문법 오류를 먼저 확인합니다.

### openai

OpenAI Chat Completions 호환 경로를 사용합니다.

```txt
POST https://api.openai.com/v1/chat/completions
```

`.env` 또는 설정 창에 API Key를 입력합니다.

### gemini

Google Gemini `generateContent` REST 경로를 사용합니다.

```txt
POST https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent
```

### claude

Anthropic Messages API 경로를 사용합니다.

```txt
POST https://api.anthropic.com/v1/messages
```

`x-api-key`와 `anthropic-version` 헤더가 필요합니다.

### ollama

Ollama가 로컬에서 실행 중이어야 합니다.

```txt
POST http://localhost:11434/api/chat
```

### lmstudio

LM Studio의 OpenAI-compatible local server를 사용합니다.

```txt
POST http://localhost:1234/v1/chat/completions
```

## 배포

`render.yaml`을 포함해 Render 배포를 준비해두었습니다. GitHub에 push한 뒤 Render에서 이 저장소를 연결하면 React 빌드 결과를 Python 백엔드가 함께 서빙합니다.

## 보안

- `.env`는 GitHub에 올리지 않습니다.
- 파일 읽기 Tool은 프로젝트 밖 경로, 숨김 파일, `.env`, `.git`, `node_modules` 접근을 차단합니다.
- Retriever는 `backend/docs/knowledge` 안의 Markdown 문서만 참고합니다.

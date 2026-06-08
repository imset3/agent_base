# agent_base

`agent_base`는 Windows와 macOS에서 실행 가능한 Mock 기반 Python Agent + React GUI 템플릿입니다.

기본 주제는 **Python 문법 오류 설명 Agent**입니다. Mock 모드에서는 API 키 없이 로컬 규칙으로 문법 오류를 분석하고, 필요하면 OpenAI 또는 Ollama 엔진으로 확장할 수 있습니다.

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
Engine: mock / openai / ollama
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

## API

```txt
GET  /api/health
POST /api/chat
```

`POST /api/chat` 예시:

```json
{
  "message": "if score >= 60\n    print(\"pass\")",
  "provider": "mock"
}
```

## Agent 명령어

GUI 입력창 또는 API 메시지에 아래 명령어를 넣을 수 있습니다.

```txt
/help
/clear
/note 오늘 배운 내용
/read backend/docs/knowledge/python_syntax.md
/files backend/docs/knowledge
```

## 엔진 선택

### mock

API 키 없이 실행됩니다. `ast.parse` 기반으로 Python 문법 오류를 먼저 확인합니다.

### openai

`.env` 또는 환경변수에 `OPENAI_API_KEY`를 설정한 뒤 실행합니다. 선택 기능입니다.

### ollama

Ollama가 로컬에서 실행 중이어야 합니다. 기본 모델명은 `llama3.2`입니다.

## 배포

`render.yaml`을 포함해 Render 배포를 준비해두었습니다. GitHub에 push한 뒤 Render에서 이 저장소를 연결하면 React 빌드 결과를 Python 백엔드가 함께 서빙합니다.

## 보안

- `.env`는 GitHub에 올리지 않습니다.
- 파일 읽기 Tool은 프로젝트 밖 경로, 숨김 파일, `.env`, `.git`, `node_modules` 접근을 차단합니다.
- Retriever는 `backend/docs/knowledge` 안의 Markdown 문서만 참고합니다.


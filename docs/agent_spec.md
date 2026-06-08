# Agent 설계서

## 이름

agent_base

## 목적

Windows와 macOS에서 바로 실행할 수 있는 간단 챗봇 베이스입니다. Mock으로 먼저 파이프라인을 확인하고, 설정 창에서 여러 LLM Provider를 연결할 수 있습니다.

## 주요 사용자

- Agent 구조를 React GUI까지 확장해보고 싶은 학습자
- OpenAI, Gemini, Claude, Ollama, LM Studio 연결 구조를 비교하려는 개발자
- 클론 후 바로 실행 가능한 챗봇 템플릿이 필요한 사용자

## 핵심 기능

1. 사용자 메시지 입력
2. Mock 엔진으로 로컬 파이프라인 확인
3. React GUI에서 OS와 Provider 선택
4. Settings 패널에서 모델명, Base URL, API Key 입력
5. OpenAI, Gemini, Claude, Ollama, LM Studio 연결 구조 제공

## 기술 구조

```txt
React GUI
  -> Python HTTP API
    -> AgentCore
      -> Memory / Tools / Retriever / Provider adapter
```

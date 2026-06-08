# Agent 설계서

## 이름

agent_base / PyFix Tutor

## 목적

Python 초보자가 자주 만나는 문법 오류를 쉽게 이해하도록 돕는 Mock 기반 Agent입니다.

## 주요 사용자

- Python을 처음 배우는 학습자
- 에러 메시지를 읽는 데 익숙하지 않은 멘티
- Agent 구조를 React GUI까지 확장해보고 싶은 개발자

## 핵심 기능

1. Python 코드 또는 에러 메시지 입력
2. Mock 엔진으로 문법 오류 분석
3. 오류 위치, 원인, 수정 방향, 짧은 메모 제공
4. React GUI에서 OS와 엔진 선택
5. OpenAI/Ollama 선택 확장 구조 제공

## 기술 구조

```txt
React GUI
  -> Python HTTP API
    -> AgentCore
      -> Memory / Tools / Retriever / LLM provider
```


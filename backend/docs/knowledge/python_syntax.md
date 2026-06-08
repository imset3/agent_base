# Python 문법 오류 빠른 참고

## 콜론 누락

`if`, `for`, `while`, `def`, `class`처럼 코드 블록을 시작하는 문장은 줄 끝에 콜론(`:`)이 필요합니다.

```python
if score >= 60:
    print("pass")
```

## 들여쓰기 오류

Python은 중괄호 대신 들여쓰기로 코드 블록을 구분합니다. 보통 스페이스 4칸을 사용합니다.

```python
for i in range(3):
    print(i)
```

## 괄호와 따옴표

열린 괄호나 따옴표는 같은 종류로 닫아야 합니다.

```python
print("hello")
numbers = [1, 2, 3]
```


# Python 3.11 슬림 이미지 사용
FROM python:3.11-slim

# 작업 디렉토리 설정
WORKDIR /app

# 필수 시스템 패키지 설치 (Playwright 의존성 등)
# uv 설치
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# 프로젝트 파일 복사
COPY pyproject.toml uv.lock ./
COPY src/ ./src/
COPY README.md ./

# 의존성 설치
RUN uv sync --frozen

# Playwright 브라우저 설치
RUN uv run playwright install chromium
RUN uv run playwright install-deps chromium

# 실행 권한 설정 (선택)
# RUN chmod +x src/cli.py

# 환경 변수 설정
ENV PYTHONPATH=/app
ENV HEADLESS=true

# 기본 실행 명령어 (도움말 출력)
ENTRYPOINT ["uv", "run", "crawler"]
CMD ["--help"]

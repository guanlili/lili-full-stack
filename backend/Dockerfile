FROM python:3.14-slim

# 依赖下载源可覆盖（大陆服务器等网络受限环境设为镜像源；uv 会把 lock 中
# 记录的 pypi.org 请求重写到该源，lockfile 内容不变）
ARG UV_INDEX_URL=https://pypi.org/simple
ENV UV_DEFAULT_INDEX=$UV_INDEX_URL

ENV PYTHONUNBUFFERED=1

# Install uv
# Ref: https://docs.astral.sh/uv/guides/integration/docker/#installing-uv
COPY --from=ghcr.io/astral-sh/uv:0.9.26 /uv /uvx /bin/

# Compile bytecode
# Ref: https://docs.astral.sh/uv/guides/integration/docker/#compiling-bytecode
ENV UV_COMPILE_BYTECODE=1

# uv Cache
# Ref: https://docs.astral.sh/uv/guides/integration/docker/#caching
ENV UV_LINK_MODE=copy

WORKDIR /app/

# Place executables in the environment at the front of the path
# Ref: https://docs.astral.sh/uv/guides/integration/docker/#using-the-environment
ENV PATH="/app/.venv/bin:$PATH"

# Install dependencies
# Ref: https://docs.astral.sh/uv/guides/integration/docker/#intermediate-layers
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-workspace --no-dev --package app

COPY ./backend/scripts /app/backend/scripts

COPY ./backend/pyproject.toml ./backend/alembic.ini /app/backend/

COPY ./backend/app /app/backend/app

# Sync the project
# Ref: https://docs.astral.sh/uv/guides/integration/docker/#intermediate-layers
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-dev --package app

# 非 root 运行：容器内进程被攻破时不直接持有 root 身份
# （frontend 镜像保持官方 nginx 默认行为：master 需 root 绑定 80 特权端口）
RUN addgroup --system app && adduser --system --ingroup app app \
    && mkdir -p /app/uploads \
    && chown -R app:app /app
USER app

WORKDIR /app/backend/

CMD ["sh", "-c", "fastapi run --workers ${WORKERS:-1}"]

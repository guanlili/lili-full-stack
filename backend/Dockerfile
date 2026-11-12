FROM python:3.14-slim

# 依赖下载源可覆盖（大陆服务器等网络受限环境设为镜像源，如
# https://mirrors.cloud.tencent.com/pypi/simple）。
# 注意：uv sync --frozen 按 lock 里记录的 files.pythonhosted.org 直链下载、
# 忽略 index 配置（https://github.com/astral-sh/uv/issues/19625），
# 因此镜像源启用时还需把 lock 中的下载直链域名重写为镜像的同构路径
# （主流镜像 tuna/腾讯云均满足：{mirror}/simple 与 {mirror}/packages 同根）。
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
# （bind mount 换成 COPY：镜像源启用时需要 sed 原地重写 lock 的下载直链，
#   见文件头说明；重写只发生在镜像层内，不污染构建上下文）
COPY uv.lock pyproject.toml ./
RUN --mount=type=cache,target=/root/.cache/uv \
    if [ "$UV_INDEX_URL" != "https://pypi.org/simple" ]; then \
      sed -i "s|https://files.pythonhosted.org|${UV_INDEX_URL%/simple}|g" uv.lock; \
    fi && \
    uv sync --frozen --no-install-workspace --no-dev --package app

COPY ./backend/scripts /app/backend/scripts

COPY ./backend/pyproject.toml ./backend/alembic.ini /app/backend/

COPY ./backend/app /app/backend/app

# Sync the project
# Ref: https://docs.astral.sh/uv/guides/integration/docker/#intermediate-layers
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --package app

# 非 root 运行：容器内进程被攻破时不直接持有 root 身份
# （frontend 镜像保持官方 nginx 默认行为：master 需 root 绑定 80 特权端口）
RUN addgroup --system app && adduser --system --ingroup app app \
    && mkdir -p /app/uploads \
    && chown -R app:app /app
USER app

WORKDIR /app/backend/

CMD ["sh", "-c", "fastapi run --workers ${WORKERS:-1}"]

# Stage base: 安装依赖（dev / build 共用）
# 注意：lockfile 需在仓库中提交（frontend/package-lock.json），npm ci 保证构建可复现
# NPM_REGISTRY 可覆盖为镜像源（大陆服务器等网络受限环境），lockfile 的
# integrity 校验不受 registry 影响
FROM node:24-slim AS base

ARG NPM_REGISTRY=https://registry.npmjs.org

WORKDIR /app/frontend

COPY frontend/package.json frontend/package-lock.json ./

RUN --mount=type=cache,target=/root/.npm npm ci --registry=$NPM_REGISTRY

COPY ./frontend ./

# Stage dev: 本地开发用 vite dev server（compose.override.yml 里 target: dev）
FROM base AS dev

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]

# Stage build: 编译静态文件
FROM base AS build-stage

ARG VITE_API_URL
# 可选：配置后前端构建期注入 Sentry DSN（与后端共用一个 DSN）
ARG VITE_SENTRY_DSN
# 自建 GlitchTip 上报源（origin，含 scheme 与域名，不带路径）。用于 nginx CSP
# connect-src 放行；未配置时 CSP 仅放行 self。不要填 Sentry 云。
ARG GLITCHTIP_ORIGIN=

RUN npm run build

# Stage final（默认 target）: nginx 托管静态文件 + 反代 /api
FROM nginx:1

COPY --from=build-stage /app/frontend/dist/ /usr/share/nginx/html

# 渲染 nginx.conf 中的 $GLITCHTIP_ORIGIN 占位；仅替换这一个变量，避免误改其他 $ 引用。
# envsubst 在最终镜像的构建层执行，产物 conf 已是定值（运行期不再做模板替换）。
COPY ./frontend/nginx.conf /tmp/nginx.conf.template
ARG GLITCHTIP_ORIGIN=
RUN envsubst '${GLITCHTIP_ORIGIN}' < /tmp/nginx.conf.template > /etc/nginx/conf.d/default.conf \
  && rm /tmp/nginx.conf.template

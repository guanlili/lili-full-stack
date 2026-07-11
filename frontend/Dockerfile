# Stage 0: build static assets with Node.js (compatible with kernel 3.10+)
FROM node:20-slim AS build-stage

WORKDIR /app/frontend

COPY frontend/package.json ./

# 不使用 package-lock.json：lock 文件在 macOS 生成，缺少 Linux x64 原生绑定
RUN npm install --no-package-lock

COPY ./frontend ./

ARG VITE_API_URL
RUN npm run build


# Stage 1: serve with nginx
FROM nginx:1

COPY --from=build-stage /app/frontend/dist/ /usr/share/nginx/html

COPY ./frontend/nginx.conf /etc/nginx/conf.d/default.conf

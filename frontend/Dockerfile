# Stage 0: build static assets with Node.js (compatible with kernel 3.10+)
FROM node:20-slim AS build-stage

WORKDIR /app

# Copy workspace manifest + lock file for deterministic install
COPY package.json package-lock.json ./
COPY frontend/package.json ./frontend/

RUN npm ci --workspace=frontend

COPY ./frontend ./frontend/

ARG VITE_API_URL
WORKDIR /app/frontend
RUN npm run build


# Stage 1: serve with nginx
FROM nginx:1

COPY --from=build-stage /app/frontend/dist/ /usr/share/nginx/html

COPY ./frontend/nginx.conf /etc/nginx/conf.d/default.conf

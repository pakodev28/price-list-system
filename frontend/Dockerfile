# Multi-stage: build the SPA to static files, then serve them with nginx.
# `npm ci` installs deterministically from the lockfile and is cached as its own
# layer (re-runs only when dependencies change). The runtime image is a tiny
# nginx with no node_modules and no dev server.
FROM node:20-slim AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY . .
ARG VITE_API_BASE_URL=http://localhost:8000/api
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
RUN npm run build

FROM nginx:alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80

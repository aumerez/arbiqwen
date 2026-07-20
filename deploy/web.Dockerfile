# syntax=docker/dockerfile:1
# Build the Vite SPA, then serve it with nginx (which also proxies the API).
# Build context is the REPO ROOT (so both web/ and deploy/nginx.conf are
# reachable); see docker-compose.prod.yml.

FROM node:20-alpine AS build
WORKDIR /app

# Install deps against the lockfile for reproducible builds.
COPY web/package.json web/package-lock.json* ./
RUN npm ci

# Build. VITE_API_BASE_URL is intentionally left empty so the SPA makes
# same-origin calls that nginx proxies to the backend (no CORS).
COPY web/ .
RUN npm run build

FROM nginx:1.27-alpine
COPY deploy/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80

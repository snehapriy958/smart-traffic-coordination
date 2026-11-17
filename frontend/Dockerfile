# ==============================================================================
# Smart Traffic Coordination System — Frontend React Dashboard Dockerfile
# Multi-stage production build and NGINX distribution
# ==============================================================================

# Stage 1: Build production static bundle
FROM node:20-alpine AS build

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

# Stage 2: Serve with lightweight NGINX Alpine
FROM nginx:alpine AS runtime

# Copy custom NGINX configuration with API/WebSocket reverse-proxy support
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy compiled SPA static artifacts
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 5173

HEALTHCHECK --interval=15s --timeout=5s --start-period=5s --retries=3 \
    CMD wget -q -O - http://127.0.0.1:5173/ || exit 1

CMD ["nginx", "-g", "daemon off;"]

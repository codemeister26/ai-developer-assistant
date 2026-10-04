# ─── Build ───
FROM node:22-slim AS build

WORKDIR /app
COPY package*.json ./
RUN npm ci

COPY . .
# Vite build time par env baked karta hai, runtime par nahi
ARG VITE_API_URL=http://localhost:8000
ENV VITE_API_URL=$VITE_API_URL
RUN npm run build

# ─── Serve ───
FROM nginx:alpine

COPY --from=build /app/dist /usr/share/nginx/html
# SPA hai — har route index.html par jaana chahiye
RUN printf 'server {\n\
  listen 80;\n\
  root /usr/share/nginx/html;\n\
  location / { try_files $uri /index.html; }\n\
}\n' > /etc/nginx/conf.d/default.conf

EXPOSE 80

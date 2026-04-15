FROM node:20-alpine AS build
WORKDIR /app
# Browser must call same-origin `/api/...` so nginx (or Vite dev proxy) forwards to api-gateway.
# Without this, `vite build` has no `window` and previously fell back to http://localhost:8000/api,
# which breaks behind :3000, on LAN IPs, or if port 8000 is not the gateway.
ARG VITE_API_URL=/api
ENV VITE_API_URL=$VITE_API_URL
COPY package*.json ./
RUN npm ci --legacy-peer-deps
COPY . .
RUN npm run build

FROM nginx:1.27-alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80

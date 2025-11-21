FROM node:20-alpine as builder
WORKDIR /app

# Install dependencies
COPY frontend/package.json frontend/package-lock.json* ./frontend/
RUN cd frontend && npm ci

# Copy frontend app and build
COPY frontend ./frontend
WORKDIR /app/frontend
RUN npm run build

# Run stage
FROM nginx:stable-alpine
COPY --from=builder /app/frontend/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]

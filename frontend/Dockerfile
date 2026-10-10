# =============================================================================
# Legatio AI — Frontend Dockerfile
# =============================================================================
# Multi-stage build for development with hot reload.
# Production build uses a separate stage.
# =============================================================================

FROM node:20-alpine AS base

WORKDIR /app

# Install dependencies first (cache layer)
COPY package.json package-lock.json* ./
RUN npm install

# Copy project source
COPY . .

# Expose Vite dev server port
EXPOSE 5173

# Default command: run Vite dev server
CMD ["npm", "run", "dev"]

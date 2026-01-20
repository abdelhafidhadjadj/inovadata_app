FROM node:20-alpine

WORKDIR /app

# Install build dependencies for native modules
RUN apk add --no-cache python3 make g++

# Copy package files first
COPY package.json package-lock.json ./

# Install dependencies (this will build bcrypt for Alpine)
RUN npm ci

# Copy source code (but exclude node_modules via .dockerignore)
COPY . .

# Remove any local node_modules that might have been copied
RUN rm -rf node_modules

# Reinstall to ensure everything is built for Alpine
RUN npm ci

# Generate .svelte-kit directory
RUN npm run sync || true

# Expose ports
EXPOSE 3000
EXPOSE 5173

# Start development server with hot reload
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
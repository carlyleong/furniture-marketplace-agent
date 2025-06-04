FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Clean install dependencies
RUN npm ci --prefer-offline --no-audit

# Copy source code
COPY . .

# Set environment for Docker
ENV NODE_ENV=production

# Build the app
RUN npm run build

# Expose port
EXPOSE 3000

# Use preview mode to serve built app with proxy support
CMD ["npm", "run", "preview", "--", "--host", "0.0.0.0", "--port", "3000"]

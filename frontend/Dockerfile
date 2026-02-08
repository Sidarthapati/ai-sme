FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy application code
COPY . .

# Railway automatically passes environment variables to Docker builds
# Debug: Print env vars to verify they're available (remove after debugging)
RUN echo "🔍 NEXT_PUBLIC_API_URL: $NEXT_PUBLIC_API_URL"
RUN echo "🔍 NEXT_PUBLIC_GOOGLE_CLIENT_ID: $NEXT_PUBLIC_GOOGLE_CLIENT_ID"

# Build the application (Next.js reads process.env.NEXT_PUBLIC_* at build time)
# Railway should automatically pass these env vars to the build process
RUN npm run build

# Expose port
EXPOSE 3000

# Start production server
CMD ["npm", "start"]

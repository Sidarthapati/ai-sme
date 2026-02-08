FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies  
RUN npm ci

# Copy application code
COPY . .

# Railway passes environment variables, but they might not be available during build
# We'll create .env.production using the build script which reads Railway's env vars
# The script will use process.env which Railway should populate
RUN NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL} \
    NEXT_PUBLIC_GOOGLE_CLIENT_ID=${NEXT_PUBLIC_GOOGLE_CLIENT_ID} \
    NEXT_PUBLIC_APP_NAME=${NEXT_PUBLIC_APP_NAME} \
    NEXT_PUBLIC_APP_VERSION=${NEXT_PUBLIC_APP_VERSION} \
    NEXT_PUBLIC_ENABLE_FILE_UPLOAD=${NEXT_PUBLIC_ENABLE_FILE_UPLOAD} \
    NEXT_PUBLIC_ENABLE_FEEDBACK=${NEXT_PUBLIC_ENABLE_FEEDBACK} \
    NEXT_PUBLIC_ENABLE_DARK_MODE=${NEXT_PUBLIC_ENABLE_DARK_MODE} \
    npm run build

# Expose port
EXPOSE 3000

# Start production server  
CMD ["npm", "start"]

FROM node:20-alpine

WORKDIR /app

# Copy package.json and package-lock.json
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy the rest of the application
COPY . .

# Create directory for Anki data (will be mounted as a volume)
RUN mkdir -p /app/anki_data

# Expose the port the app runs on
EXPOSE 3001

# Command to run the application
CMD ["node", "server.js"] 
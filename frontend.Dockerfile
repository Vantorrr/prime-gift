FROM node:18-alpine

WORKDIR /app

COPY PrimeGift/frontend/package*.json ./
RUN npm install

COPY PrimeGift/frontend/ .

# Build with ignore errors
ENV NEXT_TELEMETRY_DISABLED 1
RUN npm run build

# Set hostname to 0.0.0.0 to allow external access
ENV HOSTNAME "0.0.0.0"
ENV PORT 3000
EXPOSE 3000

CMD ["npm", "start"]
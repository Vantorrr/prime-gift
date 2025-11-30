FROM node:18-alpine

WORKDIR /app

COPY PrimeGift/frontend/package*.json ./
RUN npm install

COPY PrimeGift/frontend/ .

# Build with ignore errors
ENV NEXT_TELEMETRY_DISABLED 1
RUN npm run build

CMD ["npm", "start"]


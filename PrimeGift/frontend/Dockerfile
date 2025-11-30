FROM node:18-alpine

WORKDIR /app

COPY PrimeGift/frontend/package*.json ./
RUN npm install

COPY PrimeGift/frontend/ .

RUN npm run build

CMD ["npm", "start"]

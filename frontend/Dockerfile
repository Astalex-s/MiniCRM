# React CRM frontend (Vite dev server). В Compose прокси /api → crm-api:8000
FROM node:20-alpine

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm install

COPY . .
EXPOSE 5173

CMD ["npm", "run", "dev"]

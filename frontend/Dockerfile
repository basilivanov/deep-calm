# Frontend Dockerfile
FROM node:20-alpine

WORKDIR /app

# Копируем package files
COPY package*.json ./

# Устанавливаем зависимости
RUN npm install

# Копируем исходники
COPY . .

# Expose порт
EXPOSE 3000

# Dev server с hot-reload
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]

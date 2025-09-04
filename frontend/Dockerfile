# Stage 1: build
FROM node:22.17.1-bullseye AS build

WORKDIR /app

# Copia package.json e package-lock.json / installa dipendenze
COPY package*.json ./
RUN npm install

# Copia tutto il progetto e build
COPY . .
RUN npm run build

# Stage 2: serve
FROM node:22.17.1-bullseye

WORKDIR /app

# Copia i file buildati
COPY --from=build /app ./

# Espone la porta Vite preview
EXPOSE 5173

# Avvia in modalità preview
CMD ["npm", "run", "preview", "--", "--host", "0.0.0.0"]

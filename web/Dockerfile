FROM node:20-slim

WORKDIR /app

COPY package.json ./
RUN npm install

COPY . .

EXPOSE 5173

# Dev server is fine for the self-hosted demo; it serves the SPA with HMR.
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]

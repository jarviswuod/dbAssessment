# ── Base: shared deps ──
FROM node:20-alpine AS base
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm install

# ── Dev: no build, hot-reload ──
FROM base AS dev
COPY . .
EXPOSE 3000
CMD ["npm", "run", "dev"]

# ── Prod: build + serve ──
FROM base AS prod
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["npm", "run", "start"]

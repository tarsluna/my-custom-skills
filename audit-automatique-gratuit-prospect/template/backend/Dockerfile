FROM node:22-bookworm-slim

ENV NODE_ENV=production \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright \
    DATA_DIR=/data \
    PORT=8080

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci --omit=dev

# Chromium (headless shell) et ses bibliothèques système.
RUN npx playwright install --with-deps --only-shell chromium \
  && chmod -R o+rX /ms-playwright \
  && apt-get update && apt-get install -y --no-install-recommends gosu fonts-liberation \
  && rm -rf /var/lib/apt/lists/*

COPY tsconfig.json ./
COPY src ./src
COPY migrations ./migrations
COPY assets ./assets
COPY audit.config.json ./
COPY docker-entrypoint.sh ./
RUN chmod +x docker-entrypoint.sh && mkdir -p /data

EXPOSE 8080
ENTRYPOINT ["./docker-entrypoint.sh"]
CMD ["node", "--import", "tsx", "src/index.ts"]

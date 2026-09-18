# Dev-server image: hot reload against the api service. For a production
# build use `npm run build` and serve dist/ with any static host.
FROM node:22-alpine

WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .

EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]

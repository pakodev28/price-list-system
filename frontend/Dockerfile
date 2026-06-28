FROM node:20-slim

WORKDIR /app

COPY package.json ./
# --no-audit/--no-fund skip slow network calls that can stall the install.
RUN npm install --no-audit --no-fund

COPY . .

EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]

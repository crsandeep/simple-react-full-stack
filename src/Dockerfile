# Step 1: Build the React client
FROM node:16 AS client-build
WORKDIR /app
COPY client ./client
WORKDIR /app/client
RUN npm install && npm run build

# Step 2: Prepare the Express server
FROM node:16 AS server
WORKDIR /app
COPY server ./server
WORKDIR /app/server
RUN npm install

# Step 3: Copy React build into server
COPY --from=client-build /app/client/build ./server/public

# Step 4: Serve using Express
WORKDIR /app/server
EXPOSE 5000
CMD ["node", "index.js"]

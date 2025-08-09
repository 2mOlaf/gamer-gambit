# test using the latest node container
FROM node:latest AS ci
LABEL cicd="gambit-dev"
WORKDIR /app
COPY node/* ./
RUN npm ci --development
# test okay?
# get production modules
RUN rm -rf node_modules && npm ci --production

# This is our runtime container that will end up
# running on the device.
FROM node:alpine
LABEL cicd="gambit-prod"
WORKDIR /app
COPY --from=ci /app /app/
COPY --from=ci /app/node_modules node_modules

# Launch our App.
CMD ["node", "/app/index.js"]
# test using the latest node container
FROM node:latest AS ci
LABEL cicd="gambit-dev"
WORKDIR /app
COPY package*.json ./
RUN npm ci --development
COPY node ./

# test
# RUN npm test

# get production modules
RUN rm -rf node_modules && npm ci --production

# This is our runtime container that will end up
# running on the device.
FROM node:alpine
LABEL cicd="gambit-prod"
WORKDIR /app
COPY --from=ci /app /app/
COPY --from=ci /app/node_modules node_modules
USER node
RUN chown -R node:node ./node_modules

# Launch our App.
CMD ["node", "index.js"]
# test using the latest node container
FROM node:latest AS ci
LABEL cicd="gambit-dev"
WORKDIR /app
COPY package*.json ./
RUN npm ci --development
COPY . ./

# test
# RUN npm test

# get production modules
RUN rm -rf node_modules && npm ci --production

# This is our runtime container that will end up
# running on the device.
FROM node:alpine

# mark it with a label, so we can remove dangling images
LABEL cicd="gambit-prod"

# Copy our node_modules into our deployable container context.
WORKDIR /app
COPY --from=ci /app/node_modules node_modules
USER node
RUN chown -R node:node ./node_modules
EXPOSE 8080

# Launch our App.
CMD ["node", "index.js"]
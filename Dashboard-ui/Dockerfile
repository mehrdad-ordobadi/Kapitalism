FROM node:13.12.0-alpine
WORKDIR /app
ENV PATH /app/node_modules/.bin:$PATH
# Add these environment variables
ENV CI=true
ENV WATCHPACK_POLLING=true
ENV WDS_SOCKET_HOST=0.0.0.0
ENV WDS_SOCKET_PORT=3000
ENV HOST=0.0.0.0

COPY package.json ./
COPY package-lock.json ./
RUN npm install
RUN npm install react-scripts@3.4.1 -g
COPY . ./

CMD ["npm", "start", "--", "--host", "0.0.0.0"]
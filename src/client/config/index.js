export default {
  BACKEND_SERVER_ENDPOINT: process.env.REACT_APP_BACKEND_URL,
  BACKEND_SERVER_PORT: parseInt(process.env.REACT_APP_BACKEND_PORT, 10),
  BACKEND_SERVER_URL: `http://${process.env.REACT_APP_BACKEND_URL}:${parseInt(process.env.REACT_APP_BACKEND_PORT, 10)}`
};

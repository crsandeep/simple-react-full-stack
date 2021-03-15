module.exports = {
  env: {
    browser: true,
    es6: true,
  },
  extends: 'airbnb',
  parser: "babel-eslint",
  globals: {
    Atomics: 'readonly',
    SharedArrayBuffer: 'readonly',
  },
  parserOptions: {
    ecmaFeatures: {
      jsx: true,
      "experimentalObjectRestSpread": true
    },
    ecmaVersion: 2018,
    sourceType: 'module',
  },
  plugins: [
    'react',
  ],
  rules: {
    "no-console": "off",
    "react/jsx-filename-extension": [1, {"extensions": [".js", ".jsx"]}],
    "linebreak-style": 0 ,
    "no-multiple-empty-lines": [2, {"max": 99999, "maxEOF": 0}],
    'react/state-in-constructor': 1,
  },
};

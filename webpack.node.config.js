// this webpack used to bundle node.js which is not mandatory for most project

const path = require('path');
const HtmlWebpackPlugin = require('html-webpack-plugin');
const CleanWebpackPlugin = require('clean-webpack-plugin');
const { BundleAnalyzerPlugin } = require('webpack-bundle-analyzer');
const webpack = require('webpack');
const nodeExternals = require('webpack-node-externals');
const TerserPlugin = require('terser-webpack-plugin');

// for react read config
require('dotenv').config();


const outputDirectory = './bundle/server';

module.exports = {
  target: 'node',
  entry: ['babel-polyfill', './src/server/index.ts'],
  output: {
    path: path.join(__dirname, outputDirectory),
    filename: 'bundle-back.js',
    publicPath: '/'
  },
  externals: [nodeExternals()],
  module: {
    rules: [{
      test: /\.(ts|tsx)$/,
      include: path.resolve(__dirname, './src/server'),
      exclude: /node_modules/,
      use: {
        loader: 'ts-loader'
      }
    }
    ]
  },
  resolve: {
    extensions: ['.json', '.js', '.ts', '.tsx']
  },
  plugins: [
    new CleanWebpackPlugin([outputDirectory]),
    new webpack.ContextReplacementPlugin(/moment[/\\]locale$/, /en/)
    // new BundleAnalyzerPlugin() // plug-in for analyzer bundle size
  ]
  // , stats: {
  //   children: true
  // }
};

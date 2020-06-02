const path = require('path');
const HtmlWebpackPlugin = require('html-webpack-plugin');
const CleanWebpackPlugin = require('clean-webpack-plugin');
const { BundleAnalyzerPlugin } = require('webpack-bundle-analyzer');
const webpack = require('webpack');

// for react read config
require('dotenv').config();

const outputDirectory = './dist/client';

module.exports = {
  target: 'web',
  entry: ['babel-polyfill', './src/client/index.js'],
  output: {
    path: path.join(__dirname, outputDirectory),
    filename: 'bundle-front.js',
    publicPath: '/'
  },
  module: {
    rules: [{
      test: /\.(js|jsx)$/,
      exclude: /node_modules/,
      use: {
        loader: 'babel-loader'
      }
    },
    {
      test: /\.css$/,
      use: ['style-loader', 'css-loader']
    },
    {
      test: /\.(png|woff|woff2|eot|ttf|svg)$/,
      loader: 'url-loader?limit=100000'
    }
    ]
  },
  resolve: {
    extensions: ['*', '.js', '.jsx']
  },
  devServer: {
    // historyApiFallback: true,
    port: 3000,
    compress: true,
    open: false
  },
  watchOptions: {
    ignored: ['src/server', 'node_modules/**', 'jest', '__test__']
  },
  plugins: [
    new webpack.EnvironmentPlugin(['REACT_APP_BACKEND_URL', 'REACT_APP_BACKEND_PORT']), // copy .env para for react
    new CleanWebpackPlugin([outputDirectory]),
    new HtmlWebpackPlugin({
      template: './public/index.html'
    }),
    new webpack.ContextReplacementPlugin(/moment[/\\]locale$/, /en/)
    // new BundleAnalyzerPlugin() // plug-in for analyzer bundle size
  ],
  optimization: {
    splitChunks: {
      cacheGroups: {
        commons: {
          test: /[\\/]node_modules[\\/]/,
          name: 'vendors',
          chunks: 'all'
        }
      }
    }
  },
  stats: {
    children: true
  }
};

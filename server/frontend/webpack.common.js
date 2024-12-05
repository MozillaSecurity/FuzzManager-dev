const path = require("path");
const MiniCssExtractPlugin = require("mini-css-extract-plugin");
const { VueLoaderPlugin } = require("vue-loader");

module.exports = {
  mode: "development",
  entry: path.join(__dirname, "src", "main.js"),
  devtool: "inline-source-map",

  output: {
    filename: "[name].js",
    path: path.resolve(__dirname, "dist"),
    publicPath: "",
  },

  plugins: [new MiniCssExtractPlugin(), new VueLoaderPlugin()],

  module: {
    rules: [
      {
        test: /\.vue$/,
        loader: "vue-loader",
        options: {
          compilerOptions: {
            compatConfig: {
              MODE: 3,
            },
          },
        },
      },
      {
        test: /\.css$/,
        use: [MiniCssExtractPlugin.loader, "css-loader"],
      },
      {
        test: /\.js$/,
        exclude: /node_modules/,
        use: {
          loader: "babel-loader",
        },
      },
    ],
  },

  resolve: {
    alias: {
      "@": path.resolve(__dirname, "src"),
      vue: "@vue/compat",
    },
    extensions: [".js", ".vue", ".json"],
  },
};

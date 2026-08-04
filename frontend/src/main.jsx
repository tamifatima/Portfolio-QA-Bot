/*
=============================================================
  main.jsx  —  React Entry Point
=============================================================

PURPOSE:
  This is the entry point for the React application.
  Vite (the build tool) looks for this file first.

  ReactDOM.createRoot() mounts our App component into the
  <div id="root"> element in index.html.

  React.StrictMode wraps the app in development to:
    - Detect side effects
    - Warn about deprecated APIs
    - Double-invoke certain lifecycle methods to find bugs
  (StrictMode has no effect in production builds)
=============================================================
*/

import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App.jsx";

// Find the <div id="root"> in index.html and mount React into it
ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);

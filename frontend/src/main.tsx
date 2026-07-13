import React from "react";
import ReactDOM from "react-dom/client";

import App from "./App";
import "./styles/tokens.css";
import "./styles/components.css";
import "./styles/shell.css";
import "./styles/daily-workflows.css";
import "./styles/app.css";
import "./styles/catalog-workflows.css";
import "./styles/admin-workflows.css";
import "./styles/quality.css";
import "./styles/interaction-primitives.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);

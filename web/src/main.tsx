import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import { installBrowserElectronApi } from './api/installBrowserElectronApi';

// Attach the browser-local preview API before the app mounts. It does not
// overwrite an existing bridge and performs no network or storage access.
installBrowserElectronApi();

const root = ReactDOM.createRoot(document.getElementById('root') as HTMLElement);
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);

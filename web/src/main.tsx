import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import { installBrowserElectronApi } from './api/installBrowserElectronApi';

// IBM Plex fonts (bundled, no runtime network) to match the desktop typography.
import '@fontsource/ibm-plex-sans/300.css';
import '@fontsource/ibm-plex-sans/400.css';
import '@fontsource/ibm-plex-sans/500.css';
import '@fontsource/ibm-plex-sans/600.css';
import '@fontsource/ibm-plex-sans/700.css';
import '@fontsource/ibm-plex-mono/400.css';
import '@fontsource/ibm-plex-mono/500.css';
import '@fontsource/ibm-plex-mono/600.css';

import './styles/theme.css';
import './styles/shell.css';
import './styles/pages.css';
import './styles/chat.css';

// Attach the browser-local preview API before mount. It does not overwrite an
// existing bridge and performs no network or storage access.
installBrowserElectronApi();

const root = ReactDOM.createRoot(document.getElementById('root') as HTMLElement);
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);

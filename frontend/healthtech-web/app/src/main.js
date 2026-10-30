import { app } from './ui/app.js';

// Exposed for local acceptance tests only (read state, no hidden behaviour).
window.__healthtechApp = app;
app.init();

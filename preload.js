const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  onLogMessage: (callback) => ipcRenderer.on('log-message', (_event, value) => callback(value)),
  onStatusUpdate: (callback) => ipcRenderer.on('status-update', (_event, value) => callback(value))
});

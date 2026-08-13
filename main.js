const { app, BrowserWindow, dialog } = require('electron');
const { spawn, execSync } = require('child_process');
const path = require('path');
const http = require('http');

let mainWindow;
let backendProcess;
let frontendProcess;

function checkDependencies() {
  try {
    execSync('node --version', { stdio: 'ignore' });
  } catch (err) {
    dialog.showErrorBox(
      'Missing Dependency',
      'Node.js was not found on your system.\n\nPlease install Node.js (https://nodejs.org) to run this application.'
    );
    return false;
  }

  try {
    execSync('python --version', { stdio: 'ignore' });
  } catch (err) {
    try {
      execSync('py --version', { stdio: 'ignore' }); // fallback for Windows launcher
    } catch (err2) {
      dialog.showErrorBox(
        'Missing Dependency',
        'Python was not found on your system.\n\nPlease install Python (https://www.python.org/downloads/) to run this application. Make sure to check "Add Python to PATH" during installation.'
      );
      return false;
    }
  }

  return true;
}

let splashWindow;

function startServers() {
  const isPackaged = app.isPackaged;
  const basePath = isPackaged ? path.dirname(app.getPath('exe')) : __dirname;
  
  const backendDir = path.join(basePath, 'backend');
  const frontendDir = path.join(basePath, 'frontend');

  const fs = require('fs');

  if (!fs.existsSync(backendDir)) {
    dialog.showErrorBox('Missing Files', `Backend directory not found at: ${backendDir}\nPlease reinstall the app.`);
    app.quit();
    return;
  }
  if (!fs.existsSync(frontendDir)) {
    dialog.showErrorBox('Missing Files', `Frontend directory not found at: ${frontendDir}\nPlease reinstall the app.`);
    app.quit();
    return;
  }

  const sendLog = (source, data) => {
    const text = data.toString().trim();
    if (text && splashWindow && !splashWindow.isDestroyed()) {
      splashWindow.webContents.send('log-message', `[${source}] ${text}`);
    }
  };

  if (splashWindow && !splashWindow.isDestroyed()) splashWindow.webContents.send('status-update', 'Starting Backend and Frontend concurrently (pip install & npm install)...');
  console.log('Starting backend...');
  const pythonCmd = process.platform === 'win32' ? 'python' : 'python3';
  backendProcess = spawn(
    `${pythonCmd} -m pip install -r requirements.txt && ${pythonCmd} -m uvicorn main:app --port 8000`, 
    { cwd: backendDir, shell: true, env: process.env }
  );

  backendProcess.stdout.on('data', (data) => sendLog('Backend', data));
  backendProcess.stderr.on('data', (data) => sendLog('Backend ERR', data));

  console.log('Starting frontend...');
  const npmCmd = process.platform === 'win32' ? 'npm.cmd' : 'npm';
  frontendProcess = spawn(
    `${npmCmd} install && ${npmCmd} run dev`, 
    { cwd: frontendDir, shell: true, env: process.env }
  );

  frontendProcess.stdout.on('data', (data) => sendLog('Frontend', data));
  frontendProcess.stderr.on('data', (data) => sendLog('Frontend ERR', data));
}

function waitForFrontend(url, timeout = 120000) {
  return new Promise((resolve, reject) => {
    const startTime = Date.now();
    const interval = setInterval(() => {
      http.get(url, (res) => {
        if (res.statusCode === 200) {
          clearInterval(interval);
          resolve();
        }
      }).on('error', () => {
        if (Date.now() - startTime > timeout) {
          clearInterval(interval);
          reject(new Error('Timeout waiting for frontend to start'));
        }
      });
    }, 1000);
  });
}

async function createSplashAndMain() {
  splashWindow = new BrowserWindow({
    width: 650,
    height: 450,
    transparent: false,
    frame: false,
    alwaysOnTop: true,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      nodeIntegration: false,
      contextIsolation: true
    }
  });

  await splashWindow.loadFile('splash.html');

  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    show: false,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true
    },
    title: "DataChat AI"
  });

  mainWindow.setMenuBarVisibility(false);

  startServers();

  try {
    if (splashWindow && !splashWindow.isDestroyed()) splashWindow.webContents.send('status-update', 'Waiting for Vite server to boot...');
    await waitForFrontend('http://localhost:5173');
    await mainWindow.loadURL('http://localhost:5173');
    
    if (splashWindow && !splashWindow.isDestroyed()) {
      splashWindow.close();
    }
    mainWindow.show();
  } catch (error) {
    dialog.showErrorBox('Startup Error', 'Failed to start the application server. Check console logs for details.');
    app.quit();
  }

  mainWindow.on('closed', function () {
    mainWindow = null;
  });
}

app.whenReady().then(() => {
  if (!checkDependencies()) {
    app.quit();
    return;
  }

  createSplashAndMain();

  app.on('activate', function () {
    if (mainWindow === null) createSplashAndMain();
  });
});

app.on('window-all-closed', function () {
  // Kill child processes when quitting
  if (process.platform === 'win32') {
    if (backendProcess) execSync(`taskkill /pid ${backendProcess.pid} /T /F`);
    if (frontendProcess) execSync(`taskkill /pid ${frontendProcess.pid} /T /F`);
  } else {
    if (backendProcess) process.kill(-backendProcess.pid);
    if (frontendProcess) process.kill(-frontendProcess.pid);
  }
  
  if (process.platform !== 'darwin') app.quit();
});

app.on('before-quit', () => {
  if (process.platform === 'win32') {
    if (backendProcess) {
      try { execSync(`taskkill /pid ${backendProcess.pid} /T /F`); } catch (e) {}
    }
    if (frontendProcess) {
      try { execSync(`taskkill /pid ${frontendProcess.pid} /T /F`); } catch (e) {}
    }
  } else {
    if (backendProcess) {
      try { process.kill(-backendProcess.pid); } catch (e) {}
    }
    if (frontendProcess) {
      try { process.kill(-frontendProcess.pid); } catch (e) {}
    }
  }
});

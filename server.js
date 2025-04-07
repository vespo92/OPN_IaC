// server.js
const express = require('express');
const { spawn } = require('child_process');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 8000;

// Serve static files
app.use(express.static(path.join(__dirname, 'frontend/dist')));

// Start Django server
const djangoServer = spawn('python', ['OPN_Django/manage.py', 'runserver', '0.0.0.0:8001'], {
  stdio: 'inherit'
});

// Handle proxy to Django
app.use('/api', async (req, res) => {
  try {
    const url = `http://localhost:8001${req.url}`;
    const method = req.method.toLowerCase();
    
    // Get headers from the request
    const headers = {};
    for (const [key, value] of Object.entries(req.headers)) {
      if (key !== 'host') {
        headers[key] = value;
      }
    }
    
    // Get body from the request if it's a POST, PUT, or PATCH
    let body = null;
    if (['post', 'put', 'patch'].includes(method)) {
      const chunks = [];
      for await (const chunk of req) {
        chunks.push(chunk);
      }
      body = Buffer.concat(chunks).toString();
    }
    
    // Make request to Django
    const djangoResponse = await fetch(url, {
      method,
      headers,
      body
    });
    
    // Get response data
    const responseData = await djangoResponse.text();
    
    // Set response status code
    res.status(djangoResponse.status);
    
    // Set response headers
    for (const [key, value] of djangoResponse.headers.entries()) {
      res.setHeader(key, value);
    }
    
    // Send response
    res.send(responseData);
  } catch (error) {
    console.error('Error proxying request to Django:', error);
    res.status(500).send('Internal Server Error');
  }
});

// Catch-all route to return the React app
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'frontend/dist/index.html'));
});

// Start the server
app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});

// Handle process termination
process.on('SIGINT', () => {
  console.log('Shutting down...');
  djangoServer.kill();
  process.exit();
});

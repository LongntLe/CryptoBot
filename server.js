const express = require('express');
const cors = require('cors');
const spawn = require('child_process').spawn;

const app = express();

// Base Api
app.get('/api/teammembers', cors(), (req, res) => {
	const teammembers = [
		{
			id: 1,
			name:'Shugmi Shumunov',
			contribution: 'React Front End & Node Server'
		},
		{
			id: 2,
			name: 'Long Le',
			contribution: 'Bitmex Trading Bot Script in Python'
		},
		{
			id: 3,
			name: 'Suraj Mondem',
			contribution: 'In Progress'
		},
		{
			id: 4,
			name: 'Samuel Oliver Bedu-Annan',
			contribution: 'In Progress'
		}
	];

	res.json(teammembers);
});

const port = 5000;

app.listen(port, () => `Server running on port ${ port }`);

// Interact w/ Python Scripts
const pythonProcess = spawn('python', ['./hello.py', 'Shug']);

pythonProcess.stdout.on('data', (data) => {
	console.log(data);

	let dataStringify = data.toString();

	console.log(dataStringify);
});
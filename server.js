const express = require('express');
const cors = require('cors');
let { PythonShell } = require('python-shell');
// const spawn = require('child_process').spawn;

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
//import {PythonShell} from 'python-shell';
let pyshell = new PythonShell('src/Backend/bot_testnet.py');

pyshell.on('message', function (message) {
  // received a message sent from the Python script (a simple "print" statement)
  console.log(message);
  // sends a message to the Python script via stdin
});
//pyshell.send('Y');

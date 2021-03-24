const express = require('express');
const cors = require('cors');
let { PythonShell } = require('python-shell');

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
PythonShell.run('./src/Backend/bot_testnet.py', null, function (data, err) {
	if (err) console.log(err);
	console.log(data);
});
const express = require('express');
const cors = require('cors');
let { PythonShell } = require('python-shell');
require('dotenv').config();
const { MongoClient } = require('mongodb');

const app = express();
app.use(express.json({ limit: '1mb' }));
app.use(cors());

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
			contribution: 'Bitmex Trading Script in Python and MongoDB setup'
		}
	];

	res.json(teammembers);
});

app.post('/api/formsubmit', cors(), (req, res) => {
	let data = JSON.stringify(req.body.data);

	fs.writeFileSync('./src/Backend/params.json', data);
	res.send('form submitted successfully');
})

const port = 5000;
const username = process.env.MONGO_USERNAME;
const password = process.env.MONGO_PASSWORD;
const mongoURL = process.env.MONGO_CLUSTER_URL;
const uri = `mongodb+srv://${ username }:${ password }@${ mongoURL }`;
const dbName = 'crypto_info';
const collectionName = 'bot_states';
let database,
	collection;

app.listen(port, () => {
	`Server running on port ${ port }`;
});

MongoClient.connect(uri, { useNewUrlParser: true }, (error, client) => {
	if (error) {
		throw error;
	} else {
		database = client.db(dbName);
		collection = database.collection(collectionName);
	}
});

app.get('/api/crypto', cors(), (request, response) => {
	collection.find({}).toArray((error, result) => {
		if (error) {
			return response.status(500).send(error);
		}
		response.send(result);
	});
});

// Interact w/ Python Scripts
PythonShell.run('./src/Backend/bot_testnet.py', null, function (data, err) {
	if (err) console.log(err);
	console.log(data);
});

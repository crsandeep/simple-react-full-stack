const express = require('express');
const os = require('os');
const fs = require('fs');
const app = express();
// TODO: import parser
// const rulesEngineWrapper = require('./utils/rulesEngineWrapper.js')

app.use(express.static('dist'));
app.get('/api/profile_browser', (req, res) => {
	// grab headers from the request object
	const headerStrings = req.rawHeaders

	// save headers and user_agent in an object
	const data = {}
	data.headers = {}

	for (i=0; i<headerStrings.length; i+=2){
		data.headers[headerStrings[i].toLowerCase()] = headerStrings[i+1]
	}
	data.user_agent = data.headers["user-agent"]
	
	// write the user agent to a file
	fs.writeFile('./src/server/input', data.user_agent, 'utf8', function (err) {
		if (err) {
			console.log("An error occured writing user-agent to a file\n", err)
		} else {
			console.log("Succes! User-agent written to input file")
		}
	})

	// write a JSONified string of the data to a file
	const formattedHeaders = JSON.stringify(data)

	// TODO: create file name and save to variable
	// rulesEngineWrapper()

	// write data to json file
	fs.writeFile('./src/server/output.json', formattedHeaders, 'utf8', function (err) {

		if (err) {
			console.log("An error occured saving the headers\n", err)

		// return user-agent from JSON file to verify success
		} else {
			rawFileData = fs.readFileSync('./src/server/output.json')
			fileData = JSON.parse(rawFileData)

			console.log("User-Agent", fileData["user_agent"])
			console.log("Headers Saved Succesfully!")
		}
	})
	
	res.send({ username: os.userInfo().username })
});

app.listen(process.env.PORT || 8080, () => console.log(`Listening on port ${process.env.PORT || 8080}!`));

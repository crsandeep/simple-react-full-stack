const express = require('express');
const os = require('os');
const fs = require('fs');
const app = express();

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

	// write a JSONified string of the data to a file
	const formattedHeaders = JSON.stringify(data)
	fs.writeFile('output.json', formattedHeaders, 'utf8', (err) => {

		if (err) {
			console.log("An error occured saving the headers")
			console.error(err)

		// return user-agent from JSON file to verify success
		} else {
			rawFileData = fs.readFileSync('output.json')
			fileData = JSON.parse(rawFileData)

			console.log("User-Agent", fileData["user_agent"])
			console.log("Headers Saved Succesfully!")
		}
	})
	
	res.send({ username: os.userInfo().username })
});

app.listen(process.env.PORT || 8080, () => console.log(`Listening on port ${process.env.PORT || 8080}!`));

const express = require('express');
const os = require('os');
const fs = require('fs')
const app = express();

app.use(express.static('dist'));
app.get('/api/sendHeader', (req, res) => {
	// grab headers from the request object
	const headerStrings = req.rawHeaders
	const headers = {}

	// save headers in an object
	for (i=0; i<headerStrings.length; i+=2){
		headers[headerStrings[i].toLowerCase()] = headerStrings[i+1]
	}

	// write a JSONified string of the headers to a file
	const formattedHeaders = JSON.stringify(headers)
	fs.writeFile('output.json', formattedHeaders, 'utf8', (err) => {
		
		if (err) {
			console.log("An error occured saving the headers")
			console.error(err)

		// return user-agent from JSON file to verify success
		} else {
			rawFileData = fs.readFileSync('output.json')
			fileData = JSON.parse(rawFileData)

			console.log("User-Agent", fileData["user-agent"])
			console.log("Headers Saved Succesfully!")
		}
	})
	
	res.send({ username: os.userInfo().username })
});

app.listen(process.env.PORT || 8080, () => console.log(`Listening on port ${process.env.PORT || 8080}!`));

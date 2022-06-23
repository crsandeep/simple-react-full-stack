const express = require('express');
const os = require('os');
const fs = require('fs');
// const test = require('./utils/test');
const app = express();
// variables and requirements for rules engine
let inputPath = '/Users/kmantinaos/Documents/GitHub/simple-react-full-stack/src/server/input.csv'
let outputPath = '/Users/kmantinaos/Documents/GitHub/simple-react-full-stack/src/server/engineOutput.json'

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
	fs.writeFile('./src/server/input.csv', data.user_agent, 'utf8', function (err) {
		if (err) {
			console.log("An error occured writing user-agent to a file\n", err)
		} else {
			console.log("Succes! User-agent written to input file")
		}
	})

	// write a JSONified string of the data to a file
	const formattedHeaders = JSON.stringify(data)

	// create file name and save to variable
	
	// function from rulesEngineWrapper
	const passInputFileToRulesEngine = function () {
		return new Promise(function (resolve, reject) {
			var exec = require('child_process').exec;

			//syntax and how to use rules engine cli: https://confluence.integralads.com/pages/viewpage.action?spaceKey=EN&title=Running+Rules+Engine+CLI

			var javaCommandStr = 'java -cp rules-engine-2.jar com.beehive.analytics.App ' + 
			'-inputFileName ' + inputPath + 
			' -outputFileName ' + outputPath + 
			' -parseUserAgent true'

			exec(javaCommandStr, {cwd: '/Users/kmantinaos/Documents/GitHub/simple-react-full-stack/src/server'}, function (err, a, b) {
				if (err) {
					console.log('error passInputFileToRulesEngine()', err);
					reject();
				} else {

					resolve()
				}
			});
		})
	};

 	passInputFileToRulesEngine()

	// write data to json file
	fs.writeFile('./src/server/olderOutput.json', formattedHeaders, 'utf8', function (err) {

		if (err) {
			console.log("An error occured saving the headers\n", err)

		// return user-agent from JSON file to verify success
		} else {
			rawFileData = fs.readFileSync('./src/server/olderOutput.json')
			fileData = JSON.parse(rawFileData)

			console.log("User-Agent", fileData["user_agent"])
			console.log("Headers Saved Succesfully!")
		}
	})
	
	res.send({ username: os.userInfo().username })
});

app.listen(process.env.PORT || 8080, () => console.log(`Listening on port ${process.env.PORT || 8080}!`));

/*
Chrome: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36

Safari: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.5 Safari/605.1.15

Firefox: Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:101.0) Gecko/20100101 Firefox/101.0

*/
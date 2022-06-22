const express = require('express');
const os = require('os');
const fs = require('fs');
const test = require('./utils/test');
const app = express();
// variables and requirements for rules engine
const path = require('path')
const PATH_TO_RULES_ENGINE = path.resolve('./rules-engine-2.jar')

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

	// create file name and save to variable
	// TODO: resarch how to get absolute paths in Node
	let inputPath = path.resolve('./input')
	let outputPath = ('./engineOutput.json')
	// function from rulesEngineWrapper
	const passInputFileToRulesEngine = function () {
		return new Promise(function (resolve, reject) {
			var exec = require('child_process').exec;

			//syntax and how to use rules engine cli: https://confluence.integralads.com/pages/viewpage.action?spaceKey=EN&title=Running+Rules+Engine+CLI

			var javaCommandStr = 'java -cp ' + PATH_TO_RULES_ENGINE + ' com.beehive.analytics.App ' +

				// '-c ' + getConfigFolder() +
				// ' ' +
				'-i ' + inputPath +
				' ' +
				'-o ' + outputPath;

			exec(javaCommandStr, function (err, a, b) {
				if (err) {
					console.log('error passInputFileToRulesEngine()', err);
					reject();
				} else {

					resolve()
				}
			});
		})
	};

	const testOutput = passInputFileToRulesEngine()
	console.log("test engine output", testOutput)
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

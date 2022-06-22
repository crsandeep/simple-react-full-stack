/*
Chrome: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36

Safari: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.5 Safari/605.1.15

Firefox: Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:101.0) Gecko/20100101 Firefox/101.0

*/

module.exports = (function () {
    const fs = require('fs');

    if (typeof Promise !== 'function') {
        try {
            const Promise = require('promise');
        } catch (e) {
            console.log("Error with promise module", e);
        }
    }
    if (typeof Promise.denodeify !== 'function') {
        Promise.denodeify = function (fn, argumentCount) {
            argumentCount = argumentCount || Infinity;
            return function () {
                var self = this;
                var args = Array.prototype.slice.call(arguments);
                return new Promise(function (resolve, reject) {
                    while (args.length && args.length > argumentCount) {
                        args.pop();
                    }
                    args.push(function (err, res) {
                        if (err) reject(err);
                        else resolve(res);
                    })
                    var res = fn.apply(self, args);
                    if (res &&
                        (
                            typeof res === 'object' ||
                            typeof res === 'function'
                        ) &&
                        typeof res.then === 'function'
                    ) {
                        resolve(res);
                    }
                })
            }
        }
    }

    var writeFile = Promise.denodeify(fs.writeFile);
    var readFile = Promise.denodeify(fs.readFile);

    const path = require('path');
    const dirString = path.dirname(fs.realpathSync(__filename));

    const PATH_TO_RULES_ENGINE = path.resolve(__dirname, '..', '..', '..') + '/rules-engine.jar';

    const utils = require(dirString + '/../utils.js');

    var getRulesResult = function (impressionObj) {

        var getInputFilePath = function () {
            return process.cwd() + '/tmp/' + 'rules-engine-input-' + impressionObj.impressionId + '.csv'
        };

        var getOutputFilePath = function () {
            return process.cwd() + '/tmp/' + 'rules-engine-output-' + impressionObj.impressionId + '.csv'
        };

        var getConfigFolder = function () {
            return path.resolve(__dirname, '..', '..', '..') + '/swarm-js-config/conf/';
        };

        var createInputFile = function () {
            return new Promise(function (resolve, reject) {
                var FOUR_CHARACTER_SPACE = '    ';
                var logContent = impressionObj.headerUserAgent +
                    FOUR_CHARACTER_SPACE +
                    '{' +
                    'mvn:' + utils.base64Encode(impressionObj.mvn) + ',' +
                    'fsc:' + impressionObj.scaVersion + 'v' + impressionObj.fsc + ',' +
                    'sd:' + utils.base64Encode(impressionObj.scaVersion + 'v' + impressionObj.sd) + ',' +
                    'no:' + utils.base64Encode(impressionObj.scaVersion + 'v' + impressionObj.no) + ',' +
                    'asp:' + impressionObj.asp +
                    '}';

                console.log('* RulesEngine Input:', logContent);

                writeFile(getInputFilePath(), logContent, 'utf8')
                    .then(function () {
                        resolve();
                    });
            })
        };

        var passInputFileToRulesEngine = function () {
            return new Promise(function (resolve, reject) {
                var exec = require('child_process').exec;

                //syntax and how to use rules engine cli: https://confluence.integralads.com/pages/viewpage.action?spaceKey=EN&title=Running+Rules+Engine+CLI

                var javaCommandStr = 'java -cp ' + PATH_TO_RULES_ENGINE + ' com.beehive.analytics.App ' +

                    '-c ' + getConfigFolder() +
                    ' ' +
                    '-i ' + getInputFilePath() +
                    ' ' +
                    '-o ' + getOutputFilePath();

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

        var cleanUpLogs = function () {
            fs.unlinkSync(getInputFilePath());
            fs.unlinkSync(getOutputFilePath());
        };

        return new Promise(function (resolve, reject) {

            createInputFile()

                .then(passInputFileToRulesEngine, reject)

                .then(function () {
                    return readFile(getOutputFilePath(), 'utf8')
                }, reject)

                .then(function (dataFromOutputFile) {
                    cleanUpLogs();
                    resolve(dataFromOutputFile);
                }, reject)

        });
    };

    return {
        getRulesResult: getRulesResult
    }

})();
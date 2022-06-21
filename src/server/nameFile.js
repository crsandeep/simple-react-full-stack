/*
Chrome: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36

Safari: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.5 Safari/605.1.15

Firefox: Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:101.0) Gecko/20100101 Firefox/101.0

*/

module.exports.nameFile = (user_agent) => {
    console.log("import success!")
    // init browserName
    let broswerName
    // check for name (chrome must go before safari)
        // 1. Chrome 
        if (user_agent.includes("Chrome")) {
            broswerName = 'chrome'
        // 2. Firefox
        } else if (user_agent.includes("Firefox")){
            broswerName = 'firefox'
        // 3. Safari
        } else if (user_agent.includes("Safari")) {
            broswerName = 'safari'
        // other cases
        } else {
            return "Unkown Browser"
        }

    // grab version number from string
        // ${browserName}/{version number}.00.00
        // split string
        // find string with broswer name
        // Begin after the slash: idx of '/' + 1 
        // end before the first '.'

    // return 'broswerName.versionNumber.json'
}
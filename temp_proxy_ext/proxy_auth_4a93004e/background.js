
        function callbackFn(details) {
            return {
                authCredentials: {
                    username: "scraperapi.session_number=4144033",
                    password: "1b60ef7bf31cd2410a773798a15891dd"
                }
            };
        }

        chrome.webRequest.onAuthRequired.addListener(
            callbackFn,
            {urls: ["<all_urls>"]},
            ['blocking']
        );
        
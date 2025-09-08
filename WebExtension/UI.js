function addFactCheckButton() {
    const tweets = document.querySelectorAll('article');
    tweets.forEach(tweet => {
        if (!tweet.querySelector('.chex-button')) {
            const button = document.createElement('button');
            button.innerText = 'CheX';
            button.style.cssText = "transition: all 0.1s ease; margin-top: 8px; padding: 4px 10px; border: white 1px solid; border-radius: 5px; background-color: black; cursor: pointer; width: 40px; height: 30px; font-size: 12px;display: flex; align-items: center; justify-content: center; color: white;";
            button.classList.add('chex-button');
            button.addEventListener('click', () => {
                const textElements = tweet.querySelectorAll('div[lang]');
                const tweetText = textElements ? Array.from(textElements).map(el => el.innerText).join(' ') : '';
                console.log('Fact-checking tweet:', tweetText);
               fetch('http://127.0.0.1:8000/factcheck', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ claim: tweetText })
                })
                .then(response => response.json())
                .then(data => {
                    // ✅ Find the main tweet text block
                    const textBlock = tweet.querySelector('div[lang]');
                    if (textBlock) {
                        let factCheckEl = textBlock.parentNode.querySelector('.chex-result');
                        if (!factCheckEl) {
                            factCheckEl = document.createElement('div');
                            factCheckEl.className = 'chex-result';
                            factCheckEl.style.cssText = "margin-top: 6px; font-size: 13px; color: #1d9bf0; font-style: italic;";
                            textBlock.parentNode.appendChild(factCheckEl);
                        }

                        // Insert result under tweet text
                        let sources = data.sources && data.sources.length 
                            ? "\nSources: " + data.sources.join(", ") 
                            : "";

                        factCheckEl.innerText = `✅ Verdict: ${data.verdict}\n💡 ${data.response}${sources}`;
                    }
                })
            });
            button.addEventListener('mouseenter', () => {
                button.style.backgroundColor = '#c0d9e8ff';
                button.style.color = 'black';
            });
            button.addEventListener('mouseleave', () => {
                button.style.backgroundColor = 'black';
                button.style.color = 'white';
            });
            tweet.appendChild(button);
        }
    });
}


const observer = new MutationObserver(addFactCheckButton);
observer.observe(document.body, { childList: true, subtree: true });
addFactCheckButton();

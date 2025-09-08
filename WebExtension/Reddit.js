function addFactCheckButton() {
    const posts = document.querySelectorAll('div[data-testid="post-container"]');
    posts.forEach(post => {
        if (!post.querySelector('.chex-button')) {
            const button = document.createElement('button');
            button.innerText = 'CheX';
            button.style.cssText = `
                transition: all 0.1s ease; 
                margin-top: 8px; 
                padding: 4px 10px; 
                border: white 1px solid; 
                border-radius: 5px; 
                background-color: black; 
                cursor: pointer; 
                width: 40px; 
                height: 30px; 
                font-size: 12px;
                display: flex; 
                align-items: center; 
                justify-content: center; 
                color: white;
            `;
            button.classList.add('chex-button');

            button.addEventListener('click', () => {
                // ✅ Collect text: title + body (if any)
                const title = post.querySelector('h3')?.innerText || '';
                const body = Array.from(post.querySelectorAll('p')).map(el => el.innerText).join(' ');
                const postText = `${title} ${body}`.trim();

                console.log('Fact-checking post:', postText);

                fetch('http://127.0.0.1:8000/factcheck', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ claim: postText })
                })
                .then(response => response.json())
                .then(data => {
                    // ✅ Find where to insert result
                    let textBlock = post.querySelector('div[data-testid="post-content"]');
                    if (textBlock) {
                        let factCheckEl = textBlock.querySelector('.chex-result');
                        if (!factCheckEl) {
                            factCheckEl = document.createElement('div');
                            factCheckEl.className = 'chex-result';
                            factCheckEl.style.cssText = "margin-top: 6px; font-size: 13px; color: #1d9bf0; font-style: italic;";
                            textBlock.appendChild(factCheckEl);
                        }

                        let sources = data.sources && data.sources.length 
                            ? "\nSources: " + data.sources.join(", ") 
                            : "";

                        factCheckEl.innerText = `✅ Verdict: ${data.verdict}\n💡 ${data.response}${sources}`;
                    }
                });
            });

            button.addEventListener('mouseenter', () => {
                button.style.backgroundColor = '#c0d9e8ff';
                button.style.color = 'black';
            });
            button.addEventListener('mouseleave', () => {
                button.style.backgroundColor = 'black';
                button.style.color = 'white';
            });

            // ✅ Insert button at the bottom of the post actions (upvote/comment bar)
            const actionBar = post.querySelector('div[data-testid="post-container"] div[data-testid="post-content"]');
            if (actionBar) {
                actionBar.appendChild(button);
            } else {
                post.appendChild(button);
            }
        }
    });
}

// Watch for new Reddit posts being loaded
const observer = new MutationObserver(addFactCheckButton);
observer.observe(document.body, { childList: true, subtree: true });
addFactCheckButton();

document.addEventListener('DOMContentLoaded', () => {
    // Find all <pre> tags on the page
    const codeBlocks = document.querySelectorAll('pre');

    codeBlocks.forEach(block => {
        // Create the copy button
        const button = document.createElement('button');
        button.className = 'copy-button';
        button.textContent = 'Copy';

        // Add the button to the <pre> block
        block.appendChild(button);

        // Add the click event listener
        button.addEventListener('click', () => {
            // Find the <code> element inside the <pre> block
            const code = block.querySelector('code');
            if (code) {
                // Copy the text content to the clipboard
                navigator.clipboard.writeText(code.textContent).then(() => {
                    // Provide visual feedback
                    button.textContent = 'Copied!';
                    button.classList.add('copied');

                    // Reset the button text after 2 seconds
                    setTimeout(() => {
                        button.textContent = 'Copy';
                        button.classList.remove('copied');
                    }, 2000);
                }).catch(err => {
                    console.error('Failed to copy text: ', err);
                });
            }
        });
    });
});
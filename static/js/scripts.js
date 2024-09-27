function sendData() {
    const userInput = document.getElementById('user-input').value;
    fetch('/data', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ userInput })
document.getElementById('scrape-btn').addEventListener('click', function () {
    const progressDiv = document.getElementById('scrape-progress');
    progressDiv.innerHTML = ''; // Clear previous progress

    fetch('/scrape', {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            progressDiv.innerHTML = `<p class="error">${data.error}</p>`;
        } else {
            data.progress.forEach(step => {
                const stepElement = document.createElement('p');
                stepElement.textContent = step;
                progressDiv.appendChild(stepElement);
            });
            // Show prediction form after scraping
            document.getElementById('prediction-form').classList.remove('hidden');
        }
    })
    .catch(error => {
        progressDiv.innerHTML = `<p class="error">An unexpected error occurred: ${error.message}</p>`;
    });
});

document.getElementById('prediction-form').addEventListener('submit', function (e) {
    e.preventDefault();
    
    const event = document.getElementById('event').value;
    const actual = document.getElementById('actual').value;
    const forecast = document.getElementById('forecast').value;
    const previous = document.getElementById('previous').value;

    fetch('/predict', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ event, actual, forecast, previous })
    })
    .then(response => response.json())
    .then(data => {
        document.getElementById('predicted-difference').textContent = data.predicted_difference;
        document.getElementById('outcome').textContent = data.outcome;
        document.getElementById('result').classList.remove('hidden');
    })
    .catch(error => console.error('Error:', error));
});

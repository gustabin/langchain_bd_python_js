document.getElementById('submit').addEventListener('click', function () {
    const query = document.getElementById('query').value;
    fetch('/langchain-db', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query: query }),
    })
        .then(response => {
            if (!response.ok) {
                throw new Error('Error en la consulta');
            }
            return response.json();
        })
        .then(data => {
            document.getElementById('result').textContent = data.result;
        })
        .catch(error => {
            document.getElementById('result').textContent = 'Error: ' + error.message;
        });
});

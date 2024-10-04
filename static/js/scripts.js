// Agrega un evento de escucha al botón "submit"
document.getElementById('submit').addEventListener('click', function () {
    // Obtiene el valor de la consulta ingresada por el usuario en el textarea
    const query = document.getElementById('query').value;

    // Realiza una solicitud POST al endpoint '/langchain-db' con la consulta
    fetch('/langchain-db', {
        method: 'POST', // Especifica el método HTTP como POST
        headers: {
            'Content-Type': 'application/json', // Define el tipo de contenido como JSON
        },
        // Convierte el objeto con la consulta en una cadena JSON para enviarlo en el cuerpo de la solicitud
        body: JSON.stringify({ query: query }),
    })
        .then(response => {
            // Verifica si la respuesta fue exitosa (código de estado 2xx)
            if (!response.ok) {
                // Si no es exitosa, lanza un error con un mensaje
                throw new Error('Error en la consulta');
            }
            // Convierte la respuesta en formato JSON y la devuelve
            return response.json();
        })
        .then(data => {
            // Muestra el resultado de la consulta en el elemento 'result'
            document.getElementById('result').textContent = data.result;
        })
        .catch(error => {
            // Captura cualquier error que ocurra durante el proceso
            // Muestra el mensaje de error en el elemento 'result'
            document.getElementById('result').textContent = 'Error: ' + error.message;
        });
});

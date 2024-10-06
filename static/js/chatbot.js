// chatbot.js
(function () {
    // Cargar el script del chatbot
    const apiKey = document.currentScript.getAttribute('data-api-key');
    // Verifica que se haya proporcionado una API key
    if (!apiKey) {
        console.error('API key is missing. Please provide a valid API key.');
        return;
    }

    // Crear el contenedor del chatbot
    const chatContainer = document.createElement('div');
    chatContainer.id = 'chatbot-container';
    chatContainer.style.position = 'absolute';  // Cambiado a absolute para controlar mejor la posición
    chatContainer.style.bottom = '60px'; // Ajusta esto para la posición vertical
    chatContainer.style.right = '10px'; // Para que aparezca en la esquina inferior derecha
    chatContainer.style.width = '300px'; // Ancho clásico de un chatbot
    chatContainer.style.border = '1px solid #ccc';
    chatContainer.style.borderRadius = '10px';
    chatContainer.style.boxShadow = '0 0 10px rgba(0, 0, 0, 0.1)';
    chatContainer.style.display = 'none'; // Inicialmente oculto

    // Crear la estructura interna del chatbot
    const chatContent = document.createElement('div');
    chatContent.innerHTML = '<h3>Chatbot</h3><p>¡Hola! Estoy aquí para ayudarte.</p>';
    chatContent.style.padding = '10px';
    chatContainer.appendChild(chatContent);

    // Contenedor para la conversación
    const chatOutput = document.createElement('div');
    chatOutput.id = 'chat-output';
    chatOutput.style.height = '200px'; // Establecer una altura para el área de chat
    chatOutput.style.overflowY = 'auto'; // Hacer que sea desplazable si es necesario
    chatOutput.style.padding = '5px';
    chatContainer.appendChild(chatOutput);

    // Campo de entrada del usuario
    const userInput = document.createElement('input');
    userInput.type = 'text';
    userInput.id = 'user-input';
    userInput.placeholder = 'Escribe tu consulta aquí...';
    userInput.style.marginTop = '10px'; // Agrega un margen superior
    userInput.style.marginLeft = '10px'; // Agrega un margen izquierdo
    userInput.style.marginRight = '10px'; // Agrega un margen derecho
    userInput.style.height = '40px'; // Ajusta la altura del campo de entrada
    userInput.style.width = 'calc(100% - 42px)'; // Ajusta el ancho para considerar los márgenes
    chatContainer.appendChild(userInput);

    // Botón para enviar el mensaje
    const sendButton = document.createElement('button');
    sendButton.innerText = 'Enviar';
    sendButton.id = 'send-button';
    sendButton.style.marginTop = '10px'; // Agrega un margen superior para separar del input
    sendButton.style.marginLeft = '10px'; // Agrega un margen izquierdo
    sendButton.style.marginBottom = '10px'; // Agrega un margen inferior
    chatContainer.appendChild(sendButton);

    // Agregar el contenedor del chatbot al cuerpo del documento
    document.body.appendChild(chatContainer);

    // Mostrar/ocultar el chatbot al hacer clic en el botón
    const openButton = document.createElement('button');
    openButton.innerText = '💬'; // Cambiado para mostrar el emoji
    openButton.style.position = 'absolute';
    openButton.style.bottom = '10px';
    openButton.style.right = '30px'; // Ajusta este valor para mover el emoji hacia la izquierda
    openButton.style.width = '50px'; // Ancho del botón
    openButton.style.height = '50px'; // Altura del botón
    openButton.style.borderRadius = '50%'; // Hacer el botón circular
    openButton.style.border = 'none';
    openButton.style.backgroundColor = 'rgb(0, 123, 255)'; // Color de fondo
    openButton.style.color = 'rgb(255, 255, 255)'; // Color del texto
    openButton.style.cursor = 'pointer';
    openButton.style.fontSize = '24px'; // Cambiado para aumentar el tamaño del emoji
    openButton.style.paddingRight = '10px'; // Agregar espacio a la derecha del emoji
    openButton.style.paddingLeft = '10px'; // Agregar espacio a la izquierda del emoji
    openButton.style.paddingTop = '8px'; // Agregar espacio en la parte superior

    openButton.onclick = function () {
        if (chatContainer.style.display === 'none') {
            chatContainer.style.display = 'block';
        } else {
            chatContainer.style.display = 'none';
        }
    };

    document.body.appendChild(openButton);

    // Lógica para enviar el mensaje y obtener la respuesta
    sendButton.onclick = async () => {
        const message = userInput.value;
        chatOutput.innerHTML += `<div><strong>Tú:</strong> ${message}</div>`;
        userInput.value = ''; // Limpia el campo de entrada

        // Enviar el mensaje al servidor
        // const response = await fetch('http://127.0.0.1:5010/chat', {
        const response = await fetch('https://echodb-rlca.onrender.com/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message }),
        });

        const data = await response.json();
        chatOutput.innerHTML += `<div><strong>Chatbot:</strong> ${data.response}</div>`;
    };

})();

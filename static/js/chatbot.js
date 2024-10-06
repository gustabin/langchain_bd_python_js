// chatbot.js
(function () {
    const apiKey = document.currentScript.getAttribute('data-api-key');

    if (!apiKey) {
        console.error('API key is missing. Please provide a valid API key.');
        return;
    }

    const chatContainer = document.createElement('div');
    chatContainer.id = 'chatbot-container';
    chatContainer.style.position = 'absolute';
    chatContainer.style.bottom = '60px';
    chatContainer.style.right = '10px';
    chatContainer.style.width = '300px';
    chatContainer.style.border = '1px solid #ccc';
    chatContainer.style.borderRadius = '10px';
    chatContainer.style.boxShadow = '0 0 10px rgba(0, 0, 0, 0.1)';
    chatContainer.style.display = 'none';

    const chatContent = document.createElement('div');
    chatContent.innerHTML = '<h3>Chatbot</h3><p>¡Hola! Estoy aquí para ayudarte.</p>';
    chatContent.style.padding = '10px';
    chatContainer.appendChild(chatContent);

    const chatOutput = document.createElement('div');
    chatOutput.id = 'chat-output';
    chatOutput.style.height = '200px';
    chatOutput.style.overflowY = 'auto';
    chatOutput.style.padding = '5px';
    chatContainer.appendChild(chatOutput);

    const userInput = document.createElement('input');
    userInput.type = 'text';
    userInput.id = 'user-input';
    userInput.placeholder = 'Escribe tu consulta aquí...';
    userInput.style.marginTop = '10px';
    userInput.style.marginLeft = '10px';
    userInput.style.marginRight = '10px';
    userInput.style.height = '40px';
    userInput.style.width = 'calc(100% - 42px)';
    chatContainer.appendChild(userInput);

    const sendButton = document.createElement('button');
    sendButton.innerText = 'Enviar';
    sendButton.id = 'send-button';
    sendButton.style.marginTop = '10px';
    sendButton.style.marginLeft = '10px';
    sendButton.style.marginBottom = '10px';
    sendButton.disabled = true; // El botón empieza deshabilitado
    chatContainer.appendChild(sendButton);

    document.body.appendChild(chatContainer);

    const openButton = document.createElement('button');
    openButton.innerText = '💬';
    openButton.style.position = 'absolute';
    openButton.style.bottom = '10px';
    openButton.style.right = '30px';
    openButton.style.width = '50px';
    openButton.style.height = '50px';
    openButton.style.borderRadius = '50%';
    openButton.style.border = 'none';
    openButton.style.backgroundColor = 'rgb(0, 123, 255)';
    openButton.style.color = 'rgb(255, 255, 255)';
    openButton.style.cursor = 'pointer';
    openButton.style.fontSize = '24px';
    openButton.style.paddingRight = '10px';
    openButton.style.paddingLeft = '10px';
    openButton.style.paddingTop = '8px';

    openButton.onclick = function () {
        if (chatContainer.style.display === 'none') {
            chatContainer.style.display = 'block';
        } else {
            chatContainer.style.display = 'none';
        }
    };

    document.body.appendChild(openButton);

    // Habilitar/deshabilitar el botón según el contenido del input
    userInput.addEventListener('input', function () {
        if (userInput.value.trim() === '') {
            sendButton.disabled = true;
        } else {
            sendButton.disabled = false;
        }
    });

    // Lógica para enviar el mensaje y obtener la respuesta
    sendButton.onclick = async () => {
        const message = userInput.value.trim(); // Eliminar espacios innecesarios

        if (!message) {
            console.error('No message provided');
            return;
        }

        try {
            const response = await fetch('http://127.0.0.1:5010/chat', {
                // const response = await fetch('https://echodb-rlca.onrender.com/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${apiKey}`
                },
                body: JSON.stringify({ message })
            });

            const data = await response.json();

            if (data.error) {
                console.error('Error:', data.error);
                chatOutput.innerHTML += `<p>Error: ${data.error}</p>`;
            } else {
                chatOutput.innerHTML += `<p>${data.response}</p>`;
                chatOutput.scrollTop = chatOutput.scrollHeight; // Auto scroll to the bottom
            }

            // Limpiar el campo de entrada y deshabilitar el botón
            userInput.value = '';
            sendButton.disabled = true;

        } catch (error) {
            console.error('Error fetching response:', error);
            chatOutput.innerHTML += `<p>Error: ${error.message}</p>`;
        }
    };
})();

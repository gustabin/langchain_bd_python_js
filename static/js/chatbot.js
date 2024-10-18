(function () {
    const apiKey = document.currentScript.getAttribute('data-api-key');

    if (!apiKey) {
        console.error('API key is missing. Please provide a valid API key.');
        return;
    }

    // Validar API key antes de mostrar el chatbot
    async function validateApiKey(apiKey) {
        try {
            const response = await fetch('http://127.0.0.1:5010/validate-api-key', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ api_key: apiKey })
            });

            const data = await response.json();

            if (data.access) {
                // Si la API key es válida, habilitar el chatbot
                console.log('Bienvenido, ' + data.user.name);
                // Mostrar el chatbot
                chatContainer.style.display = 'block';
            } else {
                console.error('API key inválida: ' + data.message);
            }
        } catch (error) {
            console.error('Error al validar la API key:', error);
        }
    }

    // Crear el contenedor del chatbot (oculto inicialmente)
    const chatContainer = document.createElement('div');
    chatContainer.id = 'chatbot-container';
    chatContainer.style.position = 'absolute';
    chatContainer.style.bottom = '60px';
    chatContainer.style.right = '10px';
    chatContainer.style.width = '300px';
    chatContainer.style.border = '1px solid #ccc';
    chatContainer.style.borderRadius = '10px';
    chatContainer.style.boxShadow = '0 0 10px rgba(0, 0, 0, 0.1)';
    chatContainer.style.display = 'none'; // Inicialmente oculto

    const chatContent = document.createElement('div');
    chatContent.innerHTML = '<strong>🤖Flashbot</strong><br>¡Hola! Estoy aquí para ayudarte.';
    chatContent.style.padding = '10px';
    chatContent.style.backgroundColor = 'azure';
    chatContent.style.borderTopLeftRadius = '10px';
    chatContent.style.borderTopRightRadius = '10px';
    chatContainer.appendChild(chatContent);

    const chatOutput = document.createElement('div');
    chatOutput.id = 'chat-output';
    chatOutput.style.height = '200px';
    chatOutput.style.overflowY = 'auto';
    chatOutput.style.padding = '5px';
    chatContainer.appendChild(chatOutput);

    const userInput = document.createElement('textarea');
    userInput.id = 'user-input';
    userInput.placeholder = 'Escribe tu consulta aquí...';
    userInput.style.marginTop = '10px';
    userInput.style.marginLeft = '10px';
    userInput.style.marginRight = '10px';
    userInput.style.height = '80px';
    userInput.style.width = 'calc(100% - 42px)';
    chatContainer.appendChild(userInput);

    const sendButton = document.createElement('button');
    sendButton.innerText = 'Enviar';
    sendButton.id = 'send-button';
    sendButton.style.marginTop = '10px';
    sendButton.style.marginLeft = '10px';
    sendButton.style.marginBottom = '10px';
    sendButton.style.backgroundColor = 'dodgerblue';
    sendButton.disabled = true; // El botón empieza deshabilitado
    chatContainer.appendChild(sendButton);

    // Crear el loader (oculto inicialmente)
    const loader = document.createElement('img');
    loader.id = 'loader';
    loader.src = 'https://echodb-rlca.onrender.com/static/img/barra.gif'; // Ruta del GIF
    loader.style.marginLeft = '10px';
    loader.style.display = 'none'; // Oculto inicialmente
    loader.style.width = '125px'; // Ajustar tamaño si es necesario
    chatContainer.appendChild(loader);

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

    openButton.onclick = function () {
        chatContainer.style.display = chatContainer.style.display === 'none' ? 'block' : 'none';
    };

    document.body.appendChild(openButton);

    // Habilitar el envío al presionar "Enter"
    userInput.addEventListener('keydown', function (event) {
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault();
            if (!sendButton.disabled) sendButton.click();
        }
    });

    // Habilitar/deshabilitar el botón según el input
    userInput.addEventListener('input', function () {
        sendButton.disabled = userInput.value.trim() === '';
    });

    // Lógica para enviar el mensaje
    sendButton.onclick = async () => {
        const message = userInput.value.trim();
        if (!message) return;

        // Mostrar loader
        loader.style.display = 'inline';

        try {
            const response = await fetch('http://127.0.0.1:5010/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${apiKey}`
                },
                body: JSON.stringify({ message })
            });

            const data = await response.json();
            if (data.error) {
                console.error(data.error);
                chatOutput.innerHTML += `<p><strong>Error:</strong> ${data.error}</p>`;
            } else {
                chatOutput.innerHTML += `<strong>${data.question}</strong><br>${data.response}<p></p>`;
                chatOutput.scrollTop = chatOutput.scrollHeight;
            }

            // Limpiar input
            userInput.value = '';
            sendButton.disabled = true;

        } catch (error) {
            console.error(error);
            chatOutput.innerHTML += `<p><strong>Error:</strong> ${error.message}</p>`;
        } finally {
            loader.style.display = 'none'; // Ocultar loader
        }
    };

    // Validar la API key al cargar el script
    validateApiKey(apiKey);
})();

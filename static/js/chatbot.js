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
                // const response = await fetch('https://echodb-rlca.onrender.com/validate-api-key', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ api_key: apiKey })
            });

            const data = await response.json();

            if (data.access) {
                // Mostrar el chatbot si el acceso es válido
                // chatContainer.style.display = 'block';
                console.log('Bienvenido, ' + data.user.name);
                // console.log('Todo el registro, ' + JSON.stringify(data));
                // console.log('email, ' + data.user.email);
                // console.log('website, ' + data.user.website);
                // console.log('password, ' + data.user.password);
                // console.log('hostDB, ' + data.user.hostDB);
                // console.log('userDB, ' + data.user.userDB);
                // console.log('passwordDB, ' + data.user.passwordDB);
                // console.log('databaseDB, ' + data.user.databaseDB);
                // console.log('db_type, ' + data.user.db_type);
                // console.log('port, ' + data.user.port);
                // console.log('ssl_enabled, ' + data.user.ssl_enabled);
                // console.log('charset, ' + data.user.charset);
            } else {
                console.error(data.message);
            }
        } catch (error) {
            console.error('Error validating API key:', error);
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
    chatContent.style.borderTopLeftRadius = '10px'; // Asegurar que el contenido también tenga bordes redondeados en la parte superior
    chatContent.style.borderTopRightRadius = '10px'; // Asegurar que el contenido también tenga bordes redondeados en la parte superior
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

    // // Crear el loader (oculto inicialmente)
    // const loader = document.createElement('span');
    // loader.id = 'loader';
    // loader.style.marginLeft = '10px';
    // loader.style.display = 'none'; // Oculto inicialmente
    // loader.innerHTML = '⏳'; // O puedes usar un ícono de carga personalizado (puede ser un GIF o cualquier símbolo)
    // chatContainer.appendChild(loader);

    // Crear el loader (oculto inicialmente)
    const loader = document.createElement('img');
    loader.id = 'loader';
    loader.src = 'https://echodb-rlca.onrender.com/static/img/barra.gif'; // Asegúrate de ajustar la ruta correcta
    loader.style.marginLeft = '10px';
    loader.style.display = 'none'; // Oculto inicialmente
    loader.style.width = '125px';   // Puedes ajustar el tamaño si es necesario
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

    // Habilitar el envío al presionar la tecla "Enter"
    userInput.addEventListener('keydown', function (event) {
        // Si se presiona solo "Enter" (sin Shift), se envía el mensaje
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault(); // Evitar que se agregue un salto de línea
            if (!sendButton.disabled) {  // Solo hacer clic si el botón no está deshabilitado
                sendButton.click(); // Simula un clic en el botón de "Enviar"
            }
        }
        // Si se presiona "Shift + Enter", se permite el salto de línea
        else if (event.key === 'Enter' && event.shiftKey) {
            // No hacer nada, por lo que el salto de línea se permite
            return;
        }
    });

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

        // Mostrar el loader cuando se hace clic en el botón de enviar
        loader.style.display = 'inline';

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
                chatOutput.innerHTML += `<p><strong>Error:</strong> ${data.error}</p>`;
            } else {
                // Mostrar la pregunta y la respuesta en el chat
                chatOutput.innerHTML += `<strong>${data.question}</strong></br>`;
                chatOutput.innerHTML += `${data.response}<p></p>`;
                chatOutput.scrollTop = chatOutput.scrollHeight; // Auto scroll to the bottom
            }

            // Limpiar el campo de entrada y deshabilitar el botón
            userInput.value = '';
            sendButton.disabled = true;

        } catch (error) {
            console.error('Error fetching response:', error);
            chatOutput.innerHTML += `<p><strong>Error:</strong> ${error.message}</p>`;
        } finally {
            // Ocultar el loader cuando se complete la respuesta
            loader.style.display = 'none';
        }
    };

    // Llamar a la función para validar la API key
    validateApiKey(apiKey);
})();
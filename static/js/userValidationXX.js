// userValidation.js
export async function validateUser(apiKey) {
    if (!apiKey) {
        return { error: 'API key is missing.' };
    }

    try {
        const userResponse = await fetch('http://127.0.0.1:5010/get_user', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ apiKey })
        });

        const userData = await userResponse.json();
        console.log('API key:', apiKey);
        console.log('Response from server:', userData);
        if (userData.error) {
            return { error: 'Invalid API key. Access to the chatbot is denied.' };
        }

        // Retorna los datos del usuario si se encuentra
        return { user: userData };
    } catch (error) {
        return { error: 'An error occurred during user validation.' };
    }
}

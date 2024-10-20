<?php
session_start();
require 'config.php'; // Archivo donde se cargan las variables de entorno

$host = getenv('DB_HOST');
$db_user = getenv('DB_USER');
$db_password = getenv('DB_PASSWORD');
$db_name = 'echoDB';
$mysqli = new mysqli($host, $db_user, $db_password, $db_name);

if ($mysqli->connect_error) {
    die("Connection failed: " . $mysqli->connect_error);
}

// Ruta index
function index()
{
    require 'views/index.php';
}

// Ruta de registro de usuarios
function register()
{
    global $mysqli;

    if ($_SERVER['REQUEST_METHOD'] == 'POST') {
        $name = $_POST['name'];
        $email = $_POST['email'];
        $password = password_hash($_POST['password'], PASSWORD_DEFAULT);
        $website = $_POST['website'];
        $api_key = bin2hex(random_bytes(22));
        $hostDB = $_POST['hostDB'];
        $userDB = $_POST['userDB'];
        $passwordDB = encryptPassword($_POST['passwordDB']);
        $databaseDB = $_POST['databaseDB'];
        $db_type = $_POST['db_type'];
        $port = $_POST['port'];
        $ssl_enabled = isset($_POST['ssl_enabled']) ? 1 : 0;
        $charset = $_POST['charset'];

        $stmt = $mysqli->prepare("INSERT INTO users (name, email, password, website, api_key, hostDB, userDB, passwordDB, databaseDB, db_type, port, ssl_enabled, charset) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)");
        $stmt->bind_param('sssssssssssis', $name, $email, $password, $website, $api_key, $hostDB, $userDB, $passwordDB, $databaseDB, $db_type, $port, $ssl_enabled, $charset);

        if ($stmt->execute()) {
            echo "Usuario registrado exitosamente!";
            echo "Tu API Key: $api_key";
        } else {
            echo "Error al registrar el usuario: " . $stmt->error;
        }
        $stmt->close();
    }
    require 'views/register.php';
}

// Ruta para validar API Key
function validateApiKey()
{
    global $mysqli;

    $data = json_decode(file_get_contents('php://input'), true);
    $api_key = $data['api_key'] ?? '';

    if (empty($api_key)) {
        echo json_encode(['error' => 'Clave API faltante']);
        return;
    }

    $stmt = $mysqli->prepare("SELECT * FROM users WHERE api_key = ?");
    $stmt->bind_param('s', $api_key);
    $stmt->execute();
    $result = $stmt->get_result();

    if ($result->num_rows > 0) {
        $user = $result->fetch_assoc();
        echo json_encode(['access' => true, 'user' => ['name' => $user['name']]]);
    } else {
        echo json_encode(['access' => false, 'message' => 'Clave API no encontrada']);
    }

    $stmt->close();
}

// Función para encriptar contraseñas de bases de datos
function encryptPassword($password)
{
    $key = getenv('FLASK_SECRET_KEY'); // Utiliza la misma clave que en Python
    $cipher = 'aes-256-cbc';
    $ivlen = openssl_cipher_iv_length($cipher);
    $iv = openssl_random_pseudo_bytes($ivlen);
    $ciphertext = openssl_encrypt($password, $cipher, $key, 0, $iv);
    return base64_encode($iv . $ciphertext);
}

// Función para desencriptar contraseñas de bases de datos
function decryptPassword($encrypted_password)
{
    $key = getenv('FLASK_SECRET_KEY');
    $cipher = 'aes-256-cbc';
    $data = base64_decode($encrypted_password);
    $ivlen = openssl_cipher_iv_length($cipher);
    $iv = substr($data, 0, $ivlen);
    $ciphertext = substr($data, $ivlen);
    return openssl_decrypt($ciphertext, $cipher, $key, 0, $iv);
}

// Ejemplo de enrutador simple
$uri = parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH);
if ($uri == '/register') {
    register();
} elseif ($uri == '/validate-api-key') {
    validateApiKey();
} else {
    index();
}

$mysqli->close();

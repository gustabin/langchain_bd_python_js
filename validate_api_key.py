# validate_api_key.py

from flask import Blueprint, jsonify, request
from extensions import db  # Importar db desde extensions.py
from models import User  # Asegúrate de tener el modelo de User correctamente importado

# Definir el blueprint para la validación de API Key
validate_api_key_bp = Blueprint('validate_api_key', __name__)


@validate_api_key_bp.route('/validate-api-key', methods=['POST'])
def validate_api_key():
    data = request.get_json()
    api_key = data.get('api_key')

    if not api_key:
        return jsonify({'error': 'Clave API faltante'}), 400

    if not isinstance(api_key, str) or len(api_key) != 44:
        return jsonify({'error': 'Formato de clave API inválido'}), 400

    try:
        user = User.query.filter_by(api_key=api_key).first()

        if user:
            return jsonify({
                'access': True,
                'user': {
                    'name': user.name,
                    'email': user.email,
                    'password': user.password,
                    'website': user.website,
                    'api_key': user.api_key,
                    'hostDB': user.hostDB,
                    'userDB': user.userDB,
                    'passwordDB': user.passwordDB,
                    'databaseDB': user.databaseDB,
                    'db_type': user.db_type,
                    'port': user.port,
                    'ssl_enabled': user.ssl_enabled,
                    'charset': user.charset
                }
            }), 200
        else:
            return jsonify({'access': False, 'message': 'Clave API no encontrada'}), 403

    except Exception as e:
        return jsonify({'error': 'Ocurrió un error al validar la clave API'}), 500

# Consulta a la Base de Datos

Este proyecto es una aplicación web desarrollada en Flask que permite realizar consultas a una base de datos SQLite utilizando el modelo de lenguaje de LangChain. El usuario puede escribir consultas en un campo de texto, y la aplicación devuelve los resultados directamente en la interfaz.

## Tecnologías Utilizadas

- **Flask**: Framework web para Python.
- **LangChain**: Biblioteca para construir aplicaciones de lenguaje natural.
- **OpenAI**: Integración con modelos de lenguaje.
- **SQLite**: Base de datos utilizada para el almacenamiento.
- **dotenv**: Manejo de variables de entorno.

## Instalación

Para instalar las dependencias del proyecto, asegúrate de tener [Python](https://www.python.org/downloads/) instalado en tu sistema. Luego, sigue estos pasos:

1. Clona el repositorio:
    ```bash
    git clone https://github.com/gustabin/langchain_bd_python_js.git
    cd nombre_del_repositorio
    ```

2. Crea y activa un entorno virtual (opcional pero recomendado):
    ```bash
    python -m venv venv
    source venv/bin/activate  # En Linux/Mac
    venv\Scripts\activate  # En Windows
    ```

3. Instala las dependencias:
    ```bash
    pip install -r requirements.txt
    ```

## Uso

1. Asegúrate de tener tu archivo de base de datos `inventario.db` en la carpeta `datasources/`.
2. Crea un archivo `.env` en la raíz del proyecto si es necesario para tus variables de entorno.
3. Inicia la aplicación:
    ```bash
    python app.py
    ```

4. Accede a la aplicación en tu navegador en `http://127.0.0.1:5010/`.

## Contribuciones

Las contribuciones son bienvenidas. Si deseas contribuir, por favor sigue estos pasos:

1. Haz un fork del proyecto.
2. Crea una rama para tu característica (`git checkout -b feature/nueva-caracteristica`).
3. Realiza tus cambios y haz un commit (`git commit -m 'Agrega nueva característica'`).
4. Haz push a la rama (`git push origin feature/nueva-caracteristica`).
5. Abre un Pull Request.

## Licencia

Este proyecto está bajo la Licencia MIT. Consulta el archivo [LICENSE](LICENSE) para más detalles.

## Contacto

Si tienes alguna pregunta o comentario, no dudes en contactarme:

- Ing. Gustavo Arias: [tabindev@gmail.com](mailto:tabindev@gmail.com)

- Cualquier ayuda se agradece: https://www.stackcodelab.com/donaciones.php

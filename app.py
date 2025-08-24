from flask import Flask, request, jsonify
import firebase_admin
from firebase_admin import credentials, messaging, firestore

# --- Configuración Inicial ---
app = Flask(__name__)

# Esta línea usa tu clave para conectar con Firebase
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)
db = firestore.client() # Objeto para interactuar con la base de datos

# --- Rutas (Endpoints) de la API ---

# Endpoint para registrar un nuevo residente
@app.route('/residentes', methods=['POST'])
def registrar_residente():
    try:
        data = request.json
        # El ID del documento será el número del apartamento para encontrarlo fácil
        apartamento_id = data['apartamento']
        db.collection('residentes').document(apartamento_id).set(data)
        return jsonify({"status": "success", "message": f"Residente del apto {apartamento_id} registrado"}), 201
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

# Endpoint para obtener la lista de todos los residentes
@app.route('/residentes', methods=['GET'])
def obtener_residentes():
    try:
        residentes_ref = db.collection('residentes').stream()
        residentes_lista = [doc.to_dict() for doc in residentes_ref]
        return jsonify(residentes_lista), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# Endpoint para enviar una notificación a un residente específico
@app.route('/notificar', methods=['POST'])
def enviar_notificacion():
    try:
        data = request.json
        apartamento_id = data['apartamento']
        mensaje_notificacion = data['mensaje']

        # Busca el token del residente en la base de datos
        residente_ref = db.collection('residentes').document(apartamento_id)
        residente = residente_ref.get()

        if not residente.exists:
            return jsonify({"status": "error", "message": "Residente no encontrado"}), 404

        token = residente.to_dict().get('fcm_token')

        if not token:
            return jsonify({"status": "error", "message": "El residente no tiene un token de notificación"}), 400

        # Construye y envía la notificación usando FCM
        message = messaging.Message(
            notification=messaging.Notification(
                title='🔔 Notificación de Portería',
                body=mensaje_notificacion,
            ),
            token=token,
        )
        response = messaging.send(message)
        return jsonify({"status": "success", "message": f"Notificación enviada: {response}"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
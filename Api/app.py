from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# --- Función de Clasificación ---
# --- Función de Clasificación ---
def clasificar_condicion(duracion, severidad, impacto):
    """Clasifica la condición médica basada en los 3 datos recibidos."""
    # Convertir a minúsculas para una comparación robusta
    duracion = duracion.lower()
    severidad = severidad.lower()
    impacto = impacto.lower()

    # 1. ENFERMEDAD TERMINAL
    if duracion in ('prolongada', 'años', 'meses') and severidad in ('muy intenso', 'grave') and impacto in ('incapacidad total', 'limitado permanentemente'):
        return "ENFERMEDAD TERMINAL"

    # 2. ENFERMEDAD CRÓNICA (Larga duración)
    elif duracion in ('prolongada', 'años', 'meses'):
        return "ENFERMEDAD CRÓNICA"

    # 3. NO ENFERMO (Mínimo o Nulo)
    elif duracion in ('ausente', 'breve') and severidad in ('nulo', 'mínimo') and impacto in ('normal', 'mínimo'):
        return "NO ENFERMO"

    # 4. ENFERMEDAD AGUDA (Corta duración con intensidad)
    elif duracion in ('aguda', 'días', 'semanas') and (severidad in ('intenso', 'fuerte') or impacto in ('incapacidad', 'limitado')):
        return "ENFERMEDAD AGUDA"

    # 5. ENFERMEDAD LEVE (Corta duración y baja severidad)
    elif duracion in ('aguda', 'días', 'semanas') and severidad in ('tolerable', 'leve') and impacto in ('mínimo', 'tolerable'):
        return "ENFERMEDAD LEVE"

    # Caso por defecto si la combinación no encaja
    return "NO ENFERMO"


# ----------------------------------------------------------------------
## 1. Ruta de la API para Clasificar
# ----------------------------------------------------------------------

@app.route('/', methods=['GET'])
def index():
    """Sirve el archivo index.html desde la carpeta templates."""
    return render_template('index.html')

@app.route('/clasificar', methods=['POST'])
def clasificar_api():
    """
    Recibe un JSON en el body con 'duracion', 'severidad' e 'impacto'
    y devuelve la condición médica clasificada.
    
    Ejemplo:
    curl -X POST -H "Content-Type: application/json" \
      -d '{"duracion":"aguda","severidad":"intenso","impacto":"incapacidad"}' \
      http://127.0.0.1:5000/clasificar
    """
    # Intentar obtener JSON del body
    data = request.get_json(silent=True)
    if not data:
        return jsonify({
            "error": "Cuerpo JSON faltante",
            "mensaje": "Envíe un JSON con los campos: duracion, severidad e impacto."
        }), 400

    duracion = data.get('duracion')
    severidad = data.get('severidad')
    impacto = data.get('impacto')

    # Verificar que los 3 datos esenciales estén presentes
    if not duracion or not severidad or not impacto:
        return jsonify({
            "error": "Faltan parámetros",
            "mensaje": "Proporcione los 3 parámetros en el JSON: duracion, severidad e impacto."
        }), 400

    # Llamar a la función de clasificación
    resultado = clasificar_condicion(duracion, severidad, impacto)

    # Devolver el resultado en formato JSON
    return jsonify({
        "duracion_dada": duracion,
        "severidad_dada": severidad,
        "impacto_dado": impacto,
        "condicion_clasificada": resultado
    })

# ----------------------------------------------------------------------

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
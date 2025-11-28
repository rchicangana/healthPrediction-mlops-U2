# Objetivo

🔬 Desafío de Modelado en Medicina: Enfermedades Huérfanas y Comunes 💡 Contexto del Problema Dado el avance tecnológico, el campo de la medicina genera una abundancia de información (datos de pacientes).

- Sin embargo, existe una notable asimetría en la disponibilidad de datos:

- Enfermedades Comunes: Existe una gran cantidad de datos (abundancia).

- Enfermedades Huérfanas (Raras): La cantidad de datos existentes es escasa.


## Diseño del Pipeline

> Para información más detallada y arquitectura técnica, consulta [docs/PROPUESTAPipeLine.md](docs/PROPUESTAPipeLine.md)

#### Nota: Las enfermedades huérfanas son aquellas con baja prevalencia que a menudo son crónicas, graves y amenazan la vida, lo que complica su diagnóstico y estudio.

📝 **Requerimiento del Proyecto**  
Se requiere construir un Modelo Predictivo capaz de determinar la probabilidad de que un paciente sufra o no de alguna enfermedad, basándose únicamente en los datos de sus síntomas.

🛠️ **Objetivos del Modelo**  
El modelo debe ser robusto y eficaz para la clasificación, independientemente de la frecuencia de la enfermedad:

- **Predicción para Enfermedades Comunes:** Manejar y clasificar correctamente con muchos datos de entrenamiento.
- **Predicción para Enfermedades Huérfanas:** Ser capaz de clasificar con precisión a pesar de la escasez de datos (problema de clases minoritarias).

# Estructura del Repositorio

# Path: /Api

## Clasificador de Condición Médica (Flask)

Este repositorio contiene una pequeña API en Flask que clasifica una condición médica sencilla basada en tres atributos: `duracion`, `severidad` e `impacto`.

El servicio expone una ruta web con una interfaz simple (`templates/index.html`) y una ruta API `/clasificar` que recibe un JSON y devuelve la clasificación.

### Estructura principal

- `app.py` - aplicación Flask con la lógica de clasificación y la ruta `/clasificar`.
- `Dockerfile` - receta para construir una imagen Docker que instala Flask y Flask-CORS y expone la app en el puerto 5000.
- `templates/index.html` - interfaz web sencilla para probar la API desde el navegador.

### Propósito / objetivo

Proveer una API mínima para clasificar condiciones médicas (ejemplo didáctico para prácticas de MLOps). Ideal para:

- Enseñar despliegue en Docker.
- Probar integración de una API REST simple con frontend estático.
- Usar como base para añadir un modelo ML real más adelante.

### Requisitos

- Opcional: Docker instalado (para construir y ejecutar la imagen).
- Python 3.8+ si se desea ejecutar localmente.

### Instrucciones: Construir y ejecutar con Docker (PowerShell)

1. Abrir PowerShell y moverse al directorio del proyecto (donde están `Dockerfile` y `app.py`):

```powershell
cd "/Api"
```

2. Construir la imagen Docker:

```powershell
docker build -t clasificador-medico .
```

3. Ejecutar el contenedor mapeando el puerto 5000:

```powershell
docker run --rm -p 5000:5000 clasificador-medico
```

4. Abrir en el navegador: `http://localhost:5000` para usar la UI.

Nota: si construyes desde otra carpeta, indica la ruta absoluta del Dockerfile y del contexto:

```powershell
docker build -t clasificador-medico -f "C:\Estudio\Maestria\MLops\Taller 1\Api\Dockerfile" "C:\Estudio\Maestria\MLops\Taller 1\Api"
```

### Ejecutar localmente sin Docker

1. Crear y activar un entorno virtual (PowerShell):

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

2. Instalar dependencias:

```powershell
pip install flask flask-cors
```

3. Ejecutar la aplicación:

```powershell
python app.py
```

La API quedará escuchando en `http://0.0.0.0:5000` (accesible como `http://localhost:5000` en la máquina host).

### Uso de la API: ejemplos de requests

Endpoint: `POST http://localhost:5000/clasificar`

Payload JSON (ejemplo):

```json
{
  "duracion": "aguda",
  "severidad": "intenso",
  "impacto": "incapacidad"
}
```

Ejemplo con curl (Linux / Git Bash / WSL):

```bash
curl -X POST http://localhost:5000/clasificar -H "Content-Type: application/json" -d '{"duracion":"aguda","severidad":"intenso","impacto":"incapacidad"}'
```

Ejemplo en PowerShell con `Invoke-RestMethod` (recomendado en Windows PowerShell):

```powershell
Invoke-RestMethod -Method POST -Uri http://localhost:5000/clasificar -ContentType "application/json" -Body ('{"duracion":"aguda","severidad":"intenso","impacto":"incapacidad"}')
```

Respuesta esperada (ejemplo):

```json
{
  "duracion_dada": "aguda",
  "severidad_dada": "intenso",
  "impacto_dado": "incapacidad",
  "condicion_clasificada": "ENFERMEDAD AGUDA"
}
```



### Interfaz Web

La ruta raíz `/` sirve `templates/index.html`, una UI simple que envía el formulario a `/clasificar` y muestra el resultado.

### Errores comunes y soluciones

- Respuesta 400 "Cuerpo JSON faltante" — Asegúrate de enviar Content-Type: application/json y un JSON válido.
- Puerto 5000 en uso — cambia el puerto local o para Docker usa otro mapeo `-p 5001:5000` y luego llamada a `http://localhost:5001`.
- CORS — el Dockerfile instala `flask-cors` y el app habilita CORS para permitir peticiones desde la UI remota.


## Nuevas Funcionalidades Agregadas

### 1. Logging de Peticiones
- Todas las solicitudes a `/clasificar` se registran automáticamente en un archivo **`logs_clasificaciones.jsonl`**.
- Cada registro incluye:
  - Timestamp UTC
  - Duración, severidad e impacto enviados
  - Resultado de la clasificación
- Formato **JSON por línea** para fácil lectura por otras APIs.

### 2. API para Consultar Logs
- Endpoint: `GET /logs` 
- Permite consultar todos los logs o filtrarlos por condición:
  - Ejemplo: `/logs?condicion=ENFERMEDAD TERMINAL`
- Devuelve un **JSON** con los registros filtrados.

### 3. Interfaz Web Mejorada
- Botón para consultar los logs directamente desde la web.
- Selector de filtro por condición antes de consultar.
- Contenedor con scroll que muestra los logs en formato JSON legible.
- Manejo de errores claro en caso de fallas de conexión o logs vacíos.


### Final: Mas Info en /docs

## Licencia

Este proyecto es de ejemplo/educativo. 

---

Ricardo Chicangana Vidal - MIAA

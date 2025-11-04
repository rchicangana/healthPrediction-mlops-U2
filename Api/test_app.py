import unittest
import json
from app import app, clasificar_condicion  # Importamos la app y la función

class TestClasificacion(unittest.TestCase):

    def setUp(self):
        # Configura el cliente de prueba de Flask
        self.client = app.test_client()
        self.client.testing = True

    # --- Test directo a la función ---
    def test_clasificar_funcion(self):
        self.assertEqual(
            clasificar_condicion("aguda", "intenso", "incapacidad"),
            "ENFERMEDAD AGUDA"
        )
        self.assertEqual(
            clasificar_condicion("prolongada", "grave", "incapacidad total"),
            "ENFERMEDAD TERMINAL"
        )
        self.assertEqual(
            clasificar_condicion("ausente", "mínimo", "normal"),
            "NO ENFERMO"
        )

    # --- Test a la ruta API /clasificar ---
    def test_clasificar_api(self):
        # Enviar JSON válido
        response = self.client.post(
            '/clasificar',
            data=json.dumps({
                "duracion": "aguda",
                "severidad": "intenso",
                "impacto": "incapacidad"
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data["condicion_clasificada"], "ENFERMEDAD AGUDA")

        # Enviar JSON incompleto
        response2 = self.client.post(
            '/clasificar',
            data=json.dumps({"duracion": "aguda"}),
            content_type='application/json'
        )
        self.assertEqual(response2.status_code, 400)
        data2 = json.loads(response2.data)
        self.assertIn("Faltan parámetros", data2["error"])

if __name__ == '__main__':
    unittest.main()

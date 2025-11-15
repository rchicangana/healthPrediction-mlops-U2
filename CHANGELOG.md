# Changelog

## Versión 1.1.0 - 2025-11-15

Esta versión incorpora la capa de tecnologías y un stack de soluciones completo al diseño del pipeline de MLOps, mejorando la visión arquitectónica del proyecto.

### ✨ Nuevas Características/Arquitectura

* **Stack de Soluciones (Solutions Stack) Incluido:** Se ha definido y agregado la pila tecnológica para la implementación del pipeline.
* **Herramientas Añadidas:**
    * **Lenguaje:** Python
    * **Versionamiento:** GitHub
    * **CI/CD:** Jenkins
    * **Contenedorización:** Docker
    * **Base de Datos:** PostgreSQL
    * **Monitoreo:** Prometheus y Grafana
    * **Seguridad:** SonarQube
    * **Nube:** Google Cloud (GCP)
* **Roles de QA/Validación:** Se ha formalizado el rol de **QA** (Quality Assurance) en las etapas de *Develop* y **QA Medical System** en la etapa de *Staging* para una validación de calidad y clínica exhaustiva, respectivamente.

### 🔄 Modificaciones en Etapas Existentes

* **Desarrollo (Develop):** Se ha agregado la etapa explícita de **Unit Test** antes del *Build*.
* **Seguridad:** El análisis de vulnerabilidades (*Security vulnerability analysis*) se enlaza al uso de **SonarQube** dentro del proceso CI/CD.
* **Monitoreo:** El monitoreo de *Performance* y *Logs* se asocia explícitamente con **Prometheus** y **Grafana**.

### 📝 Documentación

* El documento de explicación ha sido actualizado para incluir una sección detallada sobre el **Stack de Soluciones y Tecnologías**.

![Diagrama del Pipeline](PipeLineML.drawio.png)


## Versión 1.0.0 - 2025-11-03

Version Inicial

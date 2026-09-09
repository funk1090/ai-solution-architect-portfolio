# AI Solution Architect Portfolio

Plataforma de IA empresarial construida de forma incremental como proyecto
de aprendizaje y portafolio profesional, usando exclusivamente tecnologías
open source y datos sintéticos.

## Filosofía

- **Open Source First**: se prioriza software autoalojable sobre servicios
  cloud propietarios.
- **Learn by Building**: cada concepto aprendido de un libro técnico se
  traduce en una implementación real dentro de la plataforma.
- **Architecture Before Code**: cada feature significativa se diseña
  (problema, requisitos, diagrama, ADR) antes de implementarse.
- **Documentation as Code**: la documentación es un entregable, no un
  extra.

## Estado actual

🚧 Fase 1 en progreso — ver [docs/architecture/adr](docs/architecture/adr)
para las decisiones de arquitectura tomadas hasta ahora.

## Estructura del repositorio

```
.
├── docs/               # Documentación de arquitectura, ADRs, diagramas
├── datasets/           # Datos sintéticos (nunca información real/confidencial)
├── backend/            # Servicios backend (FastAPI, pipelines, etc.)
├── frontend/           # Interfaces de usuario (cuando aplique)
├── infrastructure/     # Docker Compose, IaC, configuración de despliegue
├── notebooks/          # Exploración y prototipado en Jupyter
├── experiments/        # Pruebas de concepto que no llegan a producción
├── tests/              # Pruebas automatizadas
└── books/              # Notas y resúmenes de los libros técnicos usados
```

## Licencia

Este proyecto se distribuye bajo licencia MIT. Ver [LICENSE](LICENSE).

## Aviso

Todo el contenido de negocio (RFPs, requisitos, datasets) es sintético y
ficticio (empresa ficticia "Andes Digital Networks"). No se usa ninguna
información confidencial ni propietaria.

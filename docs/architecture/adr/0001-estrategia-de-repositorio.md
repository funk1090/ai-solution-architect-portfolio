# ADR-0001: Estrategia de repositorio (monorepo)

## Estado
Aceptado

## Contexto
El proyecto se plantea como un portafolio de ingeniería construido de forma
incremental a lo largo de ~12 meses, en 7 fases, cada una asociada a un
proyecto técnico distinto (generador de datos sintéticos, pipeline de
ingesta, clasificador de requisitos, motor RAG, laboratorio de performance,
comprensión de documentos, y el producto final integrado).

Existían dos estrategias posibles para organizar el código en GitHub:

1. **Multi-repo**: un repositorio independiente por cada proyecto/fase.
2. **Monorepo**: un único repositorio con los proyectos organizados como
   módulos/carpetas dentro de una estructura común.

Este proyecto es desarrollado por una sola persona, con el objetivo
explícito de construir una narrativa profesional coherente ("plataforma
end-to-end de IA empresarial") y no una colección de scripts sueltos.

## Decisión
Se adopta una estrategia de **monorepo**. Todos los proyectos de las
distintas fases vivirán dentro de un único repositorio
(`ai-solution-architect-portfolio`), organizados por dominio funcional
(`backend/`, `infrastructure/`, `docs/`, etc.) en lugar de por fase
cronológica.

Si en el futuro un componente específico (por ejemplo, el motor RAG)
alcanza suficiente madurez y complejidad como para tener un ciclo de
release independiente, se evaluará su extracción a un repositorio propio
mediante un nuevo ADR.

## Alternativas consideradas

**Multi-repo**
- Ventajas: aislamiento total entre proyectos, historial de commits más
  limpio por proyecto, más parecido a cómo se vería en una organización
  con múltiples equipos.
- Desventajas: duplicación de configuración (CI/CD, Docker, linting),
  fricción para compartir código común (ej. utilidades de logging o
  configuración), y una narrativa de portafolio fragmentada — un
  reclutador tendría que navegar 7 repositorios distintos para entender
  el proyecto completo.

**Monorepo**
- Ventajas: una sola fuente de verdad, configuración compartida
  (linting, CI/CD, Docker Compose orquestando todos los servicios juntos),
  narrativa unificada de "plataforma", y es más fácil de mantener para un
  desarrollador único sin equipo de DevOps dedicado.
- Desventajas: el historial de commits mezcla todos los dominios, y si el
  proyecto creciera con múltiples colaboradores externos, podría requerir
  herramientas adicionales de monorepo tooling (Nx, Turborepo, Bazel) que
  hoy serían sobreingeniería para este contexto.

## Consecuencias
- Toda nueva fase se desarrollará como una carpeta/módulo dentro de este
  repositorio, no como un repositorio nuevo.
- El `docker-compose.yml` raíz podrá orquestar todos los servicios de
  todas las fases en conjunto, facilitando demos end-to-end.
- Se debe mantener disciplina en la organización por dominio (no mezclar
  lógica de negocio de una fase con otra) para que el monorepo no se
  convierta en una carpeta desordenada.
- Se revisará esta decisión si el proyecto pasa a tener colaboradores
  externos o si algún componente requiere un ciclo de despliegue
  totalmente independiente.

## Referencias
- Fundamentals of Data Engineering (Reis & Housley) — Ch. 3, Designing
  Good Data Architecture.
- Documentation as Code, principio de "Architecture Before Code" definido
  en el contexto del proyecto.

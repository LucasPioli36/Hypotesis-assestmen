# Hypothesis Platform — Data Assessment v5
**Fecha:** 2026-05-23 | **Versión:** 5.0 | **Autor:** Data Engineering

---

## Data Vision Statement

> *El objetivo de la estrategia de datos de Hypothesis no es únicamente medir uso, sino transformar la plataforma en la única herramienta de aprendizaje digital capaz de demostrar impacto educativo y valor institucional de forma cuantificable — convirtiendo analytics en diferencial comercial y motor de retención.*

---

## Resumen Ejecutivo

Hypothesis es una plataforma B2B SaaS de anotaciones colaborativas para universidades. Se integra con los principales LMS (Canvas, Blackboard, D2L, Moodle) y permite a estudiantes y profesores anotar cualquier material educativo digital.

**Hallazgo central:** La compañía posee una arquitectura técnica madura y acumula datos operacionales significativos, pero hoy no puede responder las preguntas más básicas que determinan retención de clientes: *¿cuánto usan Hypothesis los estudiantes? ¿qué instituciones están en riesgo de no renovar?* Esta brecha no es un problema técnico menor — es un riesgo de revenue que se agrava con el tiempo.

**Corrección crítica respecto a versiones anteriores:** El analytics service marcado como TODO en el código no se implementó en días por los equipos anteriores no por descuido, sino porque el diseño correcto requiere una arquitectura de ingesta dedicada. Escribir eventos de comportamiento de miles de estudiantes simultáneos directo al PostgreSQL transaccional causaría contención que degradaría la API en producción. La Fase 1 del roadmap ha sido recalibrada en consecuencia.

**Segunda corrección crítica:** La purga de LTI params a 30 días destruye contexto histórico irreemplazable (nombre del curso al momento del launch, rol académico, término/semestre, parámetros LMS custom) que no está normalizado en columnas estructurales. Esto es un riesgo **Crítico** que impide los reportes YoY que las universidades necesitan para renovar contratos. Requiere solución de ingeniería inmediata (ver R4).

**Stack corregido:** La propuesta de infraestructura analítica ha sido rediseñada para optimizar el stack AWS existente (ElasticBeanstalk + RDS + S3) en lugar de introducir herramientas externas sin justificación de costos (ver Bloque 5).

---

## Estado Actual

| Área | Estado | Descripción |
|------|--------|-------------|
| Infraestructura | 🟢 Sólida | AWS multi-región, PostgreSQL, Elasticsearch, RabbitMQ en producción |
| Integraciones | 🟢 Sólidas | Canvas, Blackboard, D2L, Moodle, JSTOR, VitalSource, YouTube, HubSpot |
| Modelo de datos | 🟢 Maduro | 61 tablas, 174+134 migraciones, esquema bien normalizado |
| Analytics | 🟡 Parcial | Solo métricas LTI (launches, grades). Sin engagement real |
| Tracking | 🔴 Deficiente | Analytics service sin implementar. Sin sesiones ni apertura de recursos |
| Data Quality | ⚪ Pendiente | Queries listas para ejecutar — ver sección Volumetría Real |
| Data Governance | 🔴 Inexistente | Sin data catalog, sin ownership formal, sin definiciones compartidas |
| Revenue Analytics | 🔴 Inexistente | Datos de contratos y billing desconectados de datos de uso |
| Product Analytics | 🔴 Inexistente | No existe una capa de analytics de producto |

**Madurez global estimada: 1.6 / 5.** El roadmap de este documento está diseñado para llevarla a 3.5/5 en 12 meses.

---

## Volumetría Real

> ⚠️ **Esta sección debe completarse antes de presentar el documento al CEO o solicitar presupuesto para Fase 1.** Ejecutar las queries en producción y completar los valores. Sin números reales, este diagnóstico es una hipótesis, no un diagnóstico de ingeniería.

### Queries a ejecutar — BD `h` (PostgreSQL)

```sql
-- 1. Total de anotaciones activas
SELECT COUNT(*) AS total_anotaciones
FROM annotation WHERE deleted = false;
-- RESULTADO: [COMPLETAR]

-- 2. Crecimiento mensual de anotaciones (últimos 24 meses)
SELECT
    DATE_TRUNC('month', created) AS mes,
    COUNT(*) AS anotaciones,
    COUNT(DISTINCT userid) AS usuarios_activos,
    COUNT(*) FILTER (WHERE array_length(references, 1) > 0) AS replies
FROM annotation
WHERE deleted = false AND created > NOW() - INTERVAL '24 months'
GROUP BY 1 ORDER BY 1 DESC;
-- RESULTADO: [COMPLETAR — tabla de 24 filas]

-- 3. Usuarios activos (30/90/180 días)
SELECT
    COUNT(DISTINCT userid) FILTER (WHERE created > NOW() - INTERVAL '30 days')  AS mau_30d,
    COUNT(DISTINCT userid) FILTER (WHERE created > NOW() - INTERVAL '90 days')  AS mau_90d,
    COUNT(DISTINCT userid) FILTER (WHERE created > NOW() - INTERVAL '180 days') AS mau_180d
FROM annotation WHERE deleted = false;
-- MAU 30d: [COMPLETAR] | MAU 90d: [COMPLETAR] | MAU 180d: [COMPLETAR]

-- 4. Tamaño de la base de datos y tablas más grandes
SELECT pg_size_pretty(pg_database_size(current_database())) AS tamano_bd_h;
-- RESULTADO: [COMPLETAR] GB

SELECT relname, pg_size_pretty(pg_total_relation_size(relid)) AS tamano, n_live_tup AS filas
FROM pg_stat_user_tables ORDER BY pg_total_relation_size(relid) DESC LIMIT 10;
-- RESULTADO: [COMPLETAR — top 10 tablas por tamaño]

-- 5. Anotaciones públicas vs privadas (shared)
SELECT shared, COUNT(*) FROM annotation WHERE deleted = false GROUP BY 1;
-- RESULTADO: shared=true [COMPLETAR] | shared=false [COMPLETAR]
```

### Queries a ejecutar — BD `lms` (PostgreSQL)

```sql
-- 6. Instituciones por estado de actividad
SELECT
    COUNT(*) FILTER (WHERE last_launched > NOW() - INTERVAL '90 days')  AS activas_90d,
    COUNT(*) FILTER (WHERE last_launched > NOW() - INTERVAL '180 days') AS activas_180d,
    COUNT(*) FILTER (WHERE last_launched <= NOW() - INTERVAL '180 days') AS inactivas,
    COUNT(*) AS total
FROM application_instances;
-- Activas 90d: [COMPLETAR] | Activas 180d: [COMPLETAR] | Inactivas: [COMPLETAR] | Total: [COMPLETAR]

-- 7. Cursos y usuarios
SELECT
    COUNT(DISTINCT lc.id)  AS total_cursos,
    COUNT(DISTINCT lu.id)  AS total_usuarios_lms
FROM lms_course lc, lms_user lu;
-- Cursos totales: [COMPLETAR] | Usuarios LMS: [COMPLETAR]

-- 8. Eventos por tipo y tendencia mensual (últimos 12 meses)
SELECT
    DATE_TRUNC('month', e.timestamp)       AS mes,
    et.type                                AS tipo_evento,
    COUNT(*)                               AS cantidad,
    COUNT(DISTINCT e.application_instance_id) AS instituciones
FROM event e
JOIN event_type et ON et.id = e.type_id
WHERE e.timestamp > NOW() - INTERVAL '12 months'
GROUP BY 1, 2 ORDER BY 1 DESC, 3 DESC;
-- RESULTADO: [COMPLETAR — tabla con tendencia de launches y otros eventos]

-- 9. Calificaciones sincronizadas
SELECT
    COUNT(*)                                         AS total_grades,
    COUNT(*) FILTER (WHERE success = true)           AS exitosas,
    ROUND(AVG(grade) FILTER (WHERE success = true), 3) AS promedio_grade
FROM grading_sync_grade;
-- Total: [COMPLETAR] | Exitosas: [COMPLETAR] | Promedio: [COMPLETAR]

-- 10. Proxy de salud por institución (top 20)
SELECT
    o.name                  AS institucion,
    ai.last_launched,
    COUNT(DISTINCT lc.id)   AS cursos_activos,
    COUNT(DISTINCT lu.id)   AS usuarios_unicos,
    CASE
        WHEN ai.last_launched > NOW() - INTERVAL '90 days'  THEN 'Activo'
        WHEN ai.last_launched > NOW() - INTERVAL '180 days' THEN 'En riesgo'
        ELSE 'Inactivo'
    END AS estado_salud
FROM organization o
JOIN application_instances ai ON ai.organization_id = o.id
LEFT JOIN lms_course_application_instance lcai ON lcai.application_instance_id = ai.id
LEFT JOIN lms_course lc ON lc.id = lcai.lms_course_id
LEFT JOIN lms_user_application_instance luai ON luai.application_instance_id = ai.id
LEFT JOIN lms_user lu ON lu.id = luai.lms_user_id
GROUP BY 1, 2 ORDER BY cursos_activos DESC LIMIT 20;
-- RESULTADO: [COMPLETAR — tabla de las 20 instituciones más activas]
```

---

## Data Maturity Assessment

| Dominio | Nivel | Descripción |
|---------|-------|-------------|
| Data Collection | 2 / 5 | Datos operacionales sí. Eventos de comportamiento, no |
| Data Quality | 2 / 5 | Sin validaciones automatizadas ni procesos de limpieza formales |
| Data Governance | 1 / 5 | Sin ownership formal, sin catalog, sin glosario |
| Analytics | 2 / 5 | Algunas métricas LMS disponibles, sin capa analítica central |
| Product Analytics | 1 / 5 | Endpoint existe en código, no implementado |
| Self-Service Analytics | 1 / 5 | No existe. Todo análisis requiere acceso directo a BD |
| AI / ML Readiness | 2 / 5 | Datos existen pero no están curados ni centralizados |

**Score global: 1.6 / 5**

---

## Current Pain by Team

*Este assessment existe porque cada área de la compañía enfrenta hoy limitaciones concretas por falta de datos. Estas son las fricciones que la estrategia de datos debe resolver.*

| Área | Pain hoy | Consecuencia |
|------|----------|--------------|
| **Product** | No saben qué features generan engagement real. Las decisiones de roadmap se basan en intuición, no en datos de uso | Features se construyen sin validación cuantitativa. Inversión mal asignada |
| **Customer Success** | No pueden detectar señales de churn antes de que el cliente avise que no renueva | CS actúa reactivamente. Pérdida de cuentas que podrían haberse salvado |
| **Sales** | No pueden demostrar ROI en una reunión de renovación. No tienen datos de engagement por institución para conversaciones de upsell | Renovaciones se negocian sin evidencia. Tasa de cierre sub-óptima |
| **Leadership** | No tienen una visión unificada del negocio. Uso y revenue viven en sistemas separados. Las decisiones estratégicas se basan en datos parciales | Asignación de recursos sub-óptima. Incapacidad de proyectar crecimiento con precisión |
| **Engineering** | No existe ownership formal de analytics. El analytics service tiene un TODO en el código desde hace tiempo. Sin priorización clara | Deuda técnica creciente en datos. Nadie es responsable de que los datos estén disponibles |
| **Finance** | No pueden correlacionar niveles de uso con probabilidad de renovación | No pueden priorizar recursos en cuentas de alto riesgo vs alto valor |

---

## Quick Wins — Próximos 30 Días

*Estas acciones son ejecutables de inmediato, tienen alta visibilidad y generan momentum organizacional.*

| Acción | Esfuerzo | Resultado inmediato | Impacto en negocio |
|--------|---------|--------------------|--------------------|
| **Ejecutar queries de Volumetría Real** | 1 día | Primer baseline real: volúmenes, crecimiento, distribución | Diagnóstico deja de ser una hipótesis. Base para solicitar presupuesto |
| **Dashboard proxy desde datos existentes** | 1-2 semanas | Health Score básico por institución desde `lms.event` + `lms.application_instances` | CS tiene visibilidad desde el mes 1, sin esperar el DW ni el tracking |
| **Diseño del sistema de eventos** | 1 semana | Taxonomía de eventos + arquitectura de write-path definida | Evita reescribir el sistema después de construirlo mal |
| **Resource tracking en client** | 2-3 días | Saber qué tipo de recurso genera más anotaciones | Product puede priorizar inversión por tipo de contenido |
| **Ejecutar queries de calidad de datos** | 1-2 días | Primer baseline de calidad de datos | Identifica riesgos antes de construir el DW |
| **Entrevistas a CS/Sales/Finance** | 1 semana | Revenue model confirmado, KPIs validados | Completa el Bloque 0 y Revenue Assessment |

> **Nota sobre el analytics endpoint:** No está en los Quick Wins de 30 días porque no es un cambio de 2-3 días — ver análisis técnico en Bloque 4, sección 4.4.

---

## Bloque 0 — Entendimiento del Negocio

### 0.1 Business Model Canvas

| Dimensión | Descripción |
|-----------|-------------|
| **Clientes** | Universidades, colleges e instituciones educativas de nivel superior |
| **Usuarios finales** | Estudiantes (anotan, responden, colaboran) y profesores (configuran, revisan, califican) |
| **Compradores** | CIO, Academic Technology Officers, LMS Administrators, Decanos |
| **Propuesta de valor** | Anotación colaborativa sobre cualquier material educativo. Fomenta lectura activa, participación y aprendizaje profundo. Se integra sin fricción con el LMS existente de la institución |
| **Canales** | Integración LTI con LMS (Canvas, Blackboard, D2L, Moodle) + web directo |
| **Relación con clientes** | Contrato institucional anual, onboarding, soporte técnico, Customer Success dedicado |
| **Fuentes de ingreso** | `[REQUIERE ENTREVISTA]` — presumiblemente licencias por cantidad de estudiantes activos o por institución |
| **Recursos clave** | Plataforma de anotación (`h`), integración LMS (`lms`), cliente JS (`client`), equipo CS |
| **Actividades clave** | Mantener integraciones LMS, onboarding institucional, soporte, desarrollo de producto |
| **Socios clave** | Proveedores LMS (Instructure, Anthology, D2L, Moodle), proveedores contenido (JSTOR, VitalSource) |
| **Estructura de costos** | Infraestructura AWS, ingeniería, Customer Success, integraciones de contenido |

---

### 0.2 Revenue Drivers

| Driver | Fuente de datos | Disponibilidad |
|--------|----------------|----------------|
| Universidades activas | `organization` + `application_instances` (lms) | ✅ BD lms |
| Estudiantes activos | `lms_user` + `lms_course_membership` (lms) | ✅ BD lms |
| Cursos con Hypothesis | `lms_course` (lms) | ✅ BD lms |
| Licencias contratadas | — | ❌ HubSpot / billing externo |
| Contratos y renovaciones | — | ❌ HubSpot / billing externo |
| Churn proxy | `application_instances.last_launched` | ⚠️ Aproximado |

---

### 0.3 North Star Metrics propuestas

| Métrica | Descripción | Fuente disponible |
|---------|-------------|------------------|
| **Monthly Active Students (MAS)** | Estudiantes únicos con al menos 1 anotación o launch en el mes | `annotation` (h) + `event` (lms) |
| **Monthly Active Instructors (MAI)** | Instructores únicos que configuran o revisan asignaciones | `event_user` con rol instructor (lms) |
| **Annotation Rate** | Anotaciones promedio por estudiante por curso | `annotation` (h) + `lms_course_membership` (lms) |
| **Launch → Annotation Conversion** | % de launches que resultan en al menos 1 anotación | `event` (lms) + `annotation` (h) |
| **Retención semestral** | % de cursos/instituciones que continúan el siguiente semestre | `lms_course` + `lms_term` (lms) |
| **Renewal Rate** | % de contratos renovados | ❌ HubSpot / billing externo |

---

### 0.4 KPIs por área

| Área | KPI | Calculable hoy |
|------|-----|---------------|
| **Product** | MAU / DAU | ⚠️ Parcial |
| | Retención 30/60/90 días | ⚠️ Parcial |
| | Annotation Rate por curso | ✅ Sí |
| | Feature adoption rate | ❌ No |
| **Customer Success** | Health Score por institución | ⚠️ Proxy solamente |
| | Adoption Score (cursos activos / contratados) | ❌ Falta dato contratos |
| | Churn Risk Score | ⚠️ Proxy desde `last_launched` |
| **Sales** | ARR | ❌ No en BDs |
| | Renewal Rate | ❌ No en BDs |
| | Expansion Revenue (nuevos cursos en clientes existentes) | ⚠️ Parcial |
| **Engineering** | Availability | ❌ New Relic |
| | Error Rate | ❌ Sentry |
| | Response Time | ❌ New Relic |
| **Education** | Annotation Density por recurso | ✅ Sí |
| | Student Participation Rate en un curso | ✅ Sí |
| | Collaboration Index (replies / anotaciones) | ✅ Sí |

---

### 0.5 Customer Journey

#### Journey del Instructor

```
[1] Accede al LMS → [2] Configura asignación → [3] Publica recurso
       ↓                      ↓                        ↓
    LTI config          deep_linking event         document_url en BD

[4] Estudiantes ingresan → [5] Se generan anotaciones → [6] Revisa actividad
       ↓                           ↓                           ↓
  configured_launch          annotation en h             dashboard LMS

[7] Califica
       ↓
  grading_sync_grade
```

#### Journey del Estudiante

```
[1] Launch desde LMS → [2] Abre recurso → [3] Lee contenido
       ↓                      ↓                   ↓
  configured_launch    ❌ No trackeado     ❌ No trackeado

[4] Anota            → [5] Responde       → [6] Recibe feedback
       ↓                      ↓                   ↓
  annotation en h     annotation.references    notification
```

#### Cobertura del journey

| Paso | Medible hoy | Cómo |
|------|------------|------|
| Launch desde LMS | ✅ | `event.configured_launch` (lms) |
| Configura asignación | ✅ | `event.deep_linking` / `edited_assignment` (lms) |
| **Abre recurso** | ❌ | No implementado |
| **Lee contenido** | ❌ | No implementado |
| Crea anotación | ⚠️ Parcial | `annotation` table — no hay evento explícito |
| Responde | ⚠️ Parcial | `annotation.references` — inferido |
| Menciona usuario | ✅ | `mention` table (h) |
| Calificación enviada | ✅ | `grading_sync_grade` (lms) |

> **Los pasos de mayor valor educativo (apertura de recurso, lectura) son los menos medibles.** Esto hace imposible hoy demostrar cuánto "usa" un estudiante Hypothesis.

---

### 0.6 Preguntas del Board

- ¿Qué universidades usan más el producto? ¿Cuántos cursos activos tiene cada una?
- ¿Qué LMS tiene mayor tasa de adopción?
- ¿Cuántos estudiantes usan activamente Hypothesis este semestre?
- ¿Qué recursos generan más anotaciones?
- ¿Qué instituciones están en riesgo de churn?
- ¿Cuánto revenue está asociado a cada nivel de uso?
- ¿Qué instituciones tienen contratos próximos a vencer?

---

## Bloque 1 — Arquitectura

### 1.1 Repositorios

| Repositorio | Función | Tecnología | Base de datos |
|-------------|---------|-----------|---------------|
| `hypothesis/h` | Backend central: API REST, autenticación, grupos, búsqueda, admin | Python 3.11 + Pyramid, Celery, Gunicorn | PostgreSQL + Elasticsearch |
| `hypothesis/lms` | Integración LTI con LMS educativos | Python 3.11 + Pyramid, Celery, Gunicorn | PostgreSQL separada |
| `hypothesis/client` | Cliente JS inyectable en páginas web | TypeScript + Preact + Redux, Rollup | Sin BD propia |

---

### 1.2 Infraestructura

```
┌─────────────────────────────────────────────────────────────┐
│                    AWS (us-west-1 + ca-central-1)           │
│                                                             │
│  ElasticBeanstalk: h (web) + h-websocket                   │
│  ElasticBeanstalk: lms (web + Celery workers)              │
│                                                             │
│  RDS PostgreSQL: BD h  ──FDW──  RDS PostgreSQL: BD lms     │
│  Elasticsearch 7.10 (índice annotations)                    │
│  RabbitMQ 3.12 (colas: celery, annotation, email_digests)  │
│  S3 (assets) · CloudFront (CDN) · Route53 (DNS)            │
└─────────────────────────────────────────────────────────────┘
```

---

### 1.3 Integraciones Externas

| Sistema | Tipo | Riesgo |
|---------|------|--------|
| Canvas, Blackboard, D2L, Moodle | LMS (bidireccional) | 🔴 Crítico — ver R9 |
| JSTOR, VitalSource, YouTube | Contenido (entrada) | 🟡 Medio |
| HubSpot | CRM (salida, Celery diaria) | 🟡 Medio — contiene datos de revenue |
| Sentry, New Relic | Observabilidad (salida) | 🟢 Bajo |
| Google Analytics | Analytics (salida) | 🟢 Bajo — uso no confirmado |

---

### 1.4 Flujo de datos

```
UNIVERSIDAD → (LTI Launch) → LMS
                               ↓ H Bulk API + JWT Token
                          H ←→ CLIENT (anotaciones)
                          ↓ RabbitMQ
                     LMS Celery (emails, calificaciones, HubSpot)
```

---

## Revenue Data Assessment

**Hallazgo:** Los datos de monetización no están en las bases de datos de la aplicación. Uso y dinero viven en sistemas separados — hoy no es posible correlacionar nivel de adopción con riesgo de churn o probabilidad de renovación.

| Dato | Encontrado | Ubicación probable |
|------|------------|--------------------|
| Clientes / Universidades | ✅ Parcial | `organization` + `application_instances` |
| Estudiantes activos | ✅ | `lms_user` (lms) |
| Contratos y renovaciones | ❌ | HubSpot |
| Licencias y pricing | ❌ | HubSpot / billing externo |
| Facturación | ❌ | Billing externo |
| Churn real | ❌ | Proxy: `application_instances.last_launched` |

**Proxy de salud por institución** (ejecutar query 10 de Volumetría Real).

**Acciones recomendadas:** Acceso a HubSpot + entrevistas con Finance/CS/Sales.

---

## Mapa de Ownership de Datos

| Dominio | Dueño funcional | Sistema | Estado governance |
|---------|----------------|---------|------------------|
| Annotations | Product / Backend | `h` | Sin governance formal |
| Users & Auth | Platform / Backend | `h` | Sin governance formal |
| LMS Integration | LMS/EdTech Team | `lms` | Sin governance formal |
| Courses & Assignments | LMS/EdTech Team | `lms` | Sin governance formal |
| Grading | LMS/EdTech Team | `lms` | Sin governance formal |
| Organizations / Billing | Finance / Sales | HubSpot + externo | Desconectado de uso |
| CRM / Contracts | Sales | HubSpot | Desconectado de uso |
| Analytics | **Data Engineering** | ⚠️ No existe aún | **Por crear** |

> Sin un dueño transversal de datos, cada equipo define sus propias métricas. "Usuario activo" puede significar cosas distintas para Product, CS y Finance.

---

## Evaluación de Riesgos

| # | Riesgo | Severidad | Impacto en negocio | Acción |
|---|--------|-----------|-------------------|--------|
| R1 | Analytics service no implementado (`TODO` en código) | 🔴 Crítico | Pérdida permanente de información de engagement. Implementación correcta = 3-6 semanas, no días (ver 4.4) | Diseño de sistema de eventos en Sprint 1. Implementación en Fase 1 |
| R2 | Sin tracking de sesiones ni tiempo de uso | 🔴 Alto | No se puede demostrar valor a universidades | Session tracking en client — parte del sistema de eventos |
| R3 | Eventos de anotación no persistidos en h | 🔴 Alto | Sin fuente de verdad para actividad histórica | Tabla `annotation_event` en h como parte de Fase 1 |
| R4 | **LTI params purgados a 30 días** | 🔴 **Crítico** | **Destruye la capacidad de Learning Analytics histórico y reportes YoY** — ver análisis completo abajo | **S3 cold archive inmediato antes de la próxima ejecución del purge** |
| R5 | Datos de revenue fuera del sistema | 🟡 Medio | No se puede correlacionar uso con ingresos | Pipeline HubSpot → DW |
| R6 | Dependencia de joins h ↔ lms via `h_userid` | 🟡 Medio | Complejidad analítica. Un error rompe todos los análisis | Validar integridad (ejecutar queries de Sección 3.4) |
| R7 | Elasticsearch 7.10 en EOL | 🟡 Medio | Riesgo de seguridad a mediano plazo | Planificar upgrade |
| R8 | Sin tipo de recurso normalizado | 🟢 Bajo | No se puede segmentar uso por tipo de material | Campo `resource_type` en `assignment` |
| R9 | **Dependencia crítica de LMS externos** | 🔴 Alto | Si cualquier LMS cambia su API: launches fallan, sync falla, calificaciones fallan | Monitoreo activo de changelogs LMS. Versionado de integraciones. Alertas tempranas |

### R4 — Análisis detallado: LTI params purgados a 30 días

**Qué hace el código realmente** (`lms/lms/tasks/event.py`):

```python
@app.task
def purge_launch_data(*, max_age_days=30) -> None:
    # Elimina el key 'lti_params' del JSONB en EventData.data
    # Solo opera en eventos de 30 a 60 días de antigüedad
    # NO borra la fila del evento — solo el campo lti_params del JSON
    update(EventData).values(data=EventData.data - "lti_params")
```

**Lo que sobrevive** a la purga:
- La fila completa en `event` (timestamp, type, application_instance_id, course_id, assignment_id, grouping_id)
- `event_user` (usuario + rol al momento del evento)

**Lo que se pierde permanentemente** después de 30 días:
| Campo perdido | Por qué importa para analytics |
|---------------|-------------------------------|
| `context_title` (nombre del curso) | Si el curso fue renombrado, el nombre histórico se pierde — los reportes YoY no pueden mostrar "Introducción a la Biología 2024 vs 2025" |
| `lis_person_contact_email_primary` | Email del usuario al momento del launch. Crucial para identidad histórica si cambió su email |
| Campos de término académico (`custom_*`) | Canvas y otros LMS envían término, semestre, cohorte como custom params — no están en columnas estructurales |
| `tool_consumer_instance_guid` | Identificador de la instancia LMS al momento del evento |
| Parámetros custom del LMS | Cada institución puede enviar datos propios (código de departamento, nivel del curso, modalidad) |

**Por qué es Crítico y no Medio:**
Los reportes semestrales y YoY que los compradores universitarios usan para justificar renovaciones requieren contexto histórico. Con la purga a 30 días, cualquier reporte sobre "Semester Spring 2024 vs Spring 2025" pierde el contexto del término académico si ese dato vivía en lti_params y no en una columna estructural.

**Solución de ingeniería inmediata** (prioridad antes del próximo ciclo de purge):

```python
# Modificar purge_launch_data() para archivar ANTES de eliminar
import boto3, json

@app.task
def purge_launch_data(*, max_age_days=30) -> None:
    s3 = boto3.client('s3')
    events_to_purge = ... # query existente

    # 1. Archivar a S3 cold storage (Glacier Instant Retrieval ~$0.004/GB/mes)
    archive_data = [
        {"event_id": row.event_id, "lti_params": row.data["lti_params"]}
        for row in events_to_purge if "lti_params" in row.data
    ]
    s3.put_object(
        Bucket='hypothesis-lti-archive',
        Key=f'lti_params/{datetime.utcnow().strftime("%Y/%m/%d")}.json.gz',
        Body=gzip.compress(json.dumps(archive_data).encode())
    )

    # 2. Ejecutar purge original
    # ... código existente ...
```

**Costo estimado del archivo:** A $0.004/GB/mes (Glacier), incluso con millones de eventos el costo es negligible. La retención histórica es invaluable.

---

## Bloque 2 — Modelo de Datos

### 2.1 Entidades estratégicas del negocio

| Entidad | Tabla(s) fuente | Sistema | Descripción |
|---------|----------------|---------|-------------|
| **Institution** | `organization`, `application_instances` | lms | Universidad cliente. Unidad de contrato y revenue |
| **Student** | `lms_user` (rol learner), `user` (h) | lms + h | Usuario que anota y colabora |
| **Instructor** | `lms_user` (rol instructor), `user` (h) | lms + h | Usuario que configura y evalúa |
| **Course** | `lms_course`, `grouping` | lms | Contexto educativo del uso |
| **Assignment** | `assignment` | lms | Tarea que involucra anotar un recurso |
| **Resource** | `assignment.document_url`, `file`, `document` | lms + h | Material educativo (PDF, video, HTML, libro) |
| **Annotation** | `annotation` | h | Acción central del producto — el valor entregado |
| **Session** | ❌ No existe | — | Período de uso continuo. Debe construirse |

---

### 2.2 Inventario de tablas — BD `h` (31 tablas)

| Tabla | Descripción | PK | FKs principales |
|-------|-------------|-----|----------------|
| `user` | Usuarios con perfil, estado, flags (admin, staff, nipsa, deleted) | `id` | `activation_id` |
| `user_identity` | Identidades externas (ORCID, Google, Facebook) | `id` | `user_id` |
| `activation` | Tokens de activación | `id` | — |
| `authclient` | Clientes OAuth 2.0 | `id (UUID)` | — |
| `authzcode` | Códigos de autorización OAuth | `id` | `user_id`, `authclient_id` |
| `authticket` | Tickets de sesión web | `id` | `user_id` |
| `token` | API tokens de acceso y refresh | `id` | `user_id`, `authclient_id` |
| `group` | Grupos de anotación | `id` | `creator_id → user`, `organization_id` |
| `user_group` | Membresía usuario-grupo con roles JSONB | `id` | `user_id`, `group_id` |
| `groupscope` | Alcance de URLs del grupo | `id` | `group_id` |
| `organization` | Organizaciones | `id` | — |
| `annotation` | **Tabla central.** Texto, tags, selectores, moderación | `id (UUID)` | `document_id` |
| `annotation_slim` | Vista desnormalizada para queries rápidas | `id` | `pubid → annotation`, `user_id`, `group_id`, `document_id` |
| `annotation_metadata` | Metadata extendida JSONB | `annotation_id` | `annotation_id → annotation_slim` |
| `document` | Documento web anotado | `id` | — |
| `document_uri` | URIs concretas del documento | `id` | `document_id` |
| `document_meta` | Metadata (título, autor) | `id` | `document_id` |
| `mention` | Menciones `@usuario` | `id` | `annotation_id`, `user_id` |
| `notification` | Notificaciones (reply, mention) | `id` | `source_annotation_id`, `recipient_id` |
| `flag` | Reportes de anotaciones | `id` | `annotation_id`, `user_id` |
| `moderation_log` | Log de cambios de moderación | `id` | `annotation_id`, `moderator_id` |
| `subscriptions` | Preferencias de notificación | `id` | — |
| `feature` | Feature flags | `id` | — |
| `featurecohort` | Grupos para A/B testing | `id` | — |
| `featurecohort_user` | Relación usuario-cohorte | `id` | `user_id`, `cohort_id` |
| `featurecohort_feature` | Relación cohorte-feature | `id` | `feature_id`, `cohort_id` |
| `job` | Cola de jobs internos | `id` | — |
| `task_done` | Registro de tareas completadas | `id` | — |
| `user_deletion` | Auditoría de borrado de usuarios | `id` | — |
| `blocklist` | URIs bloqueadas | `id` | — |
| `setting` | Key-value settings del sistema | `key` | — |

---

### 2.3 Inventario de tablas — BD `lms` (30 tablas)

| Tabla | Descripción | PK | FKs principales |
|-------|-------------|-----|----------------|
| `organization` | Universidad / institución cliente | `id` | `parent_id → organization` |
| `application_instances` | Instalación de Hypothesis en un LMS | `id` | `organization_id`, `lti_registration_id` |
| `lti_registration` | Registro LTI 1.3 | `id` | — |
| `lms_user` | Usuario canónico con `h_userid` para vincular con h | `id` | — |
| `user` | Usuario en contexto de instancia específica | `id` | `application_instance_id` |
| `lms_user_application_instance` | Relación usuarios-instancias | `id` | `lms_user_id`, `application_instance_id` |
| `lms_term` | Período académico con fechas | `id` | — |
| `lms_course` | Curso en el LMS | `id` | `lms_term_id` |
| `lms_course_application_instance` | Relación curso-instancia | `id` | `lms_course_id`, `application_instance_id` |
| `lms_course_membership` | Membresía usuarios-cursos con rol LTI | `id` | `lms_course_id`, `lms_user_id`, `lti_role_id` |
| `lti_role` | Roles LTI (instructor, learner, admin) | `id` | — |
| `lti_role_override` | Override de roles por instancia | `id` | `lti_role_id`, `application_instance_id` |
| `grouping` | Entidad polimórfica: curso, sección, grupo | `id` | `application_instance_id`, `parent_id → grouping` |
| `grouping_membership` | Membresía usuarios-groupings | `(grouping_id, user_id)` | ambas FKs |
| `group_info` | Información legacy de grupos LMS | `id` | `application_instance_id` |
| `assignment` | Asignación con URL del documento a anotar | `id` | `course_id → grouping`, `auto_grading_config_id` |
| `assignment_auto_grading_config` | Configuración de auto-calificación | `id` | — |
| `assignment_grouping` | Relación asignaciones-groupings | `(assignment_id, grouping_id)` | ambas FKs |
| `file` | Archivo del LMS en una asignación | `id` | `application_instance_id` |
| `grading_sync` | Proceso de sincronización de calificaciones | `id` | `assignment_id`, `created_by_id → lms_user` |
| `grading_sync_grade` | Calificación individual de estudiante | `id` | `grading_sync_id`, `lms_user_id` |
| `lis_result_sourcedid` | Info de calificación LTI 1.1 (legacy) | `id` | `application_instance_id` |
| `oauth2_token` | Tokens OAuth2 para APIs LMS | `id` | `application_instance_id` |
| `jwt_oauth2_token` | Tokens JWT para LTI 1.3 | `id` | `lti_registration_id` |
| `rsa_key` | Claves RSA para firma JWT | `id` | — |
| `event` | **Tabla de eventos LMS** | `id` | `type_id`, `application_instance_id`, `course_id`, `assignment_id` |
| `event_type` | Catálogo de tipos de evento | `id` | — |
| `event_user` | Usuarios en un evento con su rol | `id` | `event_id`, `user_id`, `lti_role_id` |
| `event_data` | Datos extra del evento en JSONB | `event_id` | `event_id → event` |
| `notification` | Notificaciones reply/mention en contexto LMS | `id` | `sender_id`, `recipient_id → lms_user`, `assignment_id` |

---

### 2.4 Relaciones entre BDs

```
lms.lms_user.h_userid  ←→  h.user.userid  (formato: acct:username@authority)
lms.grouping.authority_provided_id  ←→  h.group.authority_provided_id
```

La BD `lms` puede leer la BD `h` via **Foreign Data Wrapper (FDW)**.

---

## Bloque 3 — Calidad de Datos

*Ejecutar en producción. Resultados a completar en Volumetría Real.*

### 3.1 Completitud

```sql
-- Usuarios sin email (BD h)
SELECT COUNT(*), COUNT(*) FILTER (WHERE email IS NULL) AS sin_email
FROM "user" WHERE deleted = false;

-- Anotaciones sin target_uri
SELECT COUNT(*) FROM annotation WHERE target_uri IS NULL OR target_uri = '';

-- Usuarios LMS sin h_userid (BD lms)
SELECT COUNT(*) FROM lms_user WHERE h_userid IS NULL;

-- Eventos sin usuario (BD lms)
SELECT COUNT(*) FROM event e
LEFT JOIN event_user eu ON eu.event_id = e.id WHERE eu.user_id IS NULL;
```

### 3.2 Duplicados

```sql
-- Emails duplicados por authority (BD h)
SELECT email, authority, COUNT(*) AS n FROM "user"
WHERE email IS NOT NULL AND deleted = false
GROUP BY email, authority HAVING COUNT(*) > 1 ORDER BY n DESC LIMIT 20;

-- h_userid duplicados (BD lms)
SELECT h_userid, COUNT(*) FROM lms_user GROUP BY 1 HAVING COUNT(*) > 1;
```

### 3.3 Consistencia

```sql
SELECT COUNT(*) FROM annotation WHERE updated < created; -- Fechas invertidas (BD h)
SELECT COUNT(*) FROM grading_sync_grade WHERE grade < 0 OR grade > 1; -- Notas inválidas (BD lms)
SELECT COUNT(*) FROM lms_course WHERE ends_at < starts_at; -- Fechas de curso inválidas (BD lms)
```

### 3.4 Integridad Referencial

```sql
-- annotation_slim sin annotation padre (BD h)
SELECT COUNT(*) FROM annotation_slim asm
WHERE NOT EXISTS (SELECT 1 FROM annotation a WHERE a.id = asm.pubid);

-- Eventos con application_instance inexistente (BD lms)
SELECT COUNT(*) FROM event e
WHERE application_instance_id IS NOT NULL
  AND NOT EXISTS (SELECT 1 FROM application_instances ai WHERE ai.id = e.application_instance_id);
```

---

## Bloque 4 — Assessment de Tracking

### 4.1 Eventos existentes

#### BD `lms` — Persistidos

| Evento | Descripción |
|--------|-------------|
| `configured_launch` | Usuario abre Hypothesis desde el LMS |
| `deep_linking` | Profesor configura asignación nueva |
| `edited_assignment` | Profesor edita asignación existente |
| `submission` | Estudiante envía trabajo |
| `grade` | Sistema sincroniza calificación |
| `audit` | Cambios en modelos (audit trail) |
| `error_code` | Error durante acción LTI |

> LTI params purgados a 30 días automáticamente — contexto histórico perdido (ver R4 Crítico).

#### BD `h` — En memoria, no persistidos

| Evento | Traza disponible |
|--------|-----------------|
| `AnnotationEvent (create/update/delete)` | Solo tabla `annotation` |
| `ModeratedAnnotationEvent` | Solo `moderation_log` |
| `LoginEvent / LogoutEvent / ActivationEvent` | Solo logs, no persistidos |

---

### 4.2 Cobertura

| Acción | Trackeado | Dónde |
|--------|-----------|-------|
| Abrir desde LMS | ✅ | `event.configured_launch` |
| Crear anotación | ⚠️ | Solo tabla `annotation` |
| Responder | ⚠️ | `annotation.references` (inferido) |
| Mencionar | ✅ | `mention` (h) |
| Calificación | ✅ | `grading_sync_grade` (lms) |
| **Abrir recurso (PDF/video)** | ❌ | — |
| **Tiempo de uso** | ❌ | — |
| **Búsqueda** | ❌ | — |
| **Sesión** | ❌ | — |

### 4.3 Frecuencia

```sql
-- Eventos por tipo y mes (BD lms)
SELECT DATE_TRUNC('month', e.timestamp) AS mes, et.type, COUNT(*),
  COUNT(DISTINCT e.application_instance_id) AS instituciones
FROM event e JOIN event_type et ON et.id = e.type_id
GROUP BY 1, 2 ORDER BY 1 DESC, 3 DESC;

-- Anotaciones por mes (BD h)
SELECT DATE_TRUNC('month', created) AS mes, COUNT(*),
  COUNT(DISTINCT userid) AS usuarios,
  COUNT(*) FILTER (WHERE array_length(references, 1) > 0) AS replies
FROM annotation WHERE deleted = false GROUP BY 1 ORDER BY 1 DESC LIMIT 24;
```

---

### 4.4 Análisis técnico: por qué el analytics endpoint lleva años como TODO

**Lo que el código hace hoy** (`h/h/services/analytics.py`):

```python
class AnalyticsService:
    def create(self, event: Event):
        # TODO Enhance this
        self._log.info(event)  # ← es literalmente un logger. No hay BD, no hay tabla.
```

El endpoint existe (`POST /api/v1/analytics/events`), el schema valida exactamente 1 tipo de evento (`client.realtime.apply_updates` — disparado cuando un usuario hace clic en "aplicar actualizaciones" del panel de notificaciones en tiempo real). El cliente lo envía correctamente. El backend simplemente lo descarta al log.

**Por qué no se implementó en los sprints anteriores:**

No fue un olvido. La implementación correcta es un problema de sistemas distribuidos, no de "agregar una tabla":

| Problema | Detalle |
|----------|---------|
| **Write amplification** | Canvas tiene decenas de miles de estudiantes simultáneos. Cada uno genera múltiples eventos por sesión. Si cada evento es un POST síncrono → write en el mismo PostgreSQL OLTP que sirve annotations, auth y API: contención garantizada bajo carga |
| **Schema demasiado estrecho** | Solo acepta 1 evento (`apply_updates`). Para Learning Analytics útil necesitas 10-20 tipos: annotation_created, resource_opened, session_started, session_ended, search_performed, highlight_created, etc. Requiere rediseño completo |
| **Auth overhead por evento** | Cada POST pasa por el stack completo de Pyramid (JWT decode, session validation, routing). Para eventos de alta frecuencia, esto agrega latencia innecesaria en cada request |
| **Sin batching** | El client envía un POST por evento. A escala, esto significa miles de requests/minuto adicionales al API |
| **RabbitMQ no es la solución** | RabbitMQ está configurado para Celery task queues. No está diseñado ni dimensionado para streaming de eventos de comportamiento a esta escala |

**Arquitectura correcta para implementarlo** (3-6 semanas, 1 Data + 1 Backend Engineer):

```
CLIENT (batching local cada 30s)
    ↓ POST /api/analytics/events (payload: batch de eventos)
H API (validación ligera de JWT, sin sesión completa)
    ↓ publicar a SQS (desacoplamiento, no bloquea la API)
AWS Lambda consumer (o Celery worker dedicado)
    ↓ escribir a tabla analytics_event SEPARADA del OLTP
    └→ (opcional) exportar a S3 Parquet para Athena
```

**Taxonomía de eventos prioritarios a capturar:**

| Evento | Prioridad | Métricas que habilita |
|--------|-----------|----------------------|
| `session.started` | 🔴 Alta | Tiempo de uso, DAU real |
| `session.ended` (con duración) | 🔴 Alta | Tiempo promedio por sesión, engagement real |
| `resource.opened` (type: pdf/video/html) | 🔴 Alta | Apertura de recurso, embudo launch→apertura |
| `annotation.created` | 🔴 Alta | Evento explícito (hoy solo inferido de tabla) |
| `annotation.reply_created` | 🔴 Alta | Collaboration Index real |
| `resource.scrolled` (% leído) | 🟡 Media | Reading depth, proxy de lectura activa |
| `search.performed` | 🟡 Media | Discovery patterns |
| `annotation.highlight_created` | 🟡 Media | Engagement sin anotación escrita |

**Estimación realista:**
- **Mal implementado (directo a PostgreSQL OLTP):** 3 días, funcionará en dev, fallará en producción bajo carga real.
- **Bien implementado (SQS buffer + tabla dedicada + client batching):** 3-6 semanas. Esta es la única versión que vale la pena construir.

---

## Bloque 5 — Modelo Analítico Futuro

### 5.1 Arquitectura target — AWS-native

La propuesta de infraestructura analítica está diseñada para el stack AWS que ya existe en producción. No se introducen herramientas externas hasta que la carga lo justifique.

```
┌──────────────────────────────────────────────────────────────────┐
│                         DATA SOURCES                             │
│   RDS h (annotations) · RDS lms (events/grades) · HubSpot · S3  │
└─────────────────────────────┬────────────────────────────────────┘
                              │
              ┌───────────────┼──────────────────┐
              │ CDC continuo  │ Batch diario      │ API pull
              ▼               ▼                   ▼
        AWS DMS           AWS Glue ETL       Lambda custom
    (replica changes    (transforma y       (HubSpot, GA)
     de RDS en tiempo   carga a S3)
     casi real)
              └───────────────┼──────────────────┘
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                     DATA LAKE (S3)                               │
│   Formato: Apache Parquet · Particionado por fecha e institución  │
│   Capas: raw/ · staging/ · business/                             │
│   Catálogo: AWS Glue Data Catalog (schema registry)             │
└─────────────────────────────┬────────────────────────────────────┘
                              │ dbt transformations
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                       BUSINESS LAYER                             │
│   DimInstitution · DimUser · DimCourse · DimAssignment           │
│   DimResource · DimDate                                          │
│   FactAnnotations · FactEvents · FactGrades · FactSessions       │
│   Métricas gobernadas: MAS, MAI, AnnotationRate, HealthScore     │
└──────────────────────────────┬───────────────────────────────────┘
                               │ consulta serverless
                               ▼
                     Amazon Athena (SQL sobre S3)
                (escala automáticamente, sin instancia
                 permanente que mantener, pago por query)
                               │
          ┌────────────────────┼─────────────────────┐
          ▼                    ▼                      ▼
   Amazon QuickSight    Metabase (self-hosted    API / Embedded
   (embedded BI         EC2, ~$50/mes,           (in-product
    dashboards,         alternativa económica     dashboards)
    sin servidor)       a QuickSight)
```

**Orquestación:** Amazon EventBridge Scheduler para jobs simples (diarios/semanales). AWS Step Functions para pipelines con dependencias. Amazon MWAA (managed Airflow) solo si la complejidad lo justifica en Fase 3.

---

### 5.2 Justificación del stack AWS-native

| Herramienta rechazada | Por qué no | Alternativa AWS |
|----------------------|------------|-----------------|
| Airbyte | Overhead de mantenimiento (servidor propio o cloud $$$). Justifica solo a escala alta. Sin beneficio vs DMS para RDS→S3 | AWS DMS (CDC) + AWS Glue (batch ETL) — ya gestionados, en el mismo VPC |
| BigQuery | Multi-cloud. Datos salen de AWS a GCP. Latencia de red, costos de egress, dos proveedores cloud que gestionar | Amazon Athena sobre S3: serverless, mismo región, pago por query ejecutada |
| Redshift (provisioned) | Costo fijo ~$180-250/mes mínimo. Sobre-dimensionado para empezar | Athena primero (pay-per-query). Redshift Serverless solo si queries > 10TB/mes frecuentes |
| Airflow/Dagster (self-hosted) | Servidor adicional, mantenimiento. Innecesario para pipelines simples | EventBridge Scheduler (cron jobs) + Step Functions (pipelines con estados) |
| Looker | Licencia enterprise $$$. Injustificable en Fase 2 | Amazon QuickSight (embedded) o Metabase (self-hosted, open source) |

**Costo estimado del stack AWS-native:**
| Componente | Costo estimado/mes |
|------------|-------------------|
| AWS DMS (t3.micro) | ~$15 |
| S3 (100GB Parquet) | ~$2.50 |
| AWS Glue (10 DPU-horas/día) | ~$13 |
| Amazon Athena (100GB queries/mes) | ~$5 |
| Metabase (EC2 t3.small self-hosted) | ~$15 |
| **Total Fase 2** | **~$50/mes** |

vs. Airbyte Cloud (~$200+) + BigQuery (~$100+ según uso) + Looker ($$$).

---

### 5.3 Esquema estrella

| Tabla | Tipo | Fuente | Factibilidad |
|-------|------|--------|-------------|
| `DimDate` | Dimensión | Generada | ✅ Hoy |
| `DimInstitution` | Dimensión | `organization` + `application_instances` | ✅ Hoy |
| `DimUser` | Dimensión | `lms_user` + `user` (h) | ✅ Hoy |
| `DimCourse` | Dimensión | `lms_course` + `lms_term` | ✅ Hoy |
| `DimAssignment` | Dimensión | `assignment` | ✅ Hoy |
| `DimResource` | Dimensión | `file` + `document` | ✅ Hoy |
| `FactAnnotations` | Hecho | `annotation` (h) | ✅ Hoy |
| `FactEvents` | Hecho | `event` + `event_user` (lms) | ✅ Hoy |
| `FactGrades` | Hecho | `grading_sync_grade` (lms) | ✅ Hoy |
| `FactSessions` | Hecho | — | ❌ Requiere sistema de eventos (Fase 1) |

---

## Bloque 6 — Roadmap

> **Principio guía:** Tracking → Data Layer → Data as a Product. **Las Fases 1 y 2 se solapan desde el mes 2.** CS no puede esperar 18 meses — necesita un proxy de churn funcional en el mes 2, no en el mes 18.

---

### Fase 1 — Tracking Foundation (meses 1-3)

**Objetivo:** Capturar los datos que hoy se pierden. Sin estos datos, el DW organizará información incompleta.
**Equipo:** 1 Data Engineer + 1 Frontend Engineer (part-time).
**Costo estimado:** 2-3 meses de trabajo. Infraestructura: ~$30/mes adicional (SQS + tabla analytics).

| Iniciativa | Prioridad | Semanas | Impacto en revenue | Outcome esperado |
|------------|-----------|---------|-------------------|-----------------|
| **S3 cold archive de LTI params** | 🔴 Inmediata (antes del próximo purge) | 0.5 | Preserva datos históricos ya existentes | Reportes YoY posibles. Sin esto, datos históricos irrecuperables |
| **Diseño del sistema de eventos** | 🔴 Alta | 1 | Fundacional | Taxonomía de eventos + arquitectura definida. Evita reescribir |
| **Analytics endpoint (write-path correcto)** | 🔴 Alta | 4-6 | Base de todo analytics futuro | SQS buffer + tabla `analytics_event` dedicada + client batching |
| **Session tracking** | 🔴 Alta | 2 | Tiempo de uso → mejora argumentos de renovación | Primera métrica de engagement real |
| **Resource tracking (PDF/video/HTML)** | 🔴 Alta | 1 | Segmentación por tipo de contenido | Product prioriza inversión por tipo |
| **Annotation events explícitos** | 🟡 Media | 1 | Actividad histórica reconstruible | Fuente de verdad para analytics de anotaciones |

---

### Inicio Fase 2: Mes 2 (paralela con Fase 1)

**El primer dashboard de CS no requiere el DW ni el tracking completo.** Los datos en `lms.event` + `lms.application_instances` + `h.annotation` ya son suficientes para un proxy de salud básico.

**CS Churn MVP — Meta: operativo en el mes 2:**

```sql
-- Dashboard proxy de salud (ejecutable hoy, sin DW)
-- Implementar como vista en Metabase conectado a RDS read replica
SELECT
    o.name                                             AS institucion,
    ai.last_launched,
    COUNT(DISTINCT e.id) FILTER (
        WHERE e.timestamp > NOW() - INTERVAL '90 days'
        AND et.type = 'configured_launch'
    )                                                  AS launches_90d,
    COUNT(DISTINCT eu.user_id)                         AS usuarios_unicos_90d,
    CASE
        WHEN ai.last_launched > NOW() - INTERVAL '30 days'  THEN '🟢 Saludable'
        WHEN ai.last_launched > NOW() - INTERVAL '90 days'  THEN '🟡 Atención'
        ELSE '🔴 Riesgo de churn'
    END                                                AS estado
FROM organization o
JOIN application_instances ai ON ai.organization_id = o.id
LEFT JOIN event e ON e.application_instance_id = ai.id
LEFT JOIN event_type et ON et.id = e.type_id
LEFT JOIN event_user eu ON eu.event_id = e.id
GROUP BY 1, 2 ORDER BY launches_90d DESC;
```

---

### Fase 2 — Data Layer MVP (meses 2-5)

**Objetivo:** Centralizar y gobernar los datos. Usar el stack AWS que ya existe.
**Equipo:** 2 Data Engineers.
**Costo estimado:** 3-4 meses de trabajo. Infraestructura: ~$50/mes (ver tabla Sección 5.2).

| Iniciativa | Semanas | Impacto en revenue | Outcome esperado |
|------------|---------|-------------------|-----------------|
| **AWS DMS replication de RDS → S3** | 2 | Habilita toda la capa analítica | Réplica continua a bajo costo sin tocar OLTP |
| **Data Lake S3 + Glue Data Catalog** | 1 | Fundacional para queries | Schema versionado, particionado por fecha |
| **dbt models (staging + business layer)** | 3 | Datos confiables y actualizados | Modelo estrella operativo con datos frescos diarios |
| **Pipeline HubSpot → S3** | 2 | **Revenue + uso en un solo lugar** | CS puede ver churn risk + valor contractual juntos |
| **Metabase sobre Athena** | 1 | CS + Sales tienen visibilidad | Primer BI funcional sin licencias enterprise |
| **KPIs gobernados + glosario** | 1 | Alineación organizacional | "Usuario activo" tiene una sola definición en toda la compañía |

---

### Fase 3 — Analytics as a Product (meses 5-12)

**Objetivo:** Reducir churn, mejorar renovaciones, demostrar ROI educativo, incrementar adopción orgánica.
**Equipo:** Squad dedicada (2 DE + 1 Data Analyst + 1 PM).
**Costo estimado:** 6-8 meses.

| Iniciativa | Impacto en revenue | Outcome de negocio |
|------------|-------------------|-------------------|
| **Dashboard institucional (para clientes)** | 🔴 **Arma la conversación de renovación** | El comprador ve ROI antes de la reunión de renovación. Tasa de renovación mejora |
| **Health Score automatizado + alertas CS** | 🔴 Detección temprana de churn | CS prioriza proactivamente. Cada cliente salvado = ARR preservado |
| **Dashboard de curso para instructores** | 🔴 Stickiness del producto | Instructores ven engagement de sus alumnos → NPS sube → menos churn orgánico |
| **Predicción de churn (modelo ML)** | 🔴 Retención proactiva | Identificar en riesgo 60-90 días antes de decisión. Intervención temprana |
| **Benchmarking institucional** | 🟡 Argumento de upsell | "Tu universidad genera 23% más anotaciones que instituciones similares" |
| **Learning Analytics metrics** | 🟡 Diferenciación competitiva | Annotation Density, Collaboration Index, At-Risk Index como oferta premium |
| **Self-Service Analytics** | 🟡 Autonomía interna | Equipos responden sus propias preguntas sin depender de DE |

---

### Timeline consolidado

```
Mes 1:   [F1] S3 archive LTI params · Diseño sistema eventos · Resource tracking
Mes 2:   [F1] Analytics endpoint (diseño + inicio impl.) · [F2-INICIO] CS Dashboard MVP
Mes 3:   [F1] Analytics endpoint (finalización) · Session tracking · [F2] DMS + Data Lake
Mes 4:   [F2] dbt models · Pipeline HubSpot · Metabase operativo
         ★ CS TIENE DASHBOARD DE CHURN REAL (no proxy) EN MES 4
Mes 5:   [F2] KPIs gobernados · [F3-INICIO] Dashboard institucional
Mes 6-8: [F3] Health Score · Alertas CS · Dashboard instructores
Mes 9-12:[F3] Predicción churn · Learning Analytics · Self-Service
```

**Total: 12 meses** (vs 24 meses en versión anterior)

---

## Compliance & Privacy

> En EdTech, privacidad no es opcional. Es un requisito de venta para universidades enterprise.

Dado que Hypothesis procesa datos educativos y comportamiento de estudiantes, cualquier estrategia analítica debe considerar:

| Regulación / Estándar | Aplicabilidad | Implicación para analytics |
|----------------------|--------------|---------------------------|
| **FERPA** (Family Educational Rights and Privacy Act) | 🔴 Alta — universidades USA | Datos de estudiantes son confidenciales. Analytics debe estar anonimizado o con consentimiento institucional |
| **GDPR** | 🟡 Media — universidades EU | Requiere base legal para procesamiento de datos de comportamiento. Derecho al olvido impacta pipelines |
| **COPPA** | 🟡 Potencial | Si hay usuarios menores de 13 años (edge case en educación superior) |
| **Minimización de datos** | 🟢 Best practice | Capturar solo lo necesario. No trackear más de lo que se va a usar |
| **Retención de datos** | 🟡 Media | Definir políticas de retención para eventos analíticos. ¿Cuánto tiempo se guarda una sesión? |
| **Anonimización** | 🔴 Alta | Los dashboards para clientes deben mostrar métricas agregadas, no datos individuales de estudiantes |

**Recomendación inmediata:** Antes de implementar session tracking, definir con Legal qué datos pueden capturarse y por cuánto tiempo. Esto evita rediseñar el sistema después de construirlo.

---

## Competitive Advantage Through Data — Learning Analytics

> Esta es la oportunidad estratégica más importante del assessment.

La mayoría de los LMS tradicionales (Canvas, Blackboard, Moodle) tienen analytics débiles orientados a actividad de navegación: páginas visitadas, videos reproducidos, tiempo en plataforma. Estas métricas miden **presencia**, no **aprendizaje**.

**Hypothesis tiene una oportunidad única y diferencial:**

La anotación es interacción cognitiva. Cuando un estudiante anota un texto, está:
- Procesando activamente el contenido (no pasivamente)
- Produciendo evidencia de comprensión
- Colaborando intelectualmente con sus pares

Esto significa que los datos de Hypothesis no son analytics operacionales — son **Learning Analytics**: métricas de engagement intelectual que los LMS tradicionales no pueden medir.

**Métricas de Learning Analytics posibles con los datos actuales:**

| Métrica | Descripción | Implicación pedagógica |
|---------|-------------|----------------------|
| **Annotation Density** | Anotaciones por página / por recurso | Indica profundidad de lectura |
| **Collaboration Index** | Replies / anotaciones totales | Mide diálogo académico entre pares |
| **Cognitive Engagement Score** | Longitud de anotaciones + menciones + replies | Proxy de procesamiento profundo |
| **Knowledge Construction Rate** | Nuevas anotaciones vs replies | Balance entre producción y diálogo |
| **At-Risk Index** | Estudiantes sin actividad en X días | Señal temprana de desenganche |

**Implicación comercial:** Hypothesis puede posicionarse no como "herramienta de anotación" sino como **"plataforma de evidencia de aprendizaje activo"** — una categoría premium que justifica pricing más alto y diferencia claramente del commoditized LMS.

Este posicionamiento también facilita ventas a universidades con mandatos de accesibilidad, equity o evidencia de aprendizaje activo (creciente en educación superior).

---

## Oportunidades de Producto Basadas en Datos

### Para universidades (compradores)
- **Dashboard institucional**: actividad semestral, comparación YoY, evolución de adopción
- **Reporte de valor automático**: PDF generado en el momento de renovación con impacto del año
- **Benchmarking**: "Su universidad genera X% más anotaciones por estudiante que el promedio"

### Para instructores (usuarios power)
- **Dashboard de curso**: participación por alumno, alumnos sin actividad, recursos más anotados
- **Alerta temprana**: "3 estudiantes no han abierto Hypothesis en 7 días"
- **Digest semanal automático**: resumen de actividad del curso

### Para el equipo interno (CS/Sales)
- **Health Score por cliente**: adopción + engagement + tendencia
- **Churn Risk Score**: actividad reciente vs historial + fecha de renovación
- **Pipeline de expansión**: clientes que usan 1 LMS pero tienen más disponibles

---

## Recomendación Organizacional

La estrategia de datos descrita en este documento no puede ejecutarse sin los cambios organizacionales correspondientes.

**Para ejecutar la Fase 1:** No se requieren cambios organizacionales. 1 Data Engineer con acceso a los repos y a la BD es suficiente.

**Para ejecutar la Fase 2:**

| Necesidad | Descripción |
|-----------|-------------|
| **Data Engineering function** | Al menos 2 Data Engineers dedicados. No pueden ser borrowed time de producto |
| **Data ownership formal** | Cada dominio (Annotations, LMS, Revenue) necesita un dueño técnico responsable |
| **Governance mínima** | Glosario de términos compartido. ¿Qué es "usuario activo"? ¿Qué es "institución activa"? |
| **Acceso unificado a datos** | DE necesita acceso de lectura a BD h, BD lms y HubSpot |
| **Budget herramientas** | AWS DMS + S3 + Glue + Athena + Metabase: **~$50/mes** (ver desglose Sección 5.2) |

**Para ejecutar la Fase 3:**

| Necesidad | Descripción |
|-----------|-------------|
| **Alineación Product + CS + Sales** | Las 3 áreas deben acordar qué métricas son oficiales y cómo se calculan |
| **Data PM o Analytics Lead** | Alguien que traduzca necesidades de negocio en especificaciones de datos |
| **Proceso de data governance** | Revisión regular de calidad, ownership y SLAs de datos |
| **Budget herramientas Fase 3** | Si Athena se satura: Redshift Serverless (~$0.36/RPU-hora). QuickSight embedded (~$0.30/sesión) |

---

## ¿Qué NO sabemos todavía?

### Requiere completar en BD (ver sección Volumetría Real)

| Información | Por qué importa |
|-------------|----------------|
| Volumen real de anotaciones | Dimensionar el Data Lake y proyectar costos de Athena |
| Crecimiento mensual histórico | Proyectar capacidad y decidir si Athena o Redshift |
| Distribución real de tipos de eventos | Validar hipótesis de uso y priorizar tracking |
| Usuarios activos reales (30/90/180 días) | Baseline real para North Star Metrics |
| Instituciones en riesgo de churn (top 20) | Acción inmediata para CS |

### Requiere entrevistas

| Información | Con quién |
|-------------|----------|
| Modelo de pricing | Finance / CEO |
| Proceso de renovación y señales de churn | Customer Success |
| Qué métricas usa Sales para cerrar | Sales |
| OKRs del año | CEO / CTO |
| Roadmap de producto | Product Manager |

### Requiere acceso a herramientas

| Herramienta | Datos buscados |
|-------------|---------------|
| **HubSpot** | Contratos, deals, renovaciones, pipeline |
| **Google Analytics** | Confirmar uso y configuración |
| **New Relic** | Performance y endpoints críticos |
| **Sentry** | Errores frecuentes e impacto |
| **Sistema de billing** | Planes, montos, fechas por cliente |

---

## Executive Recommendation

Hypothesis posee una base tecnológica sólida, integraciones operativas con los principales LMS del mercado educativo, y un modelo de datos maduro. La infraestructura no es el problema.

El problema es que hoy la compañía no puede responder la pregunta más importante para cualquier conversación de renovación: **¿cuánto valor genera Hypothesis para esta universidad?**

Este assessment identifica tres acciones críticas a tomar en los próximos 30 días, antes de cualquier decisión de inversión mayor:

**1. Completar la Volumetría Real** (1 día de trabajo): Ejecutar las 10 queries de la sección correspondiente. Sin números reales, este diagnóstico es una hipótesis, no una base para pedir presupuesto al CEO.

**2. Archivar LTI params a S3 antes del próximo purge** (2-3 días de trabajo, un solo ingeniero): Cada 30 días se ejecuta una tarea que destruye permanentemente el contexto histórico de los eventos. La próxima ejecución puede ocurrir en días. El costo de preservar estos datos es ~$2-5/mes en S3. El costo de no hacerlo es perder para siempre la capacidad de construir reportes YoY. Esta es la única acción verdaderamente irreversible del roadmap.

**3. Dashboard proxy de CS** (1-2 semanas): No se necesita DW ni tracking para que CS tenga visibilidad. Los datos en `lms.event` y `lms.application_instances` ya permiten identificar instituciones en riesgo hoy. Metabase conectado a una RDS read replica resuelve esto sin nueva infraestructura.

**A mediano plazo:** La inversión en el sistema de tracking completo (Fase 1) y el Data Layer AWS-native (Fase 2) está justificada por tres riesgos de revenue concretos: (1) churn no detectado, (2) renovaciones negociadas sin evidencia, (3) decisiones de producto sin datos. Con ~$50/mes de infraestructura adicional y 2 ingenieros durante 3-5 meses, Hypothesis puede tener dashboards operativos de CS y un Data Lake con datos históricos — una inversión mínima para el riesgo que mitiga.

**El diferenciador estratégico de largo plazo** es convertir las anotaciones en Learning Analytics: métricas de engagement intelectual que los LMS tradicionales no pueden proveer. Esta es la propuesta de valor que transforma Hypothesis de "herramienta de anotación" a "plataforma de evidencia de aprendizaje activo" — con implicaciones directas en pricing, retención y diferenciación competitiva.

---

## Apéndice — Plan de acción detallado

**Semana 1 (inmediata):**
- ✅ Ejecutar 10 queries de Volumetría Real en producción
- ✅ Implementar S3 cold archive para LTI params (no esperar al próximo purge)
- ✅ Solicitar acceso a HubSpot
- ✅ Agendar entrevistas: Finance, Sales, CS, Product, CEO

**Semana 2-3:**
- Dashboard proxy de CS desde datos existentes (Metabase → RDS read replica)
- Resource tracking en client (2-3 días)
- Diseño del sistema de eventos: taxonomía + arquitectura write-path

**Sprint 1 (semana 3-6):**
- Analytics endpoint correcto: SQS + tabla dedicada + client batching
- Session tracking (parte del sistema de eventos)

**Mes 2 (paralelo):**
- AWS DMS replication RDS → S3
- Estructura del Data Lake (particionado)
- dbt models iniciales (staging layer)

**Mes 3-4:**
- dbt business layer (modelo estrella completo)
- Pipeline HubSpot → S3
- Metabase sobre Athena operativo
- **CS tiene dashboard real de churn en mes 4**

**Mes 5-8:**
- Dashboard institucional para clientes
- Health Score automatizado
- Dashboard de instructores embedded

**Mes 9-12:**
- Predicción de churn (ML)
- Learning Analytics metrics
- Self-Service Analytics

# Hypothesis Platform — Data Assessment v2
**Fecha:** 2026-05-22
**Versión:** 2.0
**Autor:** Data Engineering
**Estado:** Fase 1 — Assessment desde código fuente (sin acceso a BD)

---

## Resumen Ejecutivo

Este documento es el resultado del assessment de datos de la plataforma Hypothesis. La empresa vende a universidades una herramienta de anotaciones digitales que se integra con sus sistemas de gestión de aprendizaje (LMS). Los usuarios (estudiantes y profesores) pueden anotar PDFs, videos, páginas web y material de estudio.

**Scope del assessment:** análisis completo desde código fuente de los 3 repositorios principales (`h`, `lms`, `client`). Las secciones que requieren acceso a base de datos están marcadas con `[REQUIERE BD]`. Las que requieren entrevistas o acceso a herramientas externas están marcadas con `[REQUIERE ENTREVISTA]` o `[REQUIERE ACCESO]`.

### Respuestas a las 7 preguntas clave

| Pregunta | Estado | Respuesta resumida |
|----------|--------|--------------------|
| ¿Qué datos existen? | ✅ | ~61 tablas entre h y lms: anotaciones, usuarios, cursos, asignaciones, eventos, calificaciones |
| ¿Dónde viven? | ✅ | 2 BDs PostgreSQL en AWS RDS + Elasticsearch para búsqueda |
| ¿Cómo fluyen? | ✅ | h ↔ lms vía API REST + RabbitMQ + Foreign Data Wrapper |
| ¿Qué tan confiables? | 🔲 | Requiere acceso a BD — queries provistas en Bloque 3 |
| ¿Qué métricas se pueden construir? | ⚠️ | Limitadas: conteos de anotaciones, launches LTI, calificaciones. Faltan métricas de engagement |
| ¿Qué falta capturar? | ✅ | Apertura de PDFs/videos, tiempo de uso, búsquedas, sesiones, engagement por recurso |
| ¿Cuál es el roadmap? | ✅ | Tracking → Data Layer → Analytics Product (ver Bloque 6) |

### Hallazgo crítico

> **El analytics service de `h` existe en el código pero no está implementado (marcado como TODO). Toda la plataforma core carece de analytics funcional. Esto significa que hoy no es posible medir engagement, adopción real ni construir un producto analítico serio.**

---

## Bloque 0 — Entendimiento del Negocio

> Este bloque se completará parcialmente con entrevistas al equipo de negocio. Lo que se puede inferir desde código fuente está marcado como tal.

### 0.1 Modelo de negocio y Revenue Drivers

**Modelo inferido desde código** (sin confirmación de negocio):

Hypothesis vende a universidades e instituciones educativas acceso a su plataforma de anotaciones colaborativas. El producto se distribuye principalmente a través de integración LTI con los LMS que las universidades ya usan (Canvas, Blackboard, D2L, Moodle).

**Revenue Drivers identificados:**

| Driver | Fuente de datos | Dónde vive hoy |
|--------|----------------|----------------|
| Universidades activas | `organization` + `application_instances` (lms) | BD lms ✅ |
| Cantidad de estudiantes activos | `lms_user` + `lms_course_membership` (lms) | BD lms ✅ |
| Cantidad de cursos con Hypothesis | `lms_course` (lms) | BD lms ✅ |
| Licencias contratadas | ❓ No encontrado en código | HubSpot / sistema de billing externo |
| Contratos y fechas de renovación | ❓ No encontrado en código | HubSpot / sistema de billing externo |
| Renewal rate | ❓ No encontrado en código | HubSpot / sistema de billing externo |
| Churn | ❓ No encontrado en código | Inferible desde `last_launched` en `application_instances` |

**Palancas de crecimiento inferidas:**
- Expansión dentro de una universidad (más cursos, más facultades)
- Expansión a nuevas universidades
- Upsell a planes con más features (auto-grading, dashboards premium)
- Retención: renovación semestral/anual de licencias

---

### 0.2 North Star Metrics propuestas

Basadas en la arquitectura del producto y benchmarks de EdTech SaaS:

| Métrica | Descripción | Fuente de datos disponible |
|---------|-------------|---------------------------|
| **Monthly Active Students (MAS)** | Estudiantes únicos que hacen al menos 1 anotación o launch en el mes | `annotation.userid` (h) + `event` (lms) |
| **Monthly Active Instructors (MAI)** | Instructores únicos que configuran o revisan asignaciones | `event_user` con rol instructor (lms) |
| **Annotation Rate** | Anotaciones promedio por estudiante por curso | `annotation` (h) + `lms_course_membership` (lms) |
| **Launch → Annotation Conversion** | % de launches que resultan en al menos 1 anotación | `event` (lms) + `annotation` (h) — requiere join |
| **Retención semestral** | % de cursos/instituciones que continúan el semestre siguiente | `lms_course` con `lms_term` (lms) |
| **Renewal Rate** | % de contratos renovados | ❌ No en BDs — requiere HubSpot/billing |

> **Nota:** Hoy las métricas MAS y Annotation Rate son calculables pero con limitaciones (no hay tracking de apertura de recursos, solo de anotaciones creadas).

---

### 0.3 Preguntas que debería poder responder el Board

Las siguientes preguntas guían las decisiones estratégicas y deben poder responderse con los datos disponibles:

**Adopción:**
- ¿Qué universidades usan más el producto? ¿Cuántos cursos activos tiene cada una?
- ¿Qué LMS tiene mayor tasa de adopción (Canvas vs Blackboard vs D2L vs Moodle)?
- ¿Cuántos estudiantes usan activamente Hypothesis en el semestre actual?
- ¿Qué porcentaje de cursos configurados generan al menos una anotación?

**Engagement:**
- ¿Qué recursos (PDFs, videos, libros) generan más anotaciones?
- ¿Qué cursos tienen mayor engagement de los estudiantes?
- ¿Cuántas anotaciones promedio hace un estudiante activo?
- ¿Cuál es la profundidad promedio de las conversaciones (replies)?

**Retención y riesgo:**
- ¿Qué instituciones están en riesgo de churn (baja actividad reciente)?
- ¿Qué instituciones están creciendo en uso?
- ¿Cuál es la retención semestral por tipo de LMS?

**Negocio:**
- ¿Cuánto revenue está asociado a cada nivel de uso?
- ¿Qué instituciones tienen contratos próximos a vencer?
- ¿Cuál es el tiempo promedio desde el primer launch hasta la primera anotación?

> **Estado actual:** Las preguntas de adopción son parcialmente respondibles. Las de engagement son respondibles solo con aproximaciones (no hay sesiones ni tracking de recursos). Las de retención y negocio requieren acceso a HubSpot y datos de billing.

---

## Bloque 1 — Arquitectura

### 1.1 Repositorios

| Repositorio | Función | Tecnología | Base de datos | Responsable |
|-------------|---------|-----------|---------------|-------------|
| `hypothesis/h` | Backend central: API REST de anotaciones, autenticación, grupos, búsqueda, panel admin | Python 3.11 + Pyramid, Celery, Gunicorn | PostgreSQL + Elasticsearch | Backend team |
| `hypothesis/lms` | Integración con LMS educativos (Canvas, Blackboard, D2L, Moodle) vía LTI 1.1/1.3 | Python 3.11 + Pyramid, Celery, Gunicorn | PostgreSQL separada | LMS/EdTech team |
| `hypothesis/client` | Cliente JavaScript inyectable en páginas web; permite anotar HTML, PDFs, videos | TypeScript + Preact + Redux, Rollup | Sin BD propia (consume API de h) | Frontend team |

**Preguntas del framework:**
- **¿Cuántos repositorios existen?** 3 principales + librerías compartidas (`@hypothesis/frontend-shared`, `h-api`, `h-vialib`)
- **¿Cuál es el producto principal?** `h` es el núcleo; `lms` es el canal de distribución a universidades; `client` es la UI
- **¿Existen microservicios?** No. Arquitectura monolítica por repo (Pyramid WSGI)
- **¿Existen procesos batch?** Sí: Celery workers en `h` (indexación, emails) y `lms` (digests, calificaciones, HubSpot)
- **¿Existen APIs?** Sí: REST API completa en `h` (`/api/*`) y `lms` (`/api/*`, `/lti_launches`)
- **¿Existen workers?** Sí: Celery + RabbitMQ en ambos backends
- **¿Existen procesos ETL?** No hay ETL dedicado. La sincronización se hace vía H Bulk API y Celery tasks

---

### 1.2 Infraestructura

**Mapa infraestructura:**

```
┌─────────────────────────────────────────────────────────────┐
│                    AWS (us-west-1 + ca-central-1)           │
│                                                             │
│  ┌──────────────────┐    ┌──────────────────────────────┐  │
│  │ ElasticBeanstalk │    │    ElasticBeanstalk           │  │
│  │   h (web)        │    │    h-websocket               │  │
│  │   Puerto 5000    │    │    Puerto 5001               │  │
│  └────────┬─────────┘    └──────────────────────────────┘  │
│           │                                                  │
│  ┌────────▼─────────┐    ┌──────────────────────────────┐  │
│  │   RDS PostgreSQL │    │    Elasticsearch 7.10         │  │
│  │   BD: h          │    │    Índice: annotations        │  │
│  └────────┬─────────┘    └──────────────────────────────┘  │
│           │ FDW                                             │
│  ┌────────▼─────────┐    ┌──────────────────────────────┐  │
│  │   RDS PostgreSQL │    │    RabbitMQ 3.12              │  │
│  │   BD: lms        │    │    Colas: celery, annotation, │  │
│  └──────────────────┘    │    email_digests, indexer     │  │
│                          └──────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ ElasticBeanstalk — lms (web + Celery workers)        │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                             │
│  S3 (assets estáticos)   CloudFront (CDN)                  │
└─────────────────────────────────────────────────────────────┘
```

**Servicios AWS identificados:**
- **ElasticBeanstalk**: hosting de `h`, `h-websocket`, `lms`
- **RDS**: 2 instancias PostgreSQL separadas (h y lms)
- **S3**: assets estáticos
- **CloudFront**: CDN
- **Route53**: DNS routing multi-región

**Preguntas del framework:**
- **¿Dónde viven los datos?** 2 BDs PostgreSQL en AWS RDS + Elasticsearch para índice de búsqueda
- **¿Cuántas bases existen?** 2 BDs relacionales + 1 índice Elasticsearch
- **¿Quién escribe en cada base?**
  - BD `h`: escribe `h` web + `h` Celery workers
  - BD `lms`: escribe `lms` web + `lms` Celery workers; lee BD `h` via FDW
  - Elasticsearch: escribe `h` indexer (Celery)
- **¿Quién consume cada base?**
  - BD `h`: `h` web (lectura/escritura), `lms` (lectura via FDW y H API)
  - BD `lms`: `lms` web + dashboard + Celery workers
  - Elasticsearch: `h` search API
- **¿Existen integraciones externas?** Sí — ver sección 1.3

---

### 1.3 Integraciones Externas

| Sistema | Tipo | Dirección | Datos intercambiados |
|---------|------|-----------|---------------------|
| **Canvas** | LMS | Bidireccional | Usuarios, cursos, archivos, páginas, calificaciones, asignaciones |
| **Blackboard** | LMS | Bidireccional | Usuarios, cursos, archivos, calificaciones |
| **D2L (Desire2Learn)** | LMS | Bidireccional | Usuarios, cursos, archivos, calificaciones |
| **Moodle** | LMS | Bidireccional | Usuarios, cursos, archivos, páginas |
| **Canvas Studio** | Media | Entrada | Metadata de videos, colecciones de media |
| **JSTOR** | Contenido | Entrada | Metadata de artículos académicos, thumbnails |
| **VitalSource** | Contenido | Entrada | Libros, tabla de contenidos, URLs de lanzamiento |
| **YouTube** | Contenido | Entrada | Metadata de videos |
| **Google Drive** | Almacenamiento | Entrada | File picker para asignaciones |
| **OneDrive** | Almacenamiento | Entrada | File picker para asignaciones |
| **HubSpot** | CRM | Salida | Organizaciones, datos de facturación (Celery task diaria) |
| **Mailchimp** | Email Marketing | Salida | Acciones de usuarios |
| **Sentry** | Error tracking | Salida | Errores frontend y backend |
| **New Relic** | APM | Salida | Métricas de performance |
| **Google Analytics** | Analytics | Salida | Eventos de página (configurado, uso no confirmado) |
| **ORCID / Google / Facebook** | Auth | Entrada | Identidades de usuario via OIDC |

---

### 1.4 APIs expuestas

#### `h` — API de anotaciones

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/api/annotations` | GET/POST | Buscar / crear anotaciones |
| `/api/annotations/{id}` | GET/PATCH/DELETE | CRUD de anotación |
| `/api/search` | GET | Búsqueda full-text (Elasticsearch) |
| `/api/groups` | GET/POST | Listar / crear grupos |
| `/api/users` | POST | Crear usuario |
| `/api/profile` | GET/PATCH | Perfil del usuario autenticado |
| `/api/token` | GET | Obtener API token |
| `/api/bulk` | POST | Operaciones masivas (usado por lms) |
| `/api/analytics/events` | POST | Registrar eventos analytics (⚠️ no implementado) |
| `/oauth/authorize` | GET/POST | OAuth 2.0 Authorization |

#### `lms` — API de integración LTI

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/lti_launches` | POST | Launch LTI (entry point desde LMS) |
| `/lti/1.3/oidc` | GET/POST | OIDC para LTI 1.3 |
| `/api/sync` | POST | Sincronizar grupos con h |
| `/api/grant_token` | GET | Token para el client |
| `/api/lti/result` | GET/POST | Calificaciones LTI |
| `/api/dashboard/assignments` | GET | Asignaciones del dashboard |
| `/api/dashboard/students/metrics` | GET | Métricas de estudiantes |
| `/admin/*` | GET/POST | Panel de administración |

---

### 1.5 Flujo de datos entre sistemas

```
                          UNIVERSIDAD
                              │
                    (LTI Launch via Browser)
                              │
                              ▼
┌─────────────────────────────────────────────────┐
│                      LMS                        │
│  1. Autentica al usuario via LTI 1.1/1.3        │
│  2. Registra Event(configured_launch)            │
│  3. Sincroniza grupos con H (/api/sync)          │
│  4. Devuelve token JWT al client                 │
└───────────────────┬─────────────────────────────┘
                    │                 │
             H Bulk API          JWT Token
                    │                 │
                    ▼                 ▼
┌───────────────────────┐   ┌──────────────────────────────┐
│          H            │   │          CLIENT              │
│  - Crea/actualiza     │◄──│  - Inyectado en la página    │
│    grupos             │   │  - Muestra anotaciones        │
│  - Recibe anotaciones │──►│  - Permite anotar PDFs,      │
│  - Indexa en          │   │    videos, HTML               │
│    Elasticsearch      │   └──────────────────────────────┘
│  - Publica a          │
│    RabbitMQ           │
└──────────┬────────────┘
           │ RabbitMQ
           ▼
┌──────────────────────────────────────────────────┐
│                 LMS (Celery workers)             │
│  - Procesa eventos de anotaciones               │
│  - Envía emails de notificación                  │
│  - Sincroniza calificaciones con Canvas/BB/D2L  │
│  - Exporta datos a HubSpot                      │
└──────────────────────────────────────────────────┘
```

---

## Revenue Data Assessment

> **Este bloque es crítico para el Board. Un assessment de uso sin datos de negocio es incompleto.**

### ¿Dónde están los datos de monetización?

| Dato | Encontrado en código | Ubicación probable |
|------|--------------------|--------------------|
| Clientes / Universidades | ✅ Parcial | `organization` + `application_instances` (lms BD) |
| Contratos y fechas de renovación | ❌ No encontrado | HubSpot (integración activa encontrada en código) |
| Licencias y pricing | ❌ No encontrado | HubSpot o sistema de billing externo |
| Facturación / Revenue | ❌ No encontrado | Sistema de billing externo (Stripe, Chargebee, manual) |
| Churn real | ❌ No encontrado | Inferible desde `application_instances.last_launched` |
| Usuarios contratados vs activos | ⚠️ Parcial | Activos en BD lms; contratados solo en billing externo |

### Proxy de revenue desde BDs existentes

Aunque no existe una tabla de contratos, se puede aproximar el "valor" de un cliente con:

```sql
-- Proxy de engagement por institución (BD lms)
SELECT
    o.name AS institucion,
    ai.tool_consumer_instance_name AS nombre_lms,
    ai.tool_consumer_info_product_family_code AS tipo_lms,
    ai.last_launched AS ultimo_uso,
    COUNT(DISTINCT lc.id) AS cursos_activos,
    COUNT(DISTINCT lu.id) AS usuarios_unicos,
    COUNT(DISTINCT a.id) AS asignaciones,
    CASE
        WHEN ai.last_launched > NOW() - INTERVAL '90 days' THEN 'Activo'
        WHEN ai.last_launched > NOW() - INTERVAL '180 days' THEN 'En riesgo'
        ELSE 'Inactivo'
    END AS estado_salud
FROM organization o
JOIN application_instances ai ON ai.organization_id = o.id
LEFT JOIN lms_course_application_instance lcai ON lcai.application_instance_id = ai.id
LEFT JOIN lms_course lc ON lc.id = lcai.lms_course_id
LEFT JOIN lms_user_application_instance luai ON luai.application_instance_id = ai.id
LEFT JOIN lms_user lu ON lu.id = luai.lms_user_id
LEFT JOIN assignment a ON a.course_id IS NOT NULL
GROUP BY 1, 2, 3, 4
ORDER BY cursos_activos DESC;
```

### Acciones recomendadas para el assessment de revenue

1. **`[REQUIERE ACCESO]` HubSpot**: solicitar acceso para extraer datos de deals, contratos, fechas de renovación y contactos
2. **`[REQUIERE ENTREVISTA]` Finance/Sales**: entender el modelo de pricing (¿por estudiante? ¿por institución? ¿por feature?)
3. **`[REQUIERE ENTREVISTA]` Customer Success**: entender el proceso de renovación y señales de churn

---

## Mapa de Ownership de Datos

| Dominio | Dueño funcional | Sistemas | BD |
|---------|----------------|----------|-----|
| **Annotations** | Product / Backend | `h` | BD h |
| **Users & Auth** | Platform / Backend | `h` | BD h |
| **LMS Integration** | LMS/EdTech Team | `lms` | BD lms |
| **Courses & Assignments** | LMS/EdTech Team | `lms` | BD lms |
| **Grading** | LMS/EdTech Team | `lms` | BD lms |
| **Organizations / Billing** | Finance / Sales | HubSpot + externo | Externo |
| **CRM / Contracts** | Sales | HubSpot | Externo |
| **Error Tracking** | Engineering | Sentry | Externo |
| **Performance** | Engineering | New Relic | Externo |
| **Analytics** | Data Engineering | ⚠️ No existe aún | — |
| **Search Index** | Backend | Elasticsearch | Elasticsearch |

### Implicaciones de gobernanza

- Hoy no existe un dueño de datos transversal (Data Engineering es nuevo)
- Los datos de revenue están en Sales/Finance, desconectados de los datos de uso en Engineering
- No hay un data catalog ni definiciones compartidas de entidades clave (ej: ¿qué es un "usuario activo"?)

---

## Evaluación de Riesgos

### Riesgos identificados desde el código

| # | Riesgo | Severidad | Impacto en negocio | Acción recomendada |
|---|--------|-----------|-------------------|-------------------|
| R1 | **Analytics service no implementado** en `h` (TODO en código) | 🔴 Alto | Pérdida permanente de información de engagement. No se puede medir valor del producto | Implementar en Sprint 1 — el endpoint ya existe |
| R2 | **No existe tracking de sesiones** ni tiempo de uso | 🔴 Alto | Imposible demostrar valor real a universidades. No se puede responder "¿cuánto usan Hypothesis?" | Agregar session tracking al client |
| R3 | **Eventos de anotación no se persisten** en h (solo en memoria) | 🔴 Alto | No hay fuente de verdad para actividad histórica de anotaciones. Solo se puede reconstruir parcialmente desde la tabla `annotation` | Crear tabla `annotation_event` en h |
| R4 | **LTI params purgados a 30 días** (Celery task automática) | 🟡 Medio | Pérdida de histórico de contexto de launches. Limita análisis retrospectivo | Evaluar si hay datos valiosos que preservar antes de la purga |
| R5 | **Datos de revenue fuera del sistema** (HubSpot, billing externo) | 🟡 Medio | No se puede correlacionar uso con ingresos sin integración manual | Construir pipeline HubSpot → DW en Fase 2 |
| R6 | **Dependencia fuerte de joins entre h y lms** via `h_userid` | 🟡 Medio | Complejidad analítica alta. Un error en la generación del `h_userid` rompe todos los análisis cruzados | Validar integridad del join con queries de la Sección 3.4 |
| R7 | **Elasticsearch 7.10** (versión en EOL) | 🟡 Medio | Riesgo operativo a mediano plazo. Sin actualizaciones de seguridad | Planificar upgrade a OpenSearch o Elasticsearch 8.x |
| R8 | **No hay tipo de recurso normalizado** (PDF, video, HTML no se distinguen) | 🟢 Bajo | No se puede segmentar adopción por tipo de material educativo | Agregar campo `resource_type` en tabla `assignment` |

---

## Bloque 2 — Modelo de Datos

### 2.1 Entidades principales

```
Organization (lms)
  └── ApplicationInstance (lms)  ← "Instalación" del LMS en una universidad
        ├── LMSUser (lms)        ← Usuario del LMS
        │     └── User (h)       ← Cuenta en Hypothesis (vinculada via h_userid)
        ├── LMSCourse (lms)      ← Curso
        │     └── Assignment (lms) ← Asignación/tarea
        └── Grouping (lms)       ← Grupos, secciones, cursos (polimórfico)
              └── [sincronizado con Group (h)]
                    └── Annotation (h)  ← La anotación
                          ├── Document (h)       ← Documento anotado
                          ├── Mention (h)        ← Menciones de usuarios
                          ├── Notification (h)   ← Notificaciones
                          └── Flag (h)           ← Reportes de moderación
```

---

### 2.2 Inventario de tablas — BD `h`

| Tabla | Descripción | PK | FKs principales |
|-------|-------------|-----|----------------|
| `user` | Usuarios de Hypothesis. Incluye campos de perfil, estado, timestamps y flags (admin, staff, nipsa, deleted) | `id` | `activation_id → activation` |
| `user_identity` | Identidades externas del usuario (ORCID, Google, Facebook) | `id` | `user_id → user` |
| `activation` | Tokens de activación de cuenta | `id` | — |
| `authclient` | Clientes OAuth 2.0 registrados (LMS, extensiones, etc.) | `id (UUID)` | — |
| `authzcode` | Códigos de autorización OAuth (vida corta) | `id` | `user_id → user`, `authclient_id → authclient` |
| `authticket` | Tickets de sesión web | `id (text)` | `user_id → user` |
| `token` | API tokens (acceso y refresh) | `id` | `user_id → user`, `authclient_id → authclient` |
| `group` | Grupos de anotación (públicos, privados, de institución) | `id` | `creator_id → user`, `organization_id → organization` |
| `user_group` | Membresía usuario-grupo con roles (JSONB) | `id` | `user_id → user`, `group_id → group` |
| `groupscope` | Alcance de URLs donde aplica el grupo | `id` | `group_id → group` |
| `organization` | Organizaciones (universidades, empresas) | `id` | — |
| `annotation` | **Tabla central**: anotaciones con texto, tags, selectores de posición, estado de moderación | `id (UUID)` | `document_id → document` |
| `annotation_slim` | Vista desnormalizada de anotaciones para queries rápidas | `id` | `pubid → annotation`, `user_id → user`, `group_id → group`, `document_id → document` |
| `annotation_metadata` | Metadata JSONB extendida de anotaciones | `annotation_id` | `annotation_id → annotation_slim` |
| `document` | Documento web anotado (agrupa URIs que representan el mismo contenido) | `id` | — |
| `document_uri` | URIs concretas de un documento | `id` | `document_id → document` |
| `document_meta` | Metadata del documento (título, autor, etc.) | `id` | `document_id → document` |
| `mention` | Menciones de usuarios dentro de anotaciones (`@usuario`) | `id` | `annotation_id → annotation`, `user_id → user` |
| `notification` | Notificaciones enviadas (reply, mention) | `id` | `source_annotation_id → annotation`, `recipient_id → user` |
| `flag` | Reportes/flags de anotaciones por usuarios | `id` | `annotation_id → annotation`, `user_id → user` |
| `moderation_log` | Log de cambios de estado de moderación | `id` | `annotation_id → annotation`, `moderator_id → user` |
| `subscriptions` | Preferencias de notificación de usuarios | `id` | — |
| `feature` | Feature flags del sistema | `id` | — |
| `featurecohort` | Grupos de usuarios para A/B testing | `id` | — |
| `featurecohort_user` | Relación usuario-cohorte | `id` | `user_id → user`, `cohort_id → featurecohort` |
| `featurecohort_feature` | Relación cohorte-feature | `id` | `feature_id → feature`, `cohort_id → featurecohort` |
| `job` | Cola de jobs internos (indexación, purga) | `id` | — |
| `task_done` | Registro de tareas completadas | `id` | — |
| `user_deletion` | Auditoría de deletions de usuarios | `id` | — |
| `blocklist` | URIs bloqueadas (no se pueden anotar) | `id` | — |
| `setting` | Key-value settings del sistema | `key` | — |

**Total: 31 tablas**

---

### 2.3 Inventario de tablas — BD `lms`

| Tabla | Descripción | PK | FKs principales |
|-------|-------------|-----|----------------|
| `organization` | Organización educativa (universidad). Puede tener jerarquía | `id` | `parent_id → organization` |
| `application_instances` | Instalación de Hypothesis en un LMS. Una universidad puede tener varias | `id` | `organization_id → organization`, `lti_registration_id → lti_registration` |
| `lti_registration` | Registro LTI 1.3 (issuer, client_id, URLs de auth/keys/token) | `id` | — |
| `lms_user` | Usuario canónico del LMS. Tiene `h_userid` para vincular con h | `id` | — |
| `user` | Usuario en el contexto de una instancia específica del LMS | `id` | `application_instance_id → application_instances` |
| `lms_user_application_instance` | Relación usuarios-instancias | `id` | `lms_user_id → lms_user`, `application_instance_id → application_instances` |
| `lms_term` | Período académico con fechas de inicio/fin | `id` | — |
| `lms_course` | Curso en el LMS | `id` | `lms_term_id → lms_term` |
| `lms_course_application_instance` | Relación curso-instancia | `id` | `lms_course_id → lms_course`, `application_instance_id → application_instances` |
| `lms_course_membership` | Membresía de usuarios en cursos con rol LTI | `id` | `lms_course_id → lms_course`, `lms_user_id → lms_user`, `lti_role_id → lti_role` |
| `lti_role` | Roles LTI (instructor, learner, admin, test_user) | `id` | — |
| `lti_role_override` | Override de roles por instancia | `id` | `lti_role_id → lti_role`, `application_instance_id → application_instances` |
| `grouping` | Entidad polimórfica: curso, sección, grupo (Canvas/BB/D2L/Moodle) | `id` | `application_instance_id → application_instances`, `parent_id → grouping` |
| `grouping_membership` | Membresía de usuarios en groupings | `(grouping_id, user_id)` | `grouping_id → grouping`, `user_id → user` |
| `group_info` | Información legacy de grupos del LMS | `id` | `application_instance_id → application_instances` |
| `assignment` | Asignación/tarea con URL del documento a anotar | `id` | `course_id → grouping`, `auto_grading_config_id → assignment_auto_grading_config` |
| `assignment_auto_grading_config` | Configuración de auto-calificación | `id` | — |
| `assignment_grouping` | Relación asignaciones-groupings | `(assignment_id, grouping_id)` | `assignment_id → assignment`, `grouping_id → grouping` |
| `file` | Archivo del LMS referenciado en una asignación | `id` | `application_instance_id → application_instances` |
| `grading_sync` | Proceso de sincronización de calificaciones | `id` | `assignment_id → assignment`, `created_by_id → lms_user` |
| `grading_sync_grade` | Calificación individual de un estudiante | `id` | `grading_sync_id → grading_sync`, `lms_user_id → lms_user` |
| `lis_result_sourcedid` | Info de calificación LTI 1.1 (legacy) | `id` | `application_instance_id → application_instances` |
| `oauth2_token` | Tokens OAuth2 para APIs de LMS | `id` | `application_instance_id → application_instances` |
| `jwt_oauth2_token` | Tokens JWT para LTI 1.3 | `id` | `lti_registration_id → lti_registration` |
| `rsa_key` | Claves RSA para firma JWT LTI 1.3 | `id` | — |
| `event` | **Tabla de eventos**: acciones en el sistema | `id` | `type_id → event_type`, `application_instance_id → application_instances`, `course_id → grouping`, `assignment_id → assignment` |
| `event_type` | Catálogo de tipos de evento | `id` | — |
| `event_user` | Usuarios que participaron en un evento y su rol | `id` | `event_id → event`, `user_id → user`, `lti_role_id → lti_role` |
| `event_data` | Datos extra del evento en JSONB | `event_id` | `event_id → event` |
| `notification` | Notificaciones de reply/mention en contexto LMS | `id` | `sender_id → lms_user`, `recipient_id → lms_user`, `assignment_id → assignment` |

**Total: 30 tablas**

---

### 2.4 Relaciones entre BDs

El campo que conecta las dos BDs es `h_userid` (ej: `acct:usuario@lms.hypothes.is`):

```
lms.lms_user.h_userid  ←→  h.user.userid
lms.grouping.authority_provided_id  ←→  h.group.authority_provided_id
```

La BD `lms` puede leer la BD `h` directamente via **Foreign Data Wrapper (FDW)**.

---

### 2.5 Inventario de tablas — Conteos `[REQUIERE BD]`

```sql
-- Conteo y crecimiento de las tablas principales (BD h)
SELECT
  relname AS tabla,
  n_live_tup AS registros_estimados
FROM pg_stat_user_tables
ORDER BY n_live_tup DESC;

-- Crecimiento mensual de anotaciones (BD h)
SELECT
  DATE_TRUNC('month', created) AS mes,
  COUNT(*) AS nuevas_anotaciones,
  COUNT(*) FILTER (WHERE shared = true) AS publicas,
  COUNT(*) FILTER (WHERE deleted = true) AS borradas
FROM annotation
GROUP BY 1 ORDER BY 1 DESC LIMIT 24;

-- Launches por mes (BD lms)
SELECT
  DATE_TRUNC('month', e.timestamp) AS mes,
  et.type,
  COUNT(*) AS cantidad
FROM event e
JOIN event_type et ON e.type_id = et.id
GROUP BY 1, 2 ORDER BY 1 DESC;
```

---

## Bloque 3 — Calidad de Datos

> Requiere acceso a base de datos. Se proveen las queries para ejecutar.

### 3.1 Completitud `[REQUIERE BD]`

```sql
-- Usuarios sin email (BD h)
SELECT
  COUNT(*) AS total_usuarios,
  COUNT(*) FILTER (WHERE email IS NULL) AS sin_email,
  ROUND(100.0 * COUNT(*) FILTER (WHERE email IS NULL) / COUNT(*), 2) AS pct_sin_email
FROM "user" WHERE deleted = false;

-- Anotaciones sin target_uri (BD h)
SELECT COUNT(*) AS anotaciones_sin_uri
FROM annotation
WHERE target_uri IS NULL OR target_uri = '';

-- Usuarios LMS sin h_userid (BD lms)
SELECT COUNT(*) AS usuarios_sin_h_userid
FROM lms_user WHERE h_userid IS NULL;

-- Eventos sin usuario asociado (BD lms)
SELECT COUNT(*) AS eventos_sin_usuario
FROM event e
LEFT JOIN event_user eu ON eu.event_id = e.id
WHERE eu.user_id IS NULL;
```

### 3.2 Duplicados `[REQUIERE BD]`

```sql
-- Usuarios con mismo email en misma authority (BD h)
SELECT email, authority, COUNT(*) AS duplicados
FROM "user"
WHERE email IS NOT NULL AND deleted = false
GROUP BY email, authority
HAVING COUNT(*) > 1
ORDER BY duplicados DESC LIMIT 20;

-- Usuarios LMS duplicados por h_userid (BD lms)
SELECT h_userid, COUNT(*) AS duplicados
FROM lms_user
GROUP BY h_userid
HAVING COUNT(*) > 1;
```

### 3.3 Consistencia `[REQUIERE BD]`

```sql
-- Anotaciones con updated < created (BD h)
SELECT COUNT(*) AS inconsistencias_fecha
FROM annotation WHERE updated < created;

-- Calificaciones fuera de rango [0, 1] (BD lms)
SELECT COUNT(*) AS notas_invalidas
FROM grading_sync_grade
WHERE grade < 0 OR grade > 1;

-- Cursos con ends_at < starts_at (BD lms)
SELECT COUNT(*) AS cursos_fechas_invalidas
FROM lms_course
WHERE ends_at IS NOT NULL AND starts_at IS NOT NULL AND ends_at < starts_at;
```

### 3.4 Integridad Referencial `[REQUIERE BD]`

```sql
-- annotation_slim sin annotation padre (BD h)
SELECT COUNT(*) AS slim_huerfanos
FROM annotation_slim asm
WHERE NOT EXISTS (
  SELECT 1 FROM annotation a WHERE a.id = asm.pubid
);

-- Events con application_instance_id inexistente (BD lms)
SELECT COUNT(*) AS eventos_huerfanos
FROM event e
WHERE e.application_instance_id IS NOT NULL
  AND NOT EXISTS (
    SELECT 1 FROM application_instances ai WHERE ai.id = e.application_instance_id
  );
```

### 3.5 Volumen `[REQUIERE BD]`

```sql
SELECT
  relname AS tabla,
  pg_size_pretty(pg_total_relation_size(relid)) AS tamaño_total,
  n_live_tup AS filas_estimadas
FROM pg_stat_user_tables
ORDER BY pg_total_relation_size(relid) DESC LIMIT 20;
```

---

## Bloque 4 — Assessment de Tracking

### 4.1 Eventos existentes

#### BD `lms` — Eventos persistidos

| Evento | Fuente | Tabla | Descripción |
|--------|--------|-------|-------------|
| `configured_launch` | LMS (LTI) | `event` | Usuario abre Hypothesis desde el LMS |
| `deep_linking` | LMS (LTI) | `event` | Profesor configura una asignación nueva |
| `edited_assignment` | Admin | `event` | Profesor edita una asignación existente |
| `submission` | LMS | `event` | Estudiante envía trabajo |
| `grade` | Celery | `event` | Sistema sincroniza calificación |
| `audit` | Admin | `event` | Cambios en modelos (audit trail) |
| `error_code` | API | `event` | Error durante una acción LTI |

#### BD `h` — Eventos en memoria (no persistidos)

| Evento | Acciones disparadas | Persistencia |
|--------|-------------------|-------------|
| `AnnotationEvent (create/update/delete)` | Elasticsearch, WebSocket, emails | ❌ Solo en `annotation` table |
| `ModeratedAnnotationEvent` | Email de moderación | ❌ Solo en `moderation_log` |
| `LoginEvent / LogoutEvent` | Logging | ❌ No persistido |
| `ActivationEvent` | Email bienvenida | ❌ No persistido |

> **⚠️ Hallazgo crítico:** En `h` no hay tabla de eventos analíticos. El endpoint `/api/analytics/events` está marcado como TODO en el código. Solo 1 tipo de evento se envía desde el client (`client.realtime.apply_updates`).

---

### 4.2 Cobertura actual vs ideal

| Acción del usuario | Trackeado | Dónde | Notas |
|-------------------|-----------|-------|-------|
| Abrir Hypothesis desde LMS | ✅ | `event` (lms) | `configured_launch` |
| Crear anotación | ⚠️ | `annotation` (h) | Solo registro, no evento |
| Editar anotación | ⚠️ | `annotation.updated` (h) | No hay versiones |
| Eliminar anotación | ⚠️ | `annotation.deleted` (h) | No hay evento explícito |
| Responder a anotación | ⚠️ | `annotation.references` (h) | Inferible |
| Mencionar usuario | ✅ | `mention` (h) | Guardado |
| Reportar anotación | ✅ | `flag` (h) | Guardado |
| Calificación sincronizada | ✅ | `grading_sync_grade` (lms) | Con resultado |
| **Abrir PDF** | ❌ | — | No trackeado |
| **Abrir video** | ❌ | — | No trackeado |
| **Búsqueda** | ❌ | — | No trackeado |
| **Tiempo de uso** | ❌ | — | No trackeado |
| **Inicio/fin de sesión** | ❌ | — | No trackeado |
| **Login** | ❌ | — | Solo log, no persistido |

---

### 4.3 Gaps críticos

**Gap 1 — Sin tracking de engagement real con el contenido**
No hay tracking de apertura de PDFs, videos o libros. Imposible calcular "tiempo de uso" o "recursos más anotados". **Impacto directo en la capacidad de demostrar valor a universidades.**

**Gap 2 — Analytics service no implementado**
El endpoint existe en código con un `TODO: Enhance this`. Pérdida activa de información cada vez que un usuario usa el producto.

**Gap 3 — Acciones de anotación sin eventos propios**
Crear/editar/eliminar anotaciones no genera registros en tabla de eventos. Solo se puede reconstruir actividad desde timestamps.

**Gap 4 — Sin concepto de sesión**
No se puede medir cuándo empieza y termina el uso. El `configured_launch` registra el inicio pero no el fin. **Imposible calcular métricas de retención o engagement por sesión.**

**Gap 5 — Tipo de recurso no normalizado**
El `document_url` puede ser PDF, video, HTML o libro. No hay campo que lo indique. **No se puede segmentar el uso por tipo de material.**

---

### 4.4 Frecuencia de eventos `[REQUIERE BD]`

```sql
-- BD lms: frecuencia de eventos por tipo y mes
SELECT
  DATE_TRUNC('month', e.timestamp) AS mes,
  et.type AS tipo,
  COUNT(*) AS cantidad,
  COUNT(DISTINCT e.application_instance_id) AS instituciones_activas
FROM event e
JOIN event_type et ON et.id = e.type_id
GROUP BY 1, 2 ORDER BY 1 DESC, 3 DESC;

-- BD h: actividad de anotaciones por mes
SELECT
  DATE_TRUNC('month', created) AS mes,
  COUNT(*) AS anotaciones_creadas,
  COUNT(DISTINCT userid) AS usuarios_activos,
  COUNT(*) FILTER (WHERE array_length(references, 1) > 0) AS replies
FROM annotation
WHERE deleted = false
GROUP BY 1 ORDER BY 1 DESC LIMIT 24;
```

---

## Bloque 5 — Modelo Analítico Futuro

### 5.1 Esquema estrella propuesto

```
                    DimDate
                      │
DimInstitution ──── FactEvents ──── DimUser
                      │
DimCourse ──────── FactAnnotations ── DimResource
                      │
DimAssignment ──── FactGrades
```

#### Dimensiones

| Dimensión | Fuente | Campos clave |
|-----------|--------|-------------|
| `DimDate` | Generada | date_key, year, month, week, is_weekend, academic_term |
| `DimInstitution` | `organization` + `application_instances` (lms) | institution_id, name, lms_type, enabled |
| `DimUser` | `lms_user` + `user` (h) | user_id, h_userid, display_name, role, institution_id |
| `DimCourse` | `lms_course` + `lms_term` (lms) | course_id, name, institution_id, term_name, starts_at, ends_at |
| `DimAssignment` | `assignment` (lms) | assignment_id, title, course_id, resource_type, is_gradable |
| `DimResource` | `file` + `document` (lms+h) | resource_id, type, url, title |

#### Tablas de hechos

| Fact | Fuente | Granularidad | Estado |
|------|--------|-------------|--------|
| `FactAnnotations` | `annotation` (h) | 1 fila por anotación | ✅ Factible hoy |
| `FactEvents` | `event` + `event_user` (lms) | 1 fila por evento-usuario | ✅ Factible hoy |
| `FactGrades` | `grading_sync_grade` (lms) | 1 fila por calificación | ✅ Factible hoy |
| `FactSessions` | — | 1 fila por sesión | ❌ Requiere implementar tracking |

### 5.2 Transformaciones necesarias

1. Joinear usuarios: `lms.lms_user.h_userid` → `h.user.userid`
2. Normalizar resource_type: parsear `assignment.document_url` para inferir tipo
3. Inferir replies: `annotation.references IS NOT NULL`
4. Construir DimCourse: joinear `lms_course`, `lms_term`, `lms_course_application_instance`
5. Cruzar anotaciones con cursos: via `h.group.authority_provided_id` → `lms.grouping.authority_provided_id`

---

## Bloque 6 — Roadmap

> **Orden corregido respecto a v1: primero Tracking, luego Data Layer, luego Analytics Product.**
> Un Data Warehouse sin datos de calidad solo organiza información incompleta.

---

### Fase 1 — Tracking (0-3 meses)

**Objetivo: capturar los datos que hoy se pierden.**

| Iniciativa | Impacto negocio | Impacto técnico | Complejidad | Descripción |
|------------|----------------|----------------|-------------|-------------|
| Implementar analytics service en `h` | 🔴 Muy alto | Alto | 🟢 Baja | El endpoint ya existe. Solo falta crear tabla `analytics_event` y persistir. Días de trabajo. |
| Session tracking en client | 🔴 Muy alto | Medio | 🟢 Baja | Trackear `session_start` / `session_end` desde el client JS. Enviar a `/api/analytics/events`. |
| Resource tracking (PDF/video/HTML) | 🔴 Muy alto | Bajo | 🟢 Baja | Agregar `resource_opened` con `resource_type` al client. Agregar campo `resource_type` en `assignment`. |
| Annotation events explícitos | 🔴 Alto | Medio | 🟢 Baja | Crear tabla `annotation_event` en h para persistir create/update/delete. |
| Preservar lti_params antes de purga | 🟡 Medio | Bajo | 🟢 Baja | Evaluar qué campos del lti_params tienen valor analítico antes de que se purguen a 30 días. |

---

### Fase 2 — Data Layer (3-9 meses)

**Objetivo: centralizar los datos para análisis.**

| Iniciativa | Impacto negocio | Impacto técnico | Complejidad | Descripción |
|------------|----------------|----------------|-------------|-------------|
| Data Warehouse (Redshift/BigQuery) | 🔴 Alto | Alto | 🔴 Alta | Implementar DW con el modelo estrella de la Sección 5.1 |
| Pipeline de ingesta (dbt) | 🔴 Alto | Alto | 🟡 Media | Ingesta diaria de h y lms hacia el DW con transformaciones dbt |
| Pipeline HubSpot → DW | 🔴 Muy alto | Medio | 🟡 Media | Conectar datos de revenue con datos de uso |
| KPIs gobernados | 🟡 Alto | Bajo | 🟢 Baja | Definir y publicar métricas oficiales: MAS, MAI, Annotation Rate, Launch→Annotation Conversion |
| Alertas de calidad de datos | 🟡 Medio | Bajo | 🟢 Baja | Automatizar queries del Bloque 3 y alertar si superan umbrales |

---

### Fase 3 — Analytics Product (9-24 meses)

**Objetivo: llevar los datos al producto y al negocio.**

| Iniciativa | Impacto negocio | Impacto técnico | Complejidad | Descripción |
|------------|----------------|----------------|-------------|-------------|
| Dashboard ejecutivo interno | 🔴 Muy alto | Medio | 🟡 Media | Adopción, engagement y salud por institución (para CS y Sales) |
| Dashboard para instructores (embedded) | 🔴 Muy alto | Alto | 🔴 Alta | Participación por alumno, alumnos en riesgo, recursos más usados — embebido en el producto |
| Dashboard para universidades | 🔴 Muy alto | Alto | 🔴 Alta | Métricas de uso institucional — valor percibido por el cliente |
| Predicción de churn | 🔴 Muy alto | Alto | 🔴 Alta | Modelo ML que detecte instituciones en riesgo antes de la renovación |
| Benchmarking | 🟡 Alto | Medio | 🟡 Media | Comparar una universidad contra el promedio de la plataforma |
| Self-Service Analytics | 🟡 Medio | Alto | 🔴 Alta | BI para equipos internos |
| IA Conversacional | 🟢 Medio | Muy alto | 🔴 Muy alta | Preguntas en lenguaje natural sobre uso de cursos |

---

## Oportunidades de Producto Basadas en Datos

> Estas oportunidades conectan el assessment con ingresos futuros.

### Para universidades (clientes)
- **Dashboard institucional**: estudiantes activos, cursos con Hypothesis, anotaciones por período, comparación semestral
- **Benchmark**: "Su universidad genera X% más anotaciones por estudiante que el promedio de la plataforma"
- **Reporte de valor**: al momento de renovar el contrato, un PDF automático con el impacto del año

### Para instructores (usuarios power)
- **Dashboard de curso**: participación por alumno, alumnos sin actividad, recursos más anotados, evolución semanal
- **Alerta de riesgo**: "3 estudiantes no han abierto Hypothesis en los últimos 7 días"
- **Resumen de actividad**: digest semanal de lo que pasó en su curso

### Para el equipo interno (Sales/CS)
- **Health score por cliente**: combinación de adopción + engagement + tendencia
- **Riesgo de churn**: clientes con baja actividad reciente vs su propio historial
- **Pipeline de expansión**: instituciones que usan 1 LMS pero tienen más disponibles

### Para el producto
- **Recomendaciones de recursos**: "Los PDFs generan 3x más anotaciones que los videos en tu plataforma"
- **Insights de uso**: qué features se usan más, cuáles no se usan y deberían promocionarse
- **A/B testing sobre datos reales**: usar la tabla `featurecohort` ya existente para medir impacto de cambios

---

## ¿Qué NO sabemos todavía?

Esta sección es parte integral del assessment. Documenta explícitamente las brechas de información para que no se asuma que el análisis está completo.

### Requiere acceso a base de datos `[REQUIERE BD]`

| Información | Por qué importa |
|-------------|----------------|
| Volumen real de registros por tabla | Entender la escala del sistema y dimensionar soluciones |
| Crecimiento mensual histórico | Proyectar capacidad del DW y detectar anomalías |
| Cardinalidad de campos JSONB (`extra`, `settings`) | Entender qué metadata se guarda en campos no estructurados |
| Distribución real de tipos de eventos | Saber si `configured_launch` domina o si hay balance |
| Tasa real de nulos en campos críticos | Evaluar riesgo de calidad antes de construir el DW |
| Usuarios activos reales (últimos 30/90/180 días) | Baseline para North Star Metrics |

### Requiere entrevistas `[REQUIERE ENTREVISTA]`

| Información | Con quién |
|-------------|----------|
| Modelo de pricing (¿por estudiante? ¿por institución? ¿por feature?) | Finance / CEO |
| Proceso de renovación y señales de churn | Customer Success |
| Qué métricas usa Sales para cerrar contratos | Sales |
| Qué métricas piden los clientes (universidades) | Customer Success / Account Managers |
| Roadmap de producto (qué features vienen) | Product Manager |
| OKRs del año (qué quiere medir el Board) | CEO / CTO |
| Ownership real de dominios de datos | Tech Leads de cada equipo |

### Requiere acceso a herramientas externas `[REQUIERE ACCESO]`

| Herramienta | Datos buscados |
|-------------|---------------|
| **HubSpot** | Contratos, deals, fechas de renovación, contactos clave, pipeline |
| **Google Analytics** | Confirmar si está activo, qué eventos están configurados, volumen de sesiones |
| **New Relic** | Performance actual, errores más frecuentes, endpoints más lentos |
| **Sentry** | Errores más frecuentes en producción, frecuencia, impacto |
| **Sistema de billing** | Facturas, montos, fechas de pago, plan por cliente |

---

## Apéndice — Próximos pasos para completar el assessment

Una vez que se tenga acceso a base de datos, ejecutar las siguientes queries en orden:

1. **Volumen general** (Sección 2.5) — entender la escala del sistema
2. **Completitud** (Sección 3.1) — identificar campos críticos vacíos
3. **Duplicados** (Sección 3.2) — medir confiabilidad de identidades
4. **Consistencia** (Sección 3.3) — validar reglas de negocio
5. **Integridad referencial** (Sección 3.4) — detectar registros huérfanos
6. **Frecuencia de eventos** (Sección 4.4) — entender patrones de uso

Con esos resultados, completar las columnas "Registros" y "Crecimiento" del inventario de tablas (Secciones 2.2 y 2.3) y ajustar el roadmap según la criticidad de los problemas encontrados.

Paralelamente, agendar entrevistas con Finance, Sales, Customer Success y Product para completar el Revenue Data Assessment y el Bloque 0.

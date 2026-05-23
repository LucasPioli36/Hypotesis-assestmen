# Hypothesis Platform — Data Assessment
**Fecha:** 2026-05-22  
**Autor:** Data Engineering  
**Estado:** Fase 1 — Assessment desde código fuente (sin acceso a BD)

---

## Resumen Ejecutivo

Este documento es el resultado del assessment de datos de la plataforma Hypothesis. La empresa vende a universidades una herramienta de anotaciones digitales que se integra con sus sistemas de gestión de aprendizaje (LMS). Los usuarios (estudiantes y profesores) pueden anotar PDFs, videos, páginas web y material de estudio.

**Scope del assessment:** análisis completo desde código fuente de los 3 repositorios principales (`h`, `lms`, `client`). Las secciones que requieren acceso a base de datos están marcadas con `[REQUIERE BD]` e incluyen las queries SQL necesarias.

### Respuestas a las 7 preguntas clave

| Pregunta | Estado | Respuesta resumida |
|----------|--------|--------------------|
| ¿Qué datos existen? | ✅ | ~61 tablas entre h y lms: anotaciones, usuarios, cursos, asignaciones, eventos, calificaciones |
| ¿Dónde viven? | ✅ | 2 BDs PostgreSQL en AWS RDS + Elasticsearch para búsqueda |
| ¿Cómo fluyen? | ✅ | h ↔ lms vía API REST + RabbitMQ + Foreign Data Wrapper |
| ¿Qué tan confiables? | 🔲 | Requiere acceso a BD — queries provistas en Bloque 3 |
| ¿Qué métricas se pueden construir? | ⚠️ | Limitadas: conteos de anotaciones, launches LTI, calificaciones. Faltan métricas de engagement |
| ¿Qué falta capturar? | ✅ | Apertura de PDFs/videos, tiempo de uso, búsquedas, sesiones, engagement por recurso |
| ¿Cuál es el roadmap? | ✅ | Ver Bloque 6 |

---

## Bloque 1 — Arquitectura

### 1.1 Repositorios

| Repositorio | Función | Tecnología | Base de datos | Responsable |
|-------------|---------|-----------|---------------|-------------|
| `hypothesis/h` | Backend central: API REST de anotaciones, autenticación, grupos, búsqueda, panel admin | Python 3.11 + Pyramid, Celery, Gunicorn | PostgreSQL (BD principal) + Elasticsearch | Backend team |
| `hypothesis/lms` | Integración con LMS educativos (Canvas, Blackboard, D2L, Moodle) vía protocolo LTI 1.1/1.3 | Python 3.11 + Pyramid, Celery, Gunicorn | PostgreSQL (BD separada) | LMS/EdTech team |
| `hypothesis/client` | Cliente JavaScript inyectable en cualquier página web; permite anotar HTML, PDFs, videos | TypeScript + Preact + Redux, Rollup | Sin BD propia (consume API de h) | Frontend team |

**Preguntas del framework:**

- **¿Cuántos repositorios existen?** 3 repositorios principales + librerías compartidas (`@hypothesis/frontend-shared`, `h-api`, `h-vialib`)
- **¿Cuál es el producto principal?** `h` es el núcleo; `lms` es el canal de distribución a universidades; `client` es la UI
- **¿Existen microservicios?** No. Arquitectura monolítica por repo (Pyramid WSGI)
- **¿Existen procesos batch?** Sí: Celery workers en `h` (indexación, emails) y `lms` (digests, sincronización de calificaciones, HubSpot)
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
| `/api/groups/{id}` | GET/PATCH/DELETE | CRUD de grupo |
| `/api/users` | POST | Crear usuario |
| `/api/profile` | GET/PATCH | Perfil del usuario autenticado |
| `/api/token` | GET | Obtener API token |
| `/api/bulk` | POST | Operaciones masivas (usado por lms) |
| `/api/bulk/lms/annotations` | POST | Bulk annotations para LMS |
| `/api/analytics/events` | POST | Registrar eventos analytics (⚠️ incompleto) |
| `/oauth/authorize` | GET/POST | OAuth 2.0 Authorization |
| `/oauth/revoke` | POST | Revocar token |

#### `lms` — API de integración LTI

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/lti_launches` | POST | Launch LTI (entry point desde LMS) |
| `/lti/1.3/oidc` | GET/POST | OIDC para LTI 1.3 |
| `/lti/1.3/jwks` | GET | JSON Web Key Set |
| `/api/sync` | POST | Sincronizar grupos con h |
| `/api/grant_token` | GET | Token para el client |
| `/api/lti/result` | GET/POST | Calificaciones LTI |
| `/api/dashboard/assignments` | GET | Asignaciones del dashboard |
| `/api/dashboard/students/metrics` | GET | Métricas de estudiantes |
| `/api/canvas/courses/{id}/files` | GET | Archivos de Canvas |
| `/api/blackboard/courses/{id}/files` | GET | Archivos de Blackboard |
| `/api/d2l/courses/{id}/files` | GET | Archivos de D2L |
| `/api/jstor/articles/{id}` | GET | Metadata JSTOR |
| `/api/vitalsource/books/{id}` | GET | Info de libro |
| `/api/youtube/videos/{id}` | GET | Metadata de video |
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
│    Elasticsearch      │   │  - Sidebar con lista de       │
│  - Publica a          │   │    anotaciones               │
│    RabbitMQ           │   └──────────────────────────────┘
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

**Flujo de una anotación (end-to-end):**
1. Estudiante selecciona texto → `client` llama `POST /api/annotations` en `h`
2. `h` guarda en PostgreSQL, indexa en Elasticsearch, publica evento a RabbitMQ
3. WebSocket (`h-websocket`) notifica a otros clientes conectados en tiempo real
4. `lms` Celery worker recibe el evento → procesa menciones → envía email si corresponde
5. Dashboard del instructor consulta `h` Bulk API para mostrar métricas de actividad
6. Celery task de calificaciones procesa anotaciones y envía nota al LMS (Canvas/Blackboard/etc.)

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
| `annotation_slim` | Vista desnormalizada de anotaciones para queries rápidas (no tiene text/selectors) | `id` | `pubid → annotation`, `user_id → user`, `group_id → group`, `document_id → document` |
| `annotation_metadata` | Metadata JSONB extendida de anotaciones | `annotation_id` | `annotation_id → annotation_slim` |
| `document` | Documento web anotado (agrupa URIs que representan el mismo contenido) | `id` | — |
| `document_uri` | URIs concretas de un documento (una URL puede tener múltiples formas) | `id` | `document_id → document` |
| `document_meta` | Metadata del documento (título, autor, etc.) | `id` | `document_id → document` |
| `mention` | Menciones de usuarios dentro de anotaciones (`@usuario`) | `id` | `annotation_id → annotation`, `user_id → user` |
| `notification` | Notificaciones enviadas (reply, mention) — registro histórico | `id` | `source_annotation_id → annotation`, `recipient_id → user` |
| `flag` | Reportes/flags de anotaciones por usuarios | `id` | `annotation_id → annotation`, `user_id → user` |
| `moderation_log` | Log de cambios de estado de moderación (APPROVED/PENDING/DENIED/SPAM) | `id` | `annotation_id → annotation`, `moderator_id → user` |
| `subscriptions` | Preferencias de notificación de usuarios | `id` | — |
| `feature` | Feature flags del sistema | `id` | — |
| `featurecohort` | Grupos de usuarios para A/B testing | `id` | — |
| `featurecohort_user` | Relación usuario-cohorte | `id` | `user_id → user`, `cohort_id → featurecohort` |
| `featurecohort_feature` | Relación cohorte-feature | `id` | `feature_id → feature`, `cohort_id → featurecohort` |
| `job` | Cola de jobs internos (indexación, purga) | `id` | — |
| `task_done` | Registro de tareas completadas (para evitar duplicados) | `id` | — |
| `user_deletion` | Auditoría de deletions de usuarios (username, fecha, quién lo pidió) | `id` | — |
| `blocklist` | URIs bloqueadas (no se pueden anotar) | `id` | — |
| `setting` | Key-value settings del sistema | `key` | — |

**Total: 31 tablas**

**Campos críticos de `annotation`:**

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | UUID | Identificador público de la anotación |
| `userid` | text | Identificador del autor (`acct:usuario@dominio`) |
| `groupid` | text | Grupo donde se publicó (pubid del grupo) |
| `text` | text | Contenido de la anotación (markdown) |
| `tags` | text[] | Tags de la anotación |
| `shared` | boolean | Pública (true) o privada (false) |
| `target_uri` | text | URL del documento anotado |
| `target_selectors` | JSONB | Selectores de posición (TextPositionSelector, TextQuoteSelector, etc.) |
| `references` | UUID[] | IDs de anotaciones padre (threading) |
| `moderation_status` | enum | APPROVED / PENDING / DENIED / SPAM |
| `deleted` | boolean | Borrado lógico |
| `created` | datetime | Fecha de creación |
| `updated` | datetime | Última modificación |

---

### 2.3 Inventario de tablas — BD `lms`

| Tabla | Descripción | PK | FKs principales |
|-------|-------------|-----|----------------|
| `organization` | Organización educativa (universidad). Puede tener jerarquía (parent_id) | `id` | `parent_id → organization` |
| `application_instances` | Instalación específica de Hypothesis en un LMS. Una universidad puede tener varias | `id` | `organization_id → organization`, `lti_registration_id → lti_registration` |
| `lti_registration` | Registro LTI 1.3 (issuer, client_id, URLs de auth/keys/token) | `id` | — |
| `lms_user` | Usuario canónico del LMS (desacoplado de instancia). Tiene h_userid para vincular con h | `id` | — |
| `user` | Usuario en el contexto de una instancia específica del LMS | `id` | `application_instance_id → application_instances` |
| `lms_user_application_instance` | Relación entre usuarios y las instancias a las que pertenecen | `id` | `lms_user_id → lms_user`, `application_instance_id → application_instances` |
| `lms_term` | Período académico (trimestre, semestre) con fechas de inicio/fin | `id` | — |
| `lms_course` | Curso en el LMS. Puede ser copia de otro (copied_from_id) | `id` | `lms_term_id → lms_term` |
| `lms_course_application_instance` | Relación curso-instancia (un curso puede aparecer en múltiples instancias) | `id` | `lms_course_id → lms_course`, `application_instance_id → application_instances` |
| `lms_course_membership` | Membresía de usuarios en cursos con su rol LTI | `id` | `lms_course_id → lms_course`, `lms_user_id → lms_user`, `lti_role_id → lti_role` |
| `lti_role` | Roles LTI (instructor, learner, admin, test_user) con scope (course, institution, system) | `id` | — |
| `lti_role_override` | Override de roles por instancia (permite customizar comportamiento por cliente) | `id` | `lti_role_id → lti_role`, `application_instance_id → application_instances` |
| `grouping` | Entidad polimórfica: puede ser curso, sección (Canvas), grupo (Canvas/BB/D2L/Moodle) | `id` | `application_instance_id → application_instances`, `parent_id → grouping` |
| `grouping_membership` | Membresía de usuarios en groupings | `(grouping_id, user_id)` | `grouping_id → grouping`, `user_id → user` |
| `group_info` | Información legacy de grupos del LMS (contexto, consumer key, metadata LMS) | `id` | `application_instance_id → application_instances` |
| `assignment` | Asignación/tarea en Hypothesis. Tiene URL del documento a anotar | `id` | `course_id → grouping`, `auto_grading_config_id → assignment_auto_grading_config` |
| `assignment_auto_grading_config` | Configuración de auto-calificación (cantidad de anotaciones requeridas) | `id` | — |
| `assignment_grouping` | Relación entre asignaciones y groupings | `(assignment_id, grouping_id)` | `assignment_id → assignment`, `grouping_id → grouping` |
| `file` | Archivo del LMS referenciado en una asignación (PDF, página, video) | `id` | `application_instance_id → application_instances` |
| `grading_sync` | Proceso de sincronización de calificaciones para una asignación | `id` | `assignment_id → assignment`, `created_by_id → lms_user` |
| `grading_sync_grade` | Calificación individual de un estudiante en un proceso de sync | `id` | `grading_sync_id → grading_sync`, `lms_user_id → lms_user` |
| `lis_result_sourcedid` | Info de calificación LTI 1.1 (legacy) | `id` | `application_instance_id → application_instances` |
| `oauth2_token` | Tokens OAuth2 para acceder a APIs de LMS (Canvas, Blackboard, D2L) | `id` | `application_instance_id → application_instances` |
| `jwt_oauth2_token` | Tokens JWT para LTI 1.3 | `id` | `lti_registration_id → lti_registration` |
| `rsa_key` | Claves RSA para firma JWT LTI 1.3 (con rotación) | `id` | — |
| `event` | **Tabla de eventos**: registra acciones en el sistema (launch, grade, deep linking, etc.) | `id` | `type_id → event_type`, `application_instance_id → application_instances`, `course_id → grouping`, `assignment_id → assignment` |
| `event_type` | Catálogo de tipos de evento | `id` | — |
| `event_user` | Usuarios que participaron en un evento y su rol | `id` | `event_id → event`, `user_id → user`, `lti_role_id → lti_role` |
| `event_data` | Datos extra del evento en JSONB (ej: lti_params, cambios de modelo) | `event_id` | `event_id → event` |
| `notification` | Notificaciones de reply/mention en contexto LMS | `id` | `sender_id → lms_user`, `recipient_id → lms_user`, `assignment_id → assignment` |

**Total: 30 tablas**

---

### 2.4 Relaciones entre BDs

El campo clave que conecta las dos BDs es `h_userid` (ej: `acct:usuario@lms.hypothes.is`):

```
lms.lms_user.h_userid  ←→  h.user.userid (formato: acct:username@authority)
lms.grouping.authority_provided_id  ←→  h.group.authority_provided_id
```

La BD `lms` puede leer la BD `h` directamente via **Foreign Data Wrapper (FDW)** configurado en la variable `H_FDW_DATABASE_URL`.

---

### 2.5 Inventario de tablas — Conteos `[REQUIERE BD]`

Ejecutar en BD `h`:
```sql
-- Conteo y crecimiento de las tablas principales
SELECT
  schemaname,
  relname AS tabla,
  n_live_tup AS registros_estimados,
  n_dead_tup AS registros_muertos,
  last_autovacuum,
  last_autoanalyze
FROM pg_stat_user_tables
ORDER BY n_live_tup DESC;

-- Crecimiento mensual de anotaciones
SELECT
  DATE_TRUNC('month', created) AS mes,
  COUNT(*) AS nuevas_anotaciones,
  COUNT(*) FILTER (WHERE shared = true) AS publicas,
  COUNT(*) FILTER (WHERE shared = false) AS privadas,
  COUNT(*) FILTER (WHERE deleted = true) AS borradas
FROM annotation
GROUP BY 1
ORDER BY 1 DESC
LIMIT 24;

-- Crecimiento mensual de usuarios
SELECT
  DATE_TRUNC('month', registered_date) AS mes,
  COUNT(*) AS nuevos_usuarios
FROM "user"
WHERE deleted = false
GROUP BY 1
ORDER BY 1 DESC
LIMIT 24;
```

Ejecutar en BD `lms`:
```sql
-- Launches por mes (métrica clave de adopción)
SELECT
  DATE_TRUNC('month', e.timestamp) AS mes,
  et.type AS tipo_evento,
  COUNT(*) AS cantidad
FROM event e
JOIN event_type et ON e.type_id = et.id
GROUP BY 1, 2
ORDER BY 1 DESC, 3 DESC;

-- Instituciones activas
SELECT
  o.name AS organizacion,
  COUNT(DISTINCT ai.id) AS instancias,
  COUNT(DISTINCT lc.id) AS cursos,
  COUNT(DISTINCT a.id) AS asignaciones
FROM organization o
JOIN application_instances ai ON ai.organization_id = o.id
LEFT JOIN lms_course_application_instance lcai ON lcai.application_instance_id = ai.id
LEFT JOIN lms_course lc ON lc.id = lcai.lms_course_id
LEFT JOIN assignment a ON a.course_id IS NOT NULL
GROUP BY 1
ORDER BY 3 DESC;
```

---

## Bloque 3 — Calidad de Datos

> **Nota:** Esta sección requiere acceso a base de datos. Se proveen las queries para ejecutar una vez que se tenga acceso.

### 3.1 Completitud `[REQUIERE BD]`

```sql
-- === BD h ===

-- Usuarios sin email (no pueden recibir notificaciones)
SELECT
  COUNT(*) AS total_usuarios,
  COUNT(*) FILTER (WHERE email IS NULL OR email = '') AS sin_email,
  ROUND(100.0 * COUNT(*) FILTER (WHERE email IS NULL OR email = '') / COUNT(*), 2) AS pct_sin_email
FROM "user"
WHERE deleted = false;

-- Anotaciones sin usuario válido
SELECT COUNT(*) AS anotaciones_sin_userid
FROM annotation
WHERE userid IS NULL OR userid = '';

-- Anotaciones sin documento
SELECT COUNT(*) AS anotaciones_sin_documento
FROM annotation
WHERE document_id IS NULL;

-- Anotaciones sin target_uri (no se sabe qué se anotó)
SELECT COUNT(*) AS anotaciones_sin_uri
FROM annotation
WHERE target_uri IS NULL OR target_uri = '';

-- Grupos sin creator
SELECT COUNT(*) AS grupos_sin_creator
FROM "group"
WHERE creator_id IS NULL;

-- === BD lms ===

-- Usuarios LMS sin h_userid (no están vinculados a Hypothesis)
SELECT COUNT(*) AS usuarios_sin_h_userid
FROM lms_user
WHERE h_userid IS NULL OR h_userid = '';

-- Asignaciones sin document_url
SELECT COUNT(*) AS asignaciones_sin_url
FROM assignment
WHERE document_url IS NULL OR document_url = '';

-- Eventos sin usuario asociado
SELECT COUNT(*) AS eventos_sin_usuario
FROM event e
LEFT JOIN event_user eu ON eu.event_id = e.id
WHERE eu.user_id IS NULL;

-- Launches sin course_id
SELECT
  COUNT(*) AS total_launches,
  COUNT(*) FILTER (WHERE course_id IS NULL) AS sin_course,
  ROUND(100.0 * COUNT(*) FILTER (WHERE course_id IS NULL) / COUNT(*), 2) AS pct_sin_course
FROM event e
JOIN event_type et ON et.id = e.type_id
WHERE et.type = 'configured_launch';
```

### 3.2 Duplicados `[REQUIERE BD]`

```sql
-- === BD h ===

-- Usuarios con el mismo email en la misma authority
SELECT email, authority, COUNT(*) AS duplicados
FROM "user"
WHERE email IS NOT NULL AND deleted = false
GROUP BY email, authority
HAVING COUNT(*) > 1
ORDER BY duplicados DESC
LIMIT 20;

-- Anotaciones duplicadas (mismo userid, mismo documento, mismo texto)
SELECT userid, document_id, MD5(COALESCE(text, '')), COUNT(*) AS duplicados
FROM annotation
WHERE deleted = false
GROUP BY 1, 2, 3
HAVING COUNT(*) > 1
ORDER BY duplicados DESC
LIMIT 20;

-- === BD lms ===

-- Usuarios LMS duplicados por h_userid
SELECT h_userid, COUNT(*) AS duplicados
FROM lms_user
GROUP BY h_userid
HAVING COUNT(*) > 1;

-- Launches duplicados en el mismo día para la misma asignación y usuario
SELECT
  e.assignment_id,
  eu.user_id,
  DATE_TRUNC('day', e.timestamp) AS dia,
  COUNT(*) AS launches
FROM event e
JOIN event_type et ON et.id = e.type_id
JOIN event_user eu ON eu.event_id = e.id
WHERE et.type = 'configured_launch'
GROUP BY 1, 2, 3
HAVING COUNT(*) > 5
ORDER BY 4 DESC
LIMIT 20;
```

### 3.3 Consistencia `[REQUIERE BD]`

```sql
-- === BD h ===

-- Emails con formato inválido
SELECT COUNT(*) AS emails_invalidos
FROM "user"
WHERE email IS NOT NULL
  AND email NOT LIKE '%@%.%';

-- Anotaciones con updated < created (inconsistencia de fechas)
SELECT COUNT(*) AS inconsistencias_fecha
FROM annotation
WHERE updated < created;

-- Anotaciones con moderation_status pero deleted = true (estado inconsistente)
SELECT COUNT(*) AS inconsistencias_moderacion
FROM annotation
WHERE deleted = true AND moderation_status IS NOT NULL;

-- === BD lms ===

-- Cursos con ends_at < starts_at
SELECT COUNT(*) AS cursos_fechas_invalidas
FROM lms_course
WHERE ends_at IS NOT NULL AND starts_at IS NOT NULL AND ends_at < starts_at;

-- Calificaciones fuera de rango [0, 1]
SELECT COUNT(*) AS notas_invalidas
FROM grading_sync_grade
WHERE grade < 0 OR grade > 1;

-- GradingSync en estado inconsistente (finished pero con grades pending)
SELECT COUNT(*) AS syncs_inconsistentes
FROM grading_sync gs
WHERE gs.status = 'finished'
  AND EXISTS (
    SELECT 1 FROM grading_sync_grade gsg
    WHERE gsg.grading_sync_id = gs.id AND gsg.success IS NULL
  );
```

### 3.4 Integridad Referencial `[REQUIERE BD]`

```sql
-- === BD h ===

-- Anotaciones cuyo userid no existe en la tabla user
SELECT COUNT(*) AS anotaciones_huerfanas
FROM annotation a
WHERE NOT EXISTS (
  SELECT 1 FROM "user" u
  WHERE 'acct:' || u.username || '@' || u.authority = a.userid
);

-- annotation_slim sin annotation padre
SELECT COUNT(*) AS slim_huerfanos
FROM annotation_slim asm
WHERE NOT EXISTS (
  SELECT 1 FROM annotation a WHERE a.id = asm.pubid
);

-- === BD lms ===

-- Usuarios LMS cuyo h_userid no existe en BD h (via FDW)
-- (Requiere FDW configurado)
SELECT COUNT(*) AS usuarios_sin_cuenta_h
FROM lms.lms_user lu
WHERE lu.h_userid IS NOT NULL
  AND NOT EXISTS (
    SELECT 1 FROM h.user u
    WHERE 'acct:' || u.username || '@' || u.authority = lu.h_userid
  );

-- Events con application_instance_id inexistente
SELECT COUNT(*) AS eventos_huerfanos
FROM event e
WHERE e.application_instance_id IS NOT NULL
  AND NOT EXISTS (
    SELECT 1 FROM application_instances ai WHERE ai.id = e.application_instance_id
  );
```

### 3.5 Volumen `[REQUIERE BD]`

```sql
-- Tamaño de las tablas principales
SELECT
  relname AS tabla,
  pg_size_pretty(pg_total_relation_size(relid)) AS tamaño_total,
  pg_size_pretty(pg_relation_size(relid)) AS tamaño_datos,
  pg_size_pretty(pg_total_relation_size(relid) - pg_relation_size(relid)) AS tamaño_indices,
  n_live_tup AS filas_estimadas
FROM pg_stat_user_tables
ORDER BY pg_total_relation_size(relid) DESC
LIMIT 20;
```

---

## Bloque 4 — Assessment de Tracking

### 4.1 Eventos existentes

#### BD `lms` — Eventos persistidos en tabla `event`

| Evento | Fuente | Tabla | Descripción | Frecuencia |
|--------|--------|-------|-------------|------------|
| `configured_launch` | LMS (LTI) | `event` | Usuario abre Hypothesis desde el LMS | Alta — cada sesión |
| `deep_linking` | LMS (LTI) | `event` | Profesor configura una asignación nueva | Media |
| `edited_assignment` | Admin/LMS | `event` | Profesor edita una asignación existente | Baja |
| `submission` | LMS (LTI) | `event` | Estudiante envía trabajo (speedgrader) | Media |
| `grade` | LMS (Celery) | `event` | Sistema sincroniza calificación con LMS | Media |
| `audit` | Admin | `event` | Cambios en modelos (insert/update/delete) | Variable |
| `error_code` | API | `event` | Error capturado durante una acción LTI | Baja |

> Los `lti_params` del evento se purgan automáticamente después de 30 días (Celery task).

#### BD `h` — Eventos en memoria (no persistidos)

| Evento | Fuente | Persistencia | Acciones disparadas |
|--------|--------|-------------|-------------------|
| `AnnotationEvent (create)` | API `/api/annotations` | ❌ No | Elasticsearch sync, WebSocket broadcast, email reply/mention |
| `AnnotationEvent (update)` | API `/api/annotations/{id}` | ❌ No | Elasticsearch sync, WebSocket broadcast |
| `AnnotationEvent (delete)` | API `/api/annotations/{id}` | ❌ No | Elasticsearch delete, WebSocket broadcast |
| `ModeratedAnnotationEvent` | API moderación | ❌ No | Email de notificación de moderación |
| `AnnotationFlagged` | API flags | ❌ No | Email a moderadores |
| `LoginEvent` | Web login | ❌ No | Solo logging |
| `LogoutEvent` | Web logout | ❌ No | Solo logging |
| `PasswordResetEvent` | Web account | ❌ No | Solo logging |
| `ActivationEvent` | Web signup | ❌ No | Email de bienvenida |

> **⚠️ Hallazgo crítico:** En `h` no hay tabla de eventos. Todas las acciones sobre anotaciones se procesan en memoria y se pierden como eventos analíticos. La única traza que queda es el registro en la tabla `annotation`.

#### Frontend `client` — Analytics

| Evento | Dónde | Persistencia | Descripción |
|--------|-------|-------------|-------------|
| `client.realtime.apply_updates` | `analytics.ts` | Logging en `h` | Cuando el usuario acepta actualizaciones en tiempo real |

> **⚠️ Hallazgo crítico:** El servicio `analytics.py` en `h` solo hace logging (`TODO: Enhance this`). No hay tabla de analytics en `h`.

---

### 4.2 Cobertura actual vs ideal

| Acción del usuario | Trackeado | Dónde | Notas |
|-------------------|-----------|-------|-------|
| Abrir Hypothesis desde LMS | ✅ | `event` (lms) | `configured_launch` |
| Crear anotación | ⚠️ | Solo en tabla `annotation` (h) | No hay evento explícito, hay que inferirlo |
| Editar anotación | ⚠️ | Solo en `annotation.updated` (h) | No hay log de versiones |
| Eliminar anotación | ⚠️ | `annotation.deleted = true` (h) | No hay evento explícito |
| Crear highlight (sin texto) | ⚠️ | `annotation` con `text = null` (h) | Se puede filtrar pero no es explícito |
| Responder a anotación | ⚠️ | `annotation.references` (h) | Se puede inferir por el campo `references` |
| Mencionar usuario | ✅ | `mention` (h) | Guardado en tabla |
| Reportar anotación | ✅ | `flag` (h) | Guardado en tabla |
| Configurar asignación | ✅ | `event` (lms) | `deep_linking` o `edited_assignment` |
| Calificación sincronizada | ✅ | `grading_sync_grade` (lms) | Con resultado (success/failure) |
| **Abrir PDF** | ❌ | — | No trackeado |
| **Abrir video** | ❌ | — | No trackeado |
| **Búsqueda dentro del sidebar** | ❌ | — | No trackeado |
| **Tiempo de uso en la página** | ❌ | — | No trackeado |
| **Scroll / lectura** | ❌ | — | No trackeado |
| **Cambio de tab** | ❌ | — | No trackeado |
| **Login/Logout** | ❌ | — | Solo log, no persistido |
| **Signup de nuevo usuario** | ❌ | — | Solo log, no persistido |
| **Compartir anotación** | ❌ | — | No trackeado explícitamente |
| **Exportar anotaciones** | ❌ | — | No trackeado |
| **Uso por recurso (PDF vs video vs HTML)** | ❌ | — | No hay campo de tipo de recurso |

---

### 4.3 Gaps críticos (con impacto en negocio)

**Gap 1 — No se mide engagement real con el contenido**
- No hay tracking de apertura de PDFs, videos o libros
- No se puede saber cuánto tiempo un estudiante está activo en Hypothesis
- **Impacto**: imposible calcular métricas de valor como "tiempo de uso" o "recursos más anotados"

**Gap 2 — El analytics service en `h` no está implementado**
- El endpoint `/api/analytics/events` existe pero solo loguea (TODO en el código)
- Solo 1 tipo de evento está siendo enviado desde el cliente (`client.realtime.apply_updates`)
- **Impacto**: toda la plataforma `h` carece de analytics funcional

**Gap 3 — Acciones de anotación no tienen eventos propios**
- Crear/editar/eliminar anotaciones no genera registros en una tabla de eventos
- Solo se puede reconstruir actividad a partir de timestamps en `annotation`
- **Impacto**: no hay una fuente de verdad para "actividad de anotación en el tiempo"

**Gap 4 — No hay concepto de "sesión"**
- No se puede saber cuándo empieza y termina el uso de un estudiante
- El `configured_launch` registra el inicio, pero no el fin de sesión
- **Impacto**: no se pueden calcular métricas de retención o engagement por sesión

**Gap 5 — Tipo de recurso no está normalizado**
- El `document_url` en `assignment` puede ser PDF, video, HTML, libro, etc.
- No hay un campo que normalice el tipo de recurso
- **Impacto**: no se puede segmentar el uso por tipo de material

---

### 4.4 Frecuencia de eventos `[REQUIERE BD]`

```sql
-- BD lms: frecuencia de eventos por tipo y mes
SELECT
  DATE_TRUNC('month', e.timestamp) AS mes,
  et.type AS tipo,
  COUNT(*) AS cantidad,
  COUNT(DISTINCT e.application_instance_id) AS instituciones_activas,
  COUNT(DISTINCT e.course_id) AS cursos_activos
FROM event e
JOIN event_type et ON et.id = e.type_id
GROUP BY 1, 2
ORDER BY 1 DESC, 3 DESC;

-- BD h: actividad de anotaciones por mes (proxy de eventos)
SELECT
  DATE_TRUNC('month', created) AS mes,
  COUNT(*) AS anotaciones_creadas,
  COUNT(DISTINCT userid) AS usuarios_activos,
  COUNT(DISTINCT document_id) AS documentos_anotados,
  COUNT(*) FILTER (WHERE array_length(references, 1) > 0) AS replies,
  COUNT(*) FILTER (WHERE text IS NULL OR text = '') AS highlights_puros
FROM annotation
WHERE deleted = false
GROUP BY 1
ORDER BY 1 DESC
LIMIT 24;
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
                      │
                    DimFeature
```

#### Dimensiones

| Dimensión | Fuente | Campos clave |
|-----------|--------|-------------|
| `DimDate` | Generada | date_key, year, month, week, day, is_weekend, academic_term |
| `DimInstitution` | `lms.organization` + `lms.application_instances` | institution_id, name, lms_type (Canvas/BB/D2L/Moodle), enabled, created_at |
| `DimUser` | `lms.lms_user` + `h.user` | user_id, h_userid, display_name, email, role (instructor/learner), institution_id |
| `DimCourse` | `lms.lms_course` + `lms.lms_term` | course_id, name, institution_id, term_name, starts_at, ends_at |
| `DimAssignment` | `lms.assignment` | assignment_id, title, course_id, document_url, resource_type, is_gradable |
| `DimResource` | `lms.file` + `h.document` | resource_id, type (pdf/video/html/book), url, title |
| `DimFeature` | `h.feature` | feature_id, name, enabled_for |

#### Tablas de hechos

| Fact | Fuente | Granularidad | Métricas |
|------|--------|-------------|---------|
| `FactAnnotations` | `h.annotation` + `h.annotation_slim` | 1 fila por anotación | count, is_reply, is_highlight, has_text, tags_count, mentions_count |
| `FactEvents` | `lms.event` + `lms.event_user` | 1 fila por evento-usuario | event_type, launch_count, grade_count |
| `FactGrades` | `lms.grading_sync_grade` | 1 fila por calificación | grade (0-1), success, sync_timestamp |
| `FactSessions` | ⚠️ A construir | 1 fila por sesión | duration, annotations_in_session, resources_opened |

---

### 5.2 Factibilidad por tabla de hechos

| Tabla | Factibilidad | Datos disponibles | Qué falta |
|-------|-------------|-------------------|-----------|
| `FactAnnotations` | ✅ Alta | `annotation`, `annotation_slim`, `mention`, `flag` | Cruzar con `DimUser` via userid, cruzar con `DimCourse` via groupid |
| `FactEvents` | ✅ Alta | `event`, `event_user`, `event_type` (lms) | Solo cubre eventos LMS; eventos de anotación no están |
| `FactGrades` | ✅ Alta | `grading_sync`, `grading_sync_grade` | Cruzar con `DimUser` via lms_user_id |
| `FactSessions` | ❌ No existe | — | Requiere implementar tracking de sesión desde cero |

---

### 5.3 Transformaciones necesarias

1. **Joinear usuarios entre BDs**: `lms.lms_user.h_userid` → `h.user.userid` (formato `acct:username@authority`)
2. **Normalizar resource_type**: parsear `assignment.document_url` para inferir tipo (PDF, video, HTML, libro)
3. **Inferir replies**: `annotation.references IS NOT NULL AND cardinality(references) > 0`
4. **Inferir highlights**: `annotation.text IS NULL OR annotation.text = ''`
5. **Construir DimCourse**: joinear `lms_course`, `lms_term`, `lms_course_application_instance`
6. **Cruzar anotaciones con cursos**: via `h.group.authority_provided_id` → `lms.grouping.authority_provided_id`

---

### 5.4 Herramientas recomendadas para el Data Warehouse

| Capa | Opción recomendada | Alternativa |
|------|-------------------|-------------|
| Almacenamiento | **Redshift** (ya en AWS) o **BigQuery** | Snowflake |
| Ingesta | **dbt** para transformaciones | SQLMesh |
| Orquestación | **Airflow** o **Dagster** | Prefect |
| BI | **Metabase** (open source) | Looker, Power BI |
| Tiempo real | **Kafka** (si se agrega tracking de eventos) | Kinesis |

---

## Bloque 6 — Roadmap de Datos

### Nivel 1 — Quick Wins (0-3 meses)

| Iniciativa | Impacto | Esfuerzo | Descripción |
|------------|---------|---------|-------------|
| **Diccionario de datos** | Alto | Bajo | Documentar todas las tablas, campos y dueños funcionales. Base de este assessment |
| **Implementar analytics service en `h`** | Alto | Bajo | El endpoint ya existe, solo falta persistir los eventos en una tabla. Crear tabla `analytics_event` en h |
| **Agregar eventos de sesión al client** | Alto | Medio | Trackear `session_start` y `session_end` desde el client JS. Enviar a `/api/analytics/events` |
| **Trackear apertura de recursos** | Alto | Bajo | Agregar `resource_opened` (con tipo: pdf/video/html/book) al cliente |
| **Normalizar tipo de recurso** | Medio | Bajo | Agregar campo `resource_type` en tabla `assignment` (lms) |
| **Dashboard de adopción básico** | Alto | Medio | Construir dashboard con datos de `lms.event`: launches por institución, cursos activos, asignaciones |
| **Queries de calidad de datos** | Medio | Bajo | Ejecutar las queries de este assessment y documentar el estado actual |

---

### Nivel 2 — Mediano Plazo (3-9 meses)

| Iniciativa | Impacto | Esfuerzo | Descripción |
|------------|---------|---------|-------------|
| **Data Warehouse** | Muy alto | Alto | Implementar DW en Redshift o BigQuery con el modelo estrella propuesto (Bloques 5.1/5.2) |
| **Pipeline de datos** | Muy alto | Alto | Ingesta diaria de `h` y `lms` hacia el DW con dbt para transformaciones |
| **Modelo de eventos en `h`** | Alto | Medio | Crear tabla `annotation_event` en h para persistir create/update/delete de anotaciones |
| **KPIs gobernados** | Alto | Medio | Definir y publicar métricas oficiales: DAU, MAU, annotations per user, launch-to-annotate rate |
| **Dashboards ejecutivos** | Alto | Medio | Dashboards de adopción, engagement y valor por institución |
| **Alertas de calidad de datos** | Medio | Medio | Automatizar las queries de calidad (Bloque 3) y alertar si superan umbrales |

---

### Nivel 3 — Largo Plazo (9-24 meses)

| Iniciativa | Impacto | Esfuerzo | Descripción |
|------------|---------|---------|-------------|
| **Self-Service Analytics** | Alto | Alto | Plataforma de BI para que los equipos internos creen sus propios reportes |
| **Embedded Analytics** | Alto | Muy alto | Dashboards de métricas de uso embebidos en el producto para los instructores |
| **Predicción de churn** | Muy alto | Alto | Modelo ML que detecte instituciones o cursos en riesgo de abandono |
| **Recomendaciones de uso** | Alto | Alto | Sugerir materiales o técnicas de anotación basados en patrones de uso |
| **IA Conversacional** | Medio | Muy alto | Chatbot que permita a instructores hacer preguntas en lenguaje natural sobre el uso de sus cursos |
| **Alertas de engagement** | Alto | Medio | Notificar a instructores cuando un estudiante tiene baja actividad |

---

## Apéndice — Próximos pasos para completar el assessment

Una vez que se tenga acceso a base de datos, ejecutar las siguientes queries en orden:

1. **Volumen general** (Sección 2.5) — entender el tamaño del sistema
2. **Completitud** (Sección 3.1) — identificar campos críticos vacíos
3. **Duplicados** (Sección 3.2) — medir la confiabilidad de identidades
4. **Consistencia** (Sección 3.3) — validar reglas de negocio
5. **Integridad referencial** (Sección 3.4) — detectar registros huérfanos
6. **Frecuencia de eventos** (Sección 4.4) — entender los patrones de uso

Con esos resultados, completar las columnas "Registros" y "Crecimiento" del inventario de tablas (Sección 2.2 y 2.3) y ajustar el roadmap según la criticidad de los problemas encontrados.

# Hypothesis Platform — Data Assessment v3
**Fecha:** 2026-05-23
**Versión:** 3.0
**Autor:** Data Engineering
**Estado:** Fase 1 — Assessment desde código fuente (sin acceso a BD)

---

## Resumen Ejecutivo

Hypothesis es una plataforma B2B SaaS de anotaciones colaborativas que vende a universidades e instituciones educativas. El producto se integra con los principales sistemas de gestión de aprendizaje (LMS) y permite a estudiantes y profesores anotar PDFs, videos, páginas web y material de estudio.

Este documento consolida el assessment completo de la plataforma desde sus repositorios de código fuente (`h`, `lms`, `client`). Las secciones que requieren acceso adicional están marcadas: `[REQUIERE BD]`, `[REQUIERE ENTREVISTA]`, `[REQUIERE ACCESO]`.

**Hallazgo central:** Hypothesis posee una arquitectura técnica robusta y acumula una cantidad significativa de datos operacionales, pero carece de una estrategia formal de analítica de producto y gobierno de datos. La principal oportunidad no está en generar más datos, sino en capturar, gobernar y transformar los datos existentes en información accionable para Product, Customer Success y Revenue Operations.

---

## Estado Actual

| Área | Estado | Descripción |
|------|--------|-------------|
| Infraestructura | 🟢 Sólida | AWS multi-región, PostgreSQL, Elasticsearch, RabbitMQ en producción |
| Integraciones | 🟢 Sólidas | Canvas, Blackboard, D2L, Moodle, JSTOR, VitalSource, YouTube, HubSpot |
| Modelo de datos | 🟢 Maduro | 61 tablas, 174+134 migraciones, esquema bien normalizado |
| Analytics | 🟡 Parcial | Solo métricas LTI (launches, grades). Sin engagement real |
| Tracking | 🔴 Deficiente | Analytics service sin implementar. Sin sesiones, sin apertura de recursos |
| Data Quality | ⚪ Desconocido | Sin acceso a BD. Queries provistas para evaluación |
| Data Governance | 🔴 Inexistente | Sin data catalog, sin ownership formal, sin definiciones compartidas |
| Revenue Analytics | 🔴 Inexistente | Datos de contratos y billing fuera del sistema (HubSpot/externo) |
| Product Analytics | 🔴 Inexistente | No hay una capa de analytics de producto construida |

**Conclusión:**
Hypothesis posee una arquitectura robusta y una gran cantidad de datos operacionales, pero carece de una estrategia formal de analítica de producto y gobierno de datos. El Board hoy no puede responder con datos propios preguntas básicas como "¿cuánto tiempo usan Hypothesis nuestros estudiantes?" o "¿qué instituciones están en riesgo de no renovar?".

---

## Data Maturity Assessment

Evaluación del nivel de madurez de datos por dominio (escala 1–5):

| Dominio | Nivel | Descripción |
|---------|-------|-------------|
| Data Collection | 2 / 5 | Se colectan datos operacionales pero faltan eventos de comportamiento |
| Data Quality | 2 / 5 | Sin validaciones automatizadas ni procesos de limpieza formales |
| Data Governance | 1 / 5 | Sin ownership formal, sin catalog, sin glosario de términos |
| Analytics | 2 / 5 | Algunas métricas de uso disponibles en dashboard LMS, sin capa analítica central |
| Product Analytics | 1 / 5 | Analytics service existe en código pero no está implementado |
| Self-Service Analytics | 1 / 5 | No existe. Todo análisis requiere acceso directo a BD |
| AI / ML Readiness | 2 / 5 | Datos existen pero no están curados ni centralizados para modelado |

**Madurez global estimada: 1.6 / 5**

> Este nivel de madurez es esperable para una compañía en etapa de crecimiento que priorizó infraestructura operacional sobre infraestructura analítica. El roadmap de este assessment está diseñado para llevarlo a 3.5/5 en 18 meses.

---

## Bloque 0 — Entendimiento del Negocio

### 0.1 Business Model Canvas

| Dimensión | Descripción |
|-----------|-------------|
| **Clientes** | Universidades, colleges e instituciones educativas de nivel superior |
| **Usuarios finales** | Estudiantes (anotan, responden, colaboran) y profesores (configuran, revisan, califican) |
| **Compradores** | CIO, Academic Technology Officers, LMS Administrators, Decanos |
| **Propuesta de valor** | Anotación colaborativa digital sobre cualquier recurso educativo. Fomenta lectura activa, participación y aprendizaje profundo. Se integra transparentemente con el LMS existente |
| **Canales** | Integración LTI directa con LMS (Canvas, Blackboard, D2L, Moodle) + web directo |
| **Relación con clientes** | Contrato institucional anual, onboarding, soporte técnico, Customer Success |
| **Fuentes de ingreso** | `[REQUIERE ENTREVISTA]` — presumiblemente licencias por cantidad de estudiantes o por institución |
| **Recursos clave** | Plataforma de anotación (h), integración LMS (lms), cliente JS (client), equipo de CS |
| **Actividades clave** | Mantener integraciones LMS actualizadas, onboarding de instituciones, soporte técnico, desarrollo de producto |
| **Socios clave** | Proveedores de LMS (Instructure/Canvas, Anthology/Blackboard, D2L, Moodle), proveedores de contenido (JSTOR, VitalSource) |
| **Estructura de costos** | Infraestructura AWS, equipo de ingeniería, equipo de CS, integraciones de contenido |

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
| **Retención semestral** | % de cursos/instituciones que continúan el semestre siguiente | `lms_course` + `lms_term` (lms) |
| **Renewal Rate** | % de contratos renovados | ❌ HubSpot / billing externo |

---

### 0.4 KPIs por área

| Área | KPI | Calculable hoy |
|------|-----|---------------|
| **Product** | Monthly Active Users (MAU) | ⚠️ Parcial |
| | Daily Active Users (DAU) | ⚠️ Parcial |
| | Retención 30/60/90 días | ⚠️ Parcial |
| | Annotation Rate por curso | ✅ Sí |
| **Customer Success** | Health Score por institución | ⚠️ Proxy solamente |
| | Adoption Score (cursos activos / contratados) | ❌ Falta dato de contratos |
| | Churn Risk Score | ⚠️ Proxy desde `last_launched` |
| **Sales** | ARR (Annual Recurring Revenue) | ❌ No en BDs |
| | Renewal Rate | ❌ No en BDs |
| | Expansion Revenue (nuevos cursos en cliente existente) | ⚠️ Parcial |
| **Engineering** | Availability (uptime) | ❌ New Relic / externo |
| | Error Rate | ❌ Sentry / externo |
| | Response Time | ❌ New Relic / externo |
| **Education** | Annotation Density (anotaciones por recurso) | ✅ Sí |
| | Student Participation Rate (% activos en un curso) | ✅ Sí |
| | Collaboration Index (replies / anotaciones) | ✅ Sí |

---

### 0.5 Customer Journey

#### Journey del Instructor

```
[1] Accede al LMS        → [2] Configura asignación   → [3] Publica recurso
       ↓                           ↓                            ↓
    LTI config               deep_linking event            document_url en BD

[4] Estudiantes ingresan → [5] Se generan anotaciones  → [6] Revisa actividad
       ↓                           ↓                            ↓
  configured_launch          annotation en h             dashboard LMS

[7] Califica
       ↓
  grading_sync_grade
```

#### Journey del Estudiante

```
[1] Launch desde LMS     → [2] Abre recurso            → [3] Lee contenido
       ↓                           ↓                            ↓
  configured_launch         ❌ No trackeado              ❌ No trackeado

[4] Anota               → [5] Responde                 → [6] Recibe feedback
       ↓                           ↓                            ↓
  annotation en h         annotation.references          notification
```

#### Cobertura del journey por paso

| Paso | Measurable hoy | Cómo |
|------|---------------|------|
| Launch desde LMS | ✅ Sí | `event.configured_launch` (lms) |
| Configura asignación | ✅ Sí | `event.deep_linking` / `event.edited_assignment` (lms) |
| Abre recurso | ❌ No | No implementado |
| Lee contenido | ❌ No | No implementado (requiere scroll/time tracking) |
| Crea anotación | ⚠️ Parcial | `annotation` table — no hay evento explícito |
| Responde a anotación | ⚠️ Parcial | `annotation.references` — inferido |
| Menciona usuario | ✅ Sí | `mention` table (h) |
| Recibe notificación | ✅ Sí | `notification` table (h y lms) |
| Revisa actividad (instructor) | ⚠️ Parcial | Dashboard LMS — sin detalle de qué vio |
| Calificación enviada | ✅ Sí | `grading_sync_grade` (lms) |

> **El journey revela que los pasos de mayor valor (apertura de recurso, lectura, engagement real) son los menos medibles.** Esto explica por qué es imposible hoy demostrar cuánto "usa" un estudiante Hypothesis.

---

### 0.6 Preguntas que debería poder responder el Board

**Adopción:**
- ¿Qué universidades usan más el producto? ¿Cuántos cursos activos tiene cada una?
- ¿Qué LMS tiene mayor tasa de adopción?
- ¿Cuántos estudiantes usan activamente Hypothesis en el semestre actual?

**Engagement:**
- ¿Qué recursos generan más anotaciones?
- ¿Cuántas anotaciones promedio hace un estudiante activo?
- ¿Cuál es la profundidad promedio de las conversaciones?

**Retención y riesgo:**
- ¿Qué instituciones están en riesgo de churn?
- ¿Qué instituciones están creciendo en uso?

**Negocio:**
- ¿Cuánto revenue está asociado a cada nivel de uso?
- ¿Qué instituciones tienen contratos próximos a vencer?

---

## Bloque 1 — Arquitectura

### 1.1 Repositorios

| Repositorio | Función | Tecnología | Base de datos | Responsable |
|-------------|---------|-----------|---------------|-------------|
| `hypothesis/h` | Backend central: API REST de anotaciones, autenticación, grupos, búsqueda, panel admin | Python 3.11 + Pyramid, Celery, Gunicorn | PostgreSQL + Elasticsearch | Backend team |
| `hypothesis/lms` | Integración con LMS educativos vía LTI 1.1/1.3 | Python 3.11 + Pyramid, Celery, Gunicorn | PostgreSQL separada | LMS/EdTech team |
| `hypothesis/client` | Cliente JavaScript inyectable; permite anotar HTML, PDFs, videos | TypeScript + Preact + Redux, Rollup | Sin BD propia | Frontend team |

- **¿Existen microservicios?** No. Arquitectura monolítica por repo (Pyramid WSGI)
- **¿Existen procesos batch?** Sí: Celery workers en `h` (indexación, emails) y `lms` (digests, calificaciones, HubSpot)
- **¿Existen ETL?** No hay ETL dedicado. La sincronización se hace vía H Bulk API y Celery tasks

---

### 1.2 Infraestructura

```
┌─────────────────────────────────────────────────────────────┐
│                    AWS (us-west-1 + ca-central-1)           │
│                                                             │
│  ┌──────────────────┐    ┌──────────────────────────────┐  │
│  │ ElasticBeanstalk │    │    ElasticBeanstalk           │  │
│  │   h (web)        │    │    h-websocket               │  │
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
└─────────────────────────────────────────────────────────────┘
```

---

### 1.3 Integraciones Externas

| Sistema | Tipo | Dirección | Datos intercambiados |
|---------|------|-----------|---------------------|
| **Canvas** | LMS | Bidireccional | Usuarios, cursos, archivos, calificaciones |
| **Blackboard** | LMS | Bidireccional | Usuarios, cursos, archivos, calificaciones |
| **D2L** | LMS | Bidireccional | Usuarios, cursos, archivos, calificaciones |
| **Moodle** | LMS | Bidireccional | Usuarios, cursos, archivos, páginas |
| **Canvas Studio** | Media | Entrada | Videos, colecciones de media |
| **JSTOR** | Contenido | Entrada | Artículos académicos, thumbnails |
| **VitalSource** | Contenido | Entrada | Libros, TOC, URLs de lanzamiento |
| **YouTube** | Contenido | Entrada | Metadata de videos |
| **Google Drive / OneDrive** | Almacenamiento | Entrada | File picker para asignaciones |
| **HubSpot** | CRM | Salida | Organizaciones, datos de facturación (Celery task diaria) |
| **Mailchimp** | Email Marketing | Salida | Acciones de usuarios |
| **Sentry** | Error tracking | Salida | Errores frontend y backend |
| **New Relic** | APM | Salida | Métricas de performance |
| **Google Analytics** | Analytics | Salida | Eventos de página (uso no confirmado) |
| **ORCID / Google / Facebook** | Auth | Entrada | Identidades de usuario via OIDC |

---

### 1.4 Flujo de datos entre sistemas

```
                          UNIVERSIDAD
                              │ (LTI Launch)
                              ▼
┌─────────────────────────────────────────────────┐
│                      LMS                        │
│  1. Autentica usuario via LTI 1.1/1.3           │
│  2. Registra Event(configured_launch)            │
│  3. Sincroniza grupos con H                      │
│  4. Devuelve token JWT al client                 │
└───────────────────┬─────────────────────────────┘
                    │                 │
             H Bulk API          JWT Token
                    │                 │
                    ▼                 ▼
┌───────────────────────┐   ┌──────────────────────────────┐
│          H            │   │          CLIENT              │
│  Recibe anotaciones   │◄──│  Inyectado en la página      │
│  Indexa Elasticsearch │──►│  Permite anotar PDFs, videos │
│  Publica a RabbitMQ   │   └──────────────────────────────┘
└──────────┬────────────┘
           │ RabbitMQ
           ▼
┌──────────────────────────────────────────────────┐
│                 LMS (Celery workers)             │
│  Procesa eventos, emails, calificaciones, HubSpot│
└──────────────────────────────────────────────────┘
```

---

## Revenue Data Assessment

> **Un assessment de uso sin datos de negocio es incompleto para el Board.**

### ¿Dónde están los datos de monetización?

| Dato | Encontrado en código | Ubicación probable |
|------|--------------------|--------------------|
| Clientes / Universidades | ✅ Parcial | `organization` + `application_instances` (lms) |
| Contratos y renovaciones | ❌ | HubSpot (integración activa en código) |
| Licencias y pricing | ❌ | HubSpot / billing externo |
| Facturación / Revenue | ❌ | Billing externo (Stripe, Chargebee, manual) |
| Churn real | ❌ | Inferible desde `application_instances.last_launched` |

### Proxy de salud por institución `[REQUIERE BD]`

```sql
SELECT
    o.name AS institucion,
    ai.tool_consumer_info_product_family_code AS lms,
    ai.last_launched AS ultimo_uso,
    COUNT(DISTINCT lc.id) AS cursos_activos,
    COUNT(DISTINCT lu.id) AS usuarios_unicos,
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
GROUP BY 1, 2, 3
ORDER BY cursos_activos DESC;
```

### Acciones recomendadas

1. **`[REQUIERE ACCESO]` HubSpot**: extraer deals, contratos, fechas de renovación
2. **`[REQUIERE ENTREVISTA]` Finance/Sales**: entender modelo de pricing
3. **`[REQUIERE ENTREVISTA]` Customer Success**: entender proceso de renovación y señales de churn

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

> Hoy no existe un dueño de datos transversal. Los datos de revenue están en Sales/Finance, desconectados de los datos de uso en Engineering. No hay data catalog ni definiciones compartidas.

---

## Evaluación de Riesgos

| # | Riesgo | Severidad | Impacto en negocio | Acción recomendada |
|---|--------|-----------|-------------------|-------------------|
| R1 | **Analytics service no implementado** en `h` (TODO en código) | 🔴 Alto | Pérdida permanente de información de engagement | Implementar en Sprint 1 — endpoint ya existe |
| R2 | **Sin tracking de sesiones** ni tiempo de uso | 🔴 Alto | Imposible demostrar valor real a universidades | Agregar session tracking al client |
| R3 | **Eventos de anotación no persistidos** en h (solo en memoria) | 🔴 Alto | Sin fuente de verdad para actividad histórica | Crear tabla `annotation_event` en h |
| R4 | **LTI params purgados a 30 días** (Celery task automática) | 🟡 Medio | Pérdida de histórico de contexto de launches | Evaluar qué campos preservar antes de la purga |
| R5 | **Datos de revenue fuera del sistema** | 🟡 Medio | No se puede correlacionar uso con ingresos | Construir pipeline HubSpot → DW en Fase 2 |
| R6 | **Dependencia de joins entre h y lms** via `h_userid` | 🟡 Medio | Complejidad analítica alta. Un error rompe todos los análisis | Validar integridad del join (Sección 3.4) |
| R7 | **Elasticsearch 7.10 en EOL** | 🟡 Medio | Riesgo de seguridad a mediano plazo | Planificar upgrade a OpenSearch o ES 8.x |
| R8 | **Sin tipo de recurso normalizado** | 🟢 Bajo | No se puede segmentar uso por tipo de material | Agregar campo `resource_type` en `assignment` |
| R9 | **Dependencia crítica de LMS externos** (Canvas, Blackboard, D2L, Moodle) | 🔴 Alto | Si cualquier LMS cambia su API: launches fallan, sincronización falla, calificaciones fallan. El producto deja de funcionar | Monitoreo activo de cambios de API LMS. Versionar integraciones. Alertas tempranas |

---

## Bloque 2 — Modelo de Datos

### 2.1 Entidades estratégicas del negocio

Estas entidades representan los conceptos clave desde una perspectiva de negocio — son las dimensiones reales de analytics:

| Entidad | Tabla(s) fuente | Sistema | Descripción de negocio |
|---------|----------------|---------|----------------------|
| **Institution** | `organization`, `application_instances` | lms | Universidad o institución cliente. Unidad de contrato y revenue |
| **Student** | `lms_user` (rol learner), `user` (h) | lms + h | Usuario final que anota y colabora |
| **Instructor** | `lms_user` (rol instructor), `user` (h) | lms + h | Usuario que configura asignaciones y evalúa |
| **Course** | `lms_course`, `grouping` | lms | Contexto educativo donde ocurre el uso |
| **Assignment** | `assignment` | lms | Tarea específica que involucra anotar un recurso |
| **Resource** | `assignment.document_url`, `file`, `document` | lms + h | Material educativo que se anota (PDF, video, HTML, libro) |
| **Annotation** | `annotation` | h | Acción central del producto — el valor entregado |
| **Session** | ❌ No existe | — | Período de uso continuo de un usuario. Debe construirse |

---

### 2.2 Entidades técnicas — BD `h`

| Tabla | Descripción | PK | FKs principales |
|-------|-------------|-----|----------------|
| `user` | Usuarios de Hypothesis con perfil, estado y flags (admin, staff, nipsa, deleted) | `id` | `activation_id → activation` |
| `user_identity` | Identidades externas (ORCID, Google, Facebook) | `id` | `user_id → user` |
| `activation` | Tokens de activación de cuenta | `id` | — |
| `authclient` | Clientes OAuth 2.0 registrados | `id (UUID)` | — |
| `authzcode` | Códigos de autorización OAuth | `id` | `user_id`, `authclient_id` |
| `authticket` | Tickets de sesión web | `id` | `user_id → user` |
| `token` | API tokens de acceso y refresh | `id` | `user_id`, `authclient_id` |
| `group` | Grupos de anotación (públicos, privados, institucionales) | `id` | `creator_id → user`, `organization_id → organization` |
| `user_group` | Membresía usuario-grupo con roles en JSONB | `id` | `user_id → user`, `group_id → group` |
| `groupscope` | Alcance de URLs donde aplica el grupo | `id` | `group_id → group` |
| `organization` | Organizaciones (universidades, empresas) | `id` | — |
| `annotation` | **Tabla central.** Anotaciones con texto, tags, selectores, estado de moderación | `id (UUID)` | `document_id → document` |
| `annotation_slim` | Vista desnormalizada para queries rápidas | `id` | `pubid → annotation`, `user_id`, `group_id`, `document_id` |
| `annotation_metadata` | Metadata extendida en JSONB | `annotation_id` | `annotation_id → annotation_slim` |
| `document` | Documento web anotado | `id` | — |
| `document_uri` | URIs concretas de un documento | `id` | `document_id → document` |
| `document_meta` | Metadata del documento (título, autor) | `id` | `document_id → document` |
| `mention` | Menciones `@usuario` dentro de anotaciones | `id` | `annotation_id`, `user_id` |
| `notification` | Notificaciones enviadas (reply, mention) | `id` | `source_annotation_id`, `recipient_id` |
| `flag` | Reportes/flags de anotaciones | `id` | `annotation_id`, `user_id` |
| `moderation_log` | Log de cambios de estado de moderación | `id` | `annotation_id`, `moderator_id` |
| `subscriptions` | Preferencias de notificación | `id` | — |
| `feature` | Feature flags del sistema | `id` | — |
| `featurecohort` | Grupos de usuarios para A/B testing | `id` | — |
| `featurecohort_user` | Relación usuario-cohorte | `id` | `user_id`, `cohort_id` |
| `featurecohort_feature` | Relación cohorte-feature | `id` | `feature_id`, `cohort_id` |
| `job` | Cola de jobs internos | `id` | — |
| `task_done` | Registro de tareas completadas | `id` | — |
| `user_deletion` | Auditoría de borrado de usuarios | `id` | — |
| `blocklist` | URIs bloqueadas | `id` | — |
| `setting` | Key-value settings del sistema | `key` | — |

**Total: 31 tablas**

---

### 2.3 Entidades técnicas — BD `lms`

| Tabla | Descripción | PK | FKs principales |
|-------|-------------|-----|----------------|
| `organization` | Universidad o institución cliente | `id` | `parent_id → organization` |
| `application_instances` | Instalación de Hypothesis en un LMS | `id` | `organization_id`, `lti_registration_id` |
| `lti_registration` | Registro LTI 1.3 | `id` | — |
| `lms_user` | Usuario canónico con `h_userid` para vincular con h | `id` | — |
| `user` | Usuario en el contexto de una instancia | `id` | `application_instance_id` |
| `lms_user_application_instance` | Relación usuarios-instancias | `id` | `lms_user_id`, `application_instance_id` |
| `lms_term` | Período académico con fechas | `id` | — |
| `lms_course` | Curso en el LMS | `id` | `lms_term_id` |
| `lms_course_application_instance` | Relación curso-instancia | `id` | `lms_course_id`, `application_instance_id` |
| `lms_course_membership` | Membresía de usuarios en cursos con rol LTI | `id` | `lms_course_id`, `lms_user_id`, `lti_role_id` |
| `lti_role` | Roles LTI (instructor, learner, admin) | `id` | — |
| `lti_role_override` | Override de roles por instancia | `id` | `lti_role_id`, `application_instance_id` |
| `grouping` | Entidad polimórfica: curso, sección, grupo | `id` | `application_instance_id`, `parent_id → grouping` |
| `grouping_membership` | Membresía de usuarios en groupings | `(grouping_id, user_id)` | `grouping_id`, `user_id` |
| `group_info` | Información legacy de grupos del LMS | `id` | `application_instance_id` |
| `assignment` | Asignación con URL del documento a anotar | `id` | `course_id → grouping`, `auto_grading_config_id` |
| `assignment_auto_grading_config` | Configuración de auto-calificación | `id` | — |
| `assignment_grouping` | Relación asignaciones-groupings | `(assignment_id, grouping_id)` | ambas FKs |
| `file` | Archivo del LMS referenciado en asignación | `id` | `application_instance_id` |
| `grading_sync` | Proceso de sincronización de calificaciones | `id` | `assignment_id`, `created_by_id → lms_user` |
| `grading_sync_grade` | Calificación individual de un estudiante | `id` | `grading_sync_id`, `lms_user_id` |
| `lis_result_sourcedid` | Info de calificación LTI 1.1 (legacy) | `id` | `application_instance_id` |
| `oauth2_token` | Tokens OAuth2 para APIs de LMS | `id` | `application_instance_id` |
| `jwt_oauth2_token` | Tokens JWT para LTI 1.3 | `id` | `lti_registration_id` |
| `rsa_key` | Claves RSA para firma JWT | `id` | — |
| `event` | **Tabla de eventos**: acciones en el sistema LMS | `id` | `type_id`, `application_instance_id`, `course_id`, `assignment_id` |
| `event_type` | Catálogo: configured_launch, deep_linking, grade, audit, error_code | `id` | — |
| `event_user` | Usuarios que participaron en un evento con su rol | `id` | `event_id`, `user_id`, `lti_role_id` |
| `event_data` | Datos extra del evento en JSONB | `event_id` | `event_id → event` |
| `notification` | Notificaciones reply/mention en contexto LMS | `id` | `sender_id`, `recipient_id → lms_user`, `assignment_id` |

**Total: 30 tablas**

---

### 2.4 Relaciones entre BDs

```
lms.lms_user.h_userid  ←→  h.user.userid  (formato: acct:username@authority)
lms.grouping.authority_provided_id  ←→  h.group.authority_provided_id
```

La BD `lms` puede leer la BD `h` directamente via **Foreign Data Wrapper (FDW)** configurado en `H_FDW_DATABASE_URL`.

---

### 2.5 Conteos `[REQUIERE BD]`

```sql
-- Volumen general (BD h)
SELECT relname AS tabla, n_live_tup AS registros_estimados
FROM pg_stat_user_tables ORDER BY n_live_tup DESC;

-- Crecimiento mensual de anotaciones (BD h)
SELECT
  DATE_TRUNC('month', created) AS mes,
  COUNT(*) AS nuevas,
  COUNT(*) FILTER (WHERE shared = true) AS publicas,
  COUNT(DISTINCT userid) AS usuarios_activos
FROM annotation WHERE deleted = false
GROUP BY 1 ORDER BY 1 DESC LIMIT 24;

-- Launches por mes (BD lms)
SELECT DATE_TRUNC('month', e.timestamp) AS mes, et.type, COUNT(*)
FROM event e JOIN event_type et ON e.type_id = et.id
GROUP BY 1, 2 ORDER BY 1 DESC;
```

---

## Bloque 3 — Calidad de Datos

### 3.1 Completitud `[REQUIERE BD]`

```sql
-- Usuarios sin email (BD h)
SELECT
  COUNT(*) AS total,
  COUNT(*) FILTER (WHERE email IS NULL) AS sin_email,
  ROUND(100.0 * COUNT(*) FILTER (WHERE email IS NULL) / COUNT(*), 2) AS pct
FROM "user" WHERE deleted = false;

-- Anotaciones sin target_uri (BD h)
SELECT COUNT(*) FROM annotation WHERE target_uri IS NULL OR target_uri = '';

-- Usuarios LMS sin h_userid (BD lms)
SELECT COUNT(*) FROM lms_user WHERE h_userid IS NULL;

-- Eventos sin usuario asociado (BD lms)
SELECT COUNT(*) FROM event e
LEFT JOIN event_user eu ON eu.event_id = e.id WHERE eu.user_id IS NULL;
```

### 3.2 Duplicados `[REQUIERE BD]`

```sql
-- Emails duplicados por authority (BD h)
SELECT email, authority, COUNT(*) AS n FROM "user"
WHERE email IS NOT NULL AND deleted = false
GROUP BY email, authority HAVING COUNT(*) > 1 ORDER BY n DESC LIMIT 20;

-- h_userid duplicados (BD lms)
SELECT h_userid, COUNT(*) AS n FROM lms_user
GROUP BY h_userid HAVING COUNT(*) > 1;
```

### 3.3 Consistencia `[REQUIERE BD]`

```sql
-- Anotaciones con updated < created (BD h)
SELECT COUNT(*) FROM annotation WHERE updated < created;

-- Calificaciones fuera de rango [0,1] (BD lms)
SELECT COUNT(*) FROM grading_sync_grade WHERE grade < 0 OR grade > 1;

-- Cursos con ends_at < starts_at (BD lms)
SELECT COUNT(*) FROM lms_course
WHERE ends_at IS NOT NULL AND starts_at IS NOT NULL AND ends_at < starts_at;
```

### 3.4 Integridad Referencial `[REQUIERE BD]`

```sql
-- annotation_slim sin annotation padre (BD h)
SELECT COUNT(*) FROM annotation_slim asm
WHERE NOT EXISTS (SELECT 1 FROM annotation a WHERE a.id = asm.pubid);

-- Eventos con application_instance inexistente (BD lms)
SELECT COUNT(*) FROM event e
WHERE application_instance_id IS NOT NULL
  AND NOT EXISTS (SELECT 1 FROM application_instances ai WHERE ai.id = e.application_instance_id);
```

### 3.5 Volumen `[REQUIERE BD]`

```sql
SELECT relname, pg_size_pretty(pg_total_relation_size(relid)) AS tamaño, n_live_tup AS filas
FROM pg_stat_user_tables ORDER BY pg_total_relation_size(relid) DESC LIMIT 20;
```

---

## Bloque 4 — Assessment de Tracking

### 4.1 Eventos existentes

#### BD `lms` — Persistidos en tabla `event`

| Evento | Descripción |
|--------|-------------|
| `configured_launch` | Usuario abre Hypothesis desde el LMS |
| `deep_linking` | Profesor configura una asignación nueva |
| `edited_assignment` | Profesor edita una asignación existente |
| `submission` | Estudiante envía trabajo |
| `grade` | Sistema sincroniza calificación |
| `audit` | Cambios en modelos (audit trail) |
| `error_code` | Error durante una acción LTI |

> LTI params purgados automáticamente a 30 días.

#### BD `h` — En memoria, no persistidos

| Evento | Persistencia | Traza disponible |
|--------|-------------|-----------------|
| `AnnotationEvent (create/update/delete)` | ❌ | Solo en tabla `annotation` |
| `ModeratedAnnotationEvent` | ❌ | Solo en `moderation_log` |
| `LoginEvent / LogoutEvent` | ❌ | Solo en logs |
| `ActivationEvent` | ❌ | Solo en logs |

> **⚠️ Analytics service en `h` marcado como TODO en código. Solo 1 evento se envía desde el client.**

---

### 4.2 Cobertura

| Acción | Trackeado | Dónde |
|--------|-----------|-------|
| Abrir Hypothesis desde LMS | ✅ | `event.configured_launch` |
| Crear anotación | ⚠️ | Solo en tabla `annotation` |
| Responder a anotación | ⚠️ | `annotation.references` (inferido) |
| Mencionar usuario | ✅ | `mention` (h) |
| Calificación sincronizada | ✅ | `grading_sync_grade` (lms) |
| **Abrir PDF / video / recurso** | ❌ | No implementado |
| **Tiempo de uso** | ❌ | No implementado |
| **Búsqueda en sidebar** | ❌ | No implementado |
| **Inicio/fin de sesión** | ❌ | No implementado |

---

### 4.3 Frecuencia `[REQUIERE BD]`

```sql
-- Frecuencia de eventos por tipo y mes (BD lms)
SELECT DATE_TRUNC('month', e.timestamp) AS mes, et.type, COUNT(*),
  COUNT(DISTINCT e.application_instance_id) AS instituciones
FROM event e JOIN event_type et ON et.id = e.type_id
GROUP BY 1, 2 ORDER BY 1 DESC, 3 DESC;

-- Actividad de anotaciones por mes (BD h)
SELECT DATE_TRUNC('month', created) AS mes, COUNT(*) AS anotaciones,
  COUNT(DISTINCT userid) AS usuarios,
  COUNT(*) FILTER (WHERE array_length(references, 1) > 0) AS replies
FROM annotation WHERE deleted = false
GROUP BY 1 ORDER BY 1 DESC LIMIT 24;
```

---

## Bloque 5 — Modelo Analítico Futuro

### 5.1 Arquitectura target

```
┌─────────────────────────────────────────────────────────────────┐
│                        DATA SOURCES                             │
│  H (annotations)  LMS (events/grades)  HubSpot  GA  Billing   │
└─────────────────────────┬───────────────────────────────────────┘
                          │ ingesta (batch / streaming)
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                        RAW LAYER                                │
│  Réplica fiel de datos fuente. Sin transformaciones.            │
│  Herramienta: Airbyte / Fivetran / scripts custom               │
└─────────────────────────┬───────────────────────────────────────┘
                          │ dbt transformations
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                       STAGING LAYER                             │
│  Limpieza, normalización, deduplicación.                        │
│  Unificación de identidades (h_userid join).                    │
│  Normalización de resource_type.                                │
└─────────────────────────┬───────────────────────────────────────┘
                          │ dbt models
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                      BUSINESS LAYER                             │
│  Modelo estrella: DimInstitution, DimUser, DimCourse,           │
│  DimAssignment, DimResource, DimDate                            │
│  FactAnnotations, FactEvents, FactGrades, FactSessions          │
│  Métricas gobernadas: MAS, MAI, AnnotationRate, HealthScore     │
└─────────────────────────┬───────────────────────────────────────┘
                          │
          ┌───────────────┼───────────────────┐
          ▼               ▼                   ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐
│      BI      │  │  Embedded    │  │   ML / AI            │
│  (Metabase / │  │  Analytics   │  │  Churn prediction    │
│   Looker)    │  │  (in-product)│  │  Usage recommendations│
└──────────────┘  └──────────────┘  └──────────────────────┘
```

---

### 5.2 Esquema estrella

#### Dimensiones

| Dimensión | Fuente | Campos clave |
|-----------|--------|-------------|
| `DimDate` | Generada | date_key, year, month, week, is_weekend, academic_term |
| `DimInstitution` | `organization` + `application_instances` | institution_id, name, lms_type, enabled |
| `DimUser` | `lms_user` + `user` (h) | user_id, h_userid, display_name, role, institution_id |
| `DimCourse` | `lms_course` + `lms_term` | course_id, name, institution_id, term_name, starts_at, ends_at |
| `DimAssignment` | `assignment` | assignment_id, title, course_id, resource_type, is_gradable |
| `DimResource` | `file` + `document` | resource_id, type (pdf/video/html/book), url, title |

#### Tablas de hechos

| Fact | Fuente | Factibilidad |
|------|--------|-------------|
| `FactAnnotations` | `annotation` (h) | ✅ Hoy |
| `FactEvents` | `event` + `event_user` (lms) | ✅ Hoy |
| `FactGrades` | `grading_sync_grade` (lms) | ✅ Hoy |
| `FactSessions` | — | ❌ Requiere tracking |

---

### 5.3 Transformaciones necesarias

1. Joinear usuarios: `lms.lms_user.h_userid` → `h.user.userid`
2. Normalizar `resource_type`: parsear `assignment.document_url`
3. Inferir replies: `annotation.references IS NOT NULL`
4. Construir `DimCourse`: joinear `lms_course`, `lms_term`, `lms_course_application_instance`
5. Cruzar anotaciones con cursos: `h.group.authority_provided_id` → `lms.grouping.authority_provided_id`

---

## Bloque 6 — Roadmap

> **Orden: Tracking → Data Layer → Data as a Product.**
> Sin datos de comportamiento, un DW solo organiza información incompleta.

---

### Fase 1 — Tracking (0-3 meses)

**Objetivo: capturar los datos que hoy se pierden.**

| Iniciativa | Impacto negocio | Complejidad | Descripción |
|------------|----------------|-------------|-------------|
| Implementar analytics service en `h` | 🔴 Muy alto | 🟢 Baja | Endpoint ya existe. Crear tabla `analytics_event` y persistir. Días de trabajo |
| Session tracking | 🔴 Muy alto | 🟢 Baja | `session_start` / `session_end` desde el client JS |
| Resource tracking | 🔴 Muy alto | 🟢 Baja | `resource_opened` con `resource_type` al client |
| Annotation events explícitos | 🔴 Alto | 🟢 Baja | Tabla `annotation_event` en h para create/update/delete |
| Normalizar `resource_type` | 🟡 Medio | 🟢 Baja | Campo en tabla `assignment` |

---

### Fase 2 — Data Layer (3-9 meses)

**Objetivo: centralizar y gobernar los datos.**

| Iniciativa | Impacto negocio | Complejidad | Descripción |
|------------|----------------|-------------|-------------|
| Data Warehouse (Redshift/BigQuery) | 🔴 Alto | 🔴 Alta | Modelo estrella de la Sección 5.2 |
| Pipeline de ingesta con dbt | 🔴 Alto | 🟡 Media | Ingesta diaria de h y lms con transformaciones |
| Pipeline HubSpot → DW | 🔴 Muy alto | 🟡 Media | Conectar revenue con uso |
| KPIs gobernados | 🟡 Alto | 🟢 Baja | Definir MAS, MAI, Annotation Rate, HealthScore |
| Data catalog y diccionario | 🟡 Medio | 🟢 Baja | Ownership, definiciones compartidas |
| Alertas de calidad de datos | 🟡 Medio | 🟢 Baja | Automatizar queries del Bloque 3 |

---

### Fase 3 — Data as a Product (9-24 meses)

**Objetivos de negocio:**
- Reducir churn de instituciones
- Mejorar tasa de renovación de contratos
- Incrementar adopción dentro de clientes existentes
- Demostrar ROI a universidades en el momento de renovación

**Habilitadores (en orden de impacto):**

| Iniciativa | Impacto negocio | Complejidad | Resultado esperado |
|------------|----------------|-------------|-------------------|
| Dashboard interno (CS/Sales) | 🔴 Muy alto | 🟡 Media | Health score, churn risk, renovaciones próximas |
| Dashboard para instructores (embedded) | 🔴 Muy alto | 🔴 Alta | Participación por alumno, alumnos en riesgo — dentro del producto |
| Dashboard institucional (clientes) | 🔴 Muy alto | 🔴 Alta | ROI visible para el comprador. Arma la renovación |
| Benchmarking | 🟡 Alto | 🟡 Media | "Tu institución genera X% más anotaciones que el promedio" |
| Predicción de churn | 🔴 Muy alto | 🔴 Alta | Detectar riesgo antes de la renovación |
| Self-Service Analytics | 🟡 Medio | 🔴 Alta | BI para equipos internos |
| IA Conversacional | 🟢 Medio | 🔴 Muy alta | Preguntas en lenguaje natural sobre cursos |

---

## Oportunidades de Producto Basadas en Datos

### Para universidades (compradores)
- **Dashboard institucional**: estudiantes activos, cursos con Hypothesis, evolución semestral, comparación YoY
- **Reporte de valor automático**: PDF generado en el momento de renovación con el impacto del año
- **Benchmarking**: "Su universidad vs el promedio de la plataforma"

### Para instructores (usuarios power)
- **Dashboard de curso**: participación por alumno, alumnos sin actividad, recursos más anotados, evolución semanal
- **Alerta temprana**: "3 estudiantes no han abierto Hypothesis en 7 días"
- **Digest semanal**: resumen automático de actividad del curso

### Para el equipo interno
- **Health Score por cliente**: adopción + engagement + tendencia → priorización de CS
- **Churn Risk Score**: clientes con baja actividad vs su historial + fecha de renovación
- **Pipeline de expansión**: clientes con margen para crecer (usan 1 LMS, tienen más disponibles)

### Para el producto
- **A/B testing**: usar `featurecohort` existente para medir impacto real de cambios
- **Feature adoption**: qué features se usan, cuáles no se usan y deberían promocionarse
- **Recomendaciones**: "Los PDFs generan 3x más anotaciones que los videos en tu plataforma"

---

## ¿Qué NO sabemos todavía?

### Requiere acceso a base de datos `[REQUIERE BD]`

| Información | Por qué importa |
|-------------|----------------|
| Volumen real de registros | Dimensionar soluciones y detectar anomalías |
| Crecimiento mensual histórico | Proyectar capacidad del DW |
| Cardinalidad de campos JSONB | Entender metadata no estructurada |
| Distribución real de tipos de eventos | Validar hipótesis de uso |
| Tasa real de nulos en campos críticos | Evaluar riesgo de calidad antes del DW |
| Usuarios activos reales (30/90/180 días) | Baseline para North Star Metrics |

### Requiere entrevistas `[REQUIERE ENTREVISTA]`

| Información | Con quién |
|-------------|----------|
| Modelo de pricing | Finance / CEO |
| Proceso de renovación y señales de churn | Customer Success |
| Qué métricas usa Sales para cerrar contratos | Sales |
| Qué métricas piden los clientes | Customer Success / Account Managers |
| Roadmap de producto | Product Manager |
| OKRs del año | CEO / CTO |
| Ownership real de dominios | Tech Leads |

### Requiere acceso a herramientas externas `[REQUIERE ACCESO]`

| Herramienta | Datos buscados |
|-------------|---------------|
| **HubSpot** | Contratos, deals, renovaciones, pipeline |
| **Google Analytics** | Confirmar si está activo y qué eventos captura |
| **New Relic** | Performance actual, endpoints más lentos |
| **Sentry** | Errores más frecuentes y su impacto |
| **Sistema de billing** | Facturas, montos, planes por cliente |

---

## Executive Recommendation

Hypothesis posee una base tecnológica sólida y una arquitectura madura para soportar crecimiento. Los tres repositorios están bien estructurados, el modelo de datos es coherente y las integraciones con los principales LMS del mercado están operativas.

Sin embargo, la compañía opera actualmente con visibilidad limitada sobre el comportamiento real de sus usuarios. El analytics service existe en el código pero no está implementado. No hay tracking de sesiones, ni de apertura de recursos, ni de tiempo de uso. Los datos de revenue viven en sistemas externos desconectados de los datos de uso. No existe una capa de gobierno de datos.

**La principal oportunidad identificada no está en generar más datos, sino en capturar los datos que ya se deberían estar generando, y conectarlos con los datos de negocio.**

La prioridad inmediata es implementar tracking de sesiones y eventos de uso antes de invertir en iniciativas de Data Warehouse o Inteligencia Artificial. Un DW construido sobre datos incompletos solo organizará información parcial.

Con una inversión relativamente baja en la Fase 1 (el endpoint de analytics ya existe, la infraestructura está en producción), Hypothesis puede pasar de una madurez de datos de 1.6/5 a más de 3.0/5 en menos de 6 meses, habilitando:
- Demostrar ROI a las universidades en el momento de renovación
- Identificar instituciones en riesgo de churn antes de que ocurra
- Dar a los instructores visibilidad sobre el engagement de sus estudiantes

Estas capacidades no son mejoras incrementales al producto. Son habilitadores directos de retención de clientes y crecimiento de revenue.

---

## Apéndice — Próximos pasos

1. **Acceso a BD**: ejecutar queries de los Bloques 2.5, 3.1–3.5 y 4.3
2. **Acceso a HubSpot**: completar Revenue Data Assessment
3. **Entrevistas**: Finance, Sales, CS, Product, CEO — completar Bloque 0 y ¿Qué no sabemos?
4. **Sprint 1**: implementar analytics service en `h` (endpoint ya existe)
5. **Sprint 2**: session tracking + resource tracking en client
6. **Sprint 3**: tabla `annotation_event` en h
7. **Q3**: Data Warehouse + pipeline dbt
8. **Q4**: Dashboard interno para CS/Sales

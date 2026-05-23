# Hypothesis Platform — Data Assessment v4
**Fecha:** 2026-05-23 | **Versión:** 4.0 | **Autor:** Data Engineering

---

## Data Vision Statement

> *El objetivo de la estrategia de datos de Hypothesis no es únicamente medir uso, sino transformar la plataforma en la única herramienta de aprendizaje digital capaz de demostrar impacto educativo y valor institucional de forma cuantificable — convirtiendo analytics en diferencial comercial y motor de retención.*

---

## Resumen Ejecutivo

Hypothesis es una plataforma B2B SaaS de anotaciones colaborativas para universidades. Se integra con los principales LMS (Canvas, Blackboard, D2L, Moodle) y permite a estudiantes y profesores anotar cualquier material educativo digital.

**Hallazgo central:** La compañía posee una arquitectura técnica madura y acumula datos operacionales significativos, pero hoy no puede responder las preguntas más básicas que determinan retención de clientes: *¿cuánto usan Hypothesis los estudiantes? ¿qué instituciones están en riesgo de no renovar?* Esta brecha no es un problema técnico — es un riesgo de revenue.

**Oportunidad identificada:** Con una inversión relativamente baja en tracking e infraestructura analítica (Fase 1 puede ejecutarse en 1-2 meses con 1 ingeniero), Hypothesis puede pasar de operar a ciegas a tener visibilidad completa sobre adopción, engagement y riesgo de churn — habilitando decisiones de retención y upsell que impactan directamente el ARR.

**Prioridad inmediata:** Implementar el analytics service que ya existe en el código antes de cualquier otra inversión en datos.

---

## Estado Actual

| Área | Estado | Descripción |
|------|--------|-------------|
| Infraestructura | 🟢 Sólida | AWS multi-región, PostgreSQL, Elasticsearch, RabbitMQ en producción |
| Integraciones | 🟢 Sólidas | Canvas, Blackboard, D2L, Moodle, JSTOR, VitalSource, YouTube, HubSpot |
| Modelo de datos | 🟢 Maduro | 61 tablas, 174+134 migraciones, esquema bien normalizado |
| Analytics | 🟡 Parcial | Solo métricas LTI (launches, grades). Sin engagement real |
| Tracking | 🔴 Deficiente | Analytics service sin implementar. Sin sesiones ni apertura de recursos |
| Data Quality | ⚪ Desconocido | Sin acceso a BD. Queries provistas para evaluación |
| Data Governance | 🔴 Inexistente | Sin data catalog, sin ownership formal, sin definiciones compartidas |
| Revenue Analytics | 🔴 Inexistente | Datos de contratos y billing desconectados de datos de uso |
| Product Analytics | 🔴 Inexistente | No existe una capa de analytics de producto |

**Madurez global estimada: 1.6 / 5.** El roadmap de este documento está diseñado para llevarla a 3.5/5 en 18 meses.

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
| **Implementar analytics endpoint en `h`** | 2-3 días (endpoint ya existe, solo falta la tabla) | Persistencia de eventos del client | Base de todo analytics futuro |
| **Session tracking en client** | 3-5 días | Primera métrica de engagement real (tiempo de uso) | CS puede ver cuánto usa cada institución |
| **Resource tracking (PDF/video/HTML)** | 2-3 días | Saber qué tipo de recurso genera más anotaciones | Product puede priorizar por tipo de contenido |
| **Dashboard de adopción básico** | 1 semana (datos de `lms.event` ya existen) | Vista de launches por institución, cursos activos, tendencia | CS tiene visibilidad sin acceso a BD |
| **Ejecutar queries de calidad de datos** | 1-2 días | Primer baseline de calidad | Identifica riesgos antes de construir el DW |
| **Entrevistas a CS/Sales/Finance** | 1 semana | Revenue model confirmado, KPIs validados | Completa el Bloque 0 y Revenue Assessment |

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

**Proxy de salud por institución** `[REQUIERE BD]`:
```sql
SELECT
    o.name AS institucion,
    ai.tool_consumer_info_product_family_code AS lms,
    ai.last_launched,
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
GROUP BY 1, 2, 3 ORDER BY cursos_activos DESC;
```

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
| R1 | Analytics service no implementado (`TODO` en código) | 🔴 Alto | Pérdida permanente de información de engagement | Sprint 1 — endpoint ya existe |
| R2 | Sin tracking de sesiones ni tiempo de uso | 🔴 Alto | No se puede demostrar valor a universidades | Session tracking en client |
| R3 | Eventos de anotación no persistidos en h | 🔴 Alto | Sin fuente de verdad para actividad histórica | Tabla `annotation_event` en h |
| R4 | LTI params purgados a 30 días | 🟡 Medio | Pérdida de histórico de contexto | Evaluar qué preservar antes de purga |
| R5 | Datos de revenue fuera del sistema | 🟡 Medio | No se puede correlacionar uso con ingresos | Pipeline HubSpot → DW |
| R6 | Dependencia de joins h ↔ lms via `h_userid` | 🟡 Medio | Complejidad analítica. Un error rompe todos los análisis | Validar integridad (Sección 3.4) |
| R7 | Elasticsearch 7.10 en EOL | 🟡 Medio | Riesgo de seguridad a mediano plazo | Planificar upgrade |
| R8 | Sin tipo de recurso normalizado | 🟢 Bajo | No se puede segmentar uso por tipo de material | Campo `resource_type` en `assignment` |
| R9 | **Dependencia crítica de LMS externos** (Canvas, Blackboard, D2L, Moodle) | 🔴 Alto | Si cualquier LMS cambia su API: launches fallan, sync falla, calificaciones fallan. El producto deja de funcionar | Monitoreo activo de changelogs de APIs LMS. Versionado de integraciones. Alertas tempranas ante breaking changes |

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

### 2.5 Conteos `[REQUIERE BD]`

```sql
-- Volumen general (BD h)
SELECT relname, n_live_tup FROM pg_stat_user_tables ORDER BY n_live_tup DESC;

-- Crecimiento mensual de anotaciones
SELECT DATE_TRUNC('month', created) AS mes, COUNT(*),
  COUNT(DISTINCT userid) AS usuarios_activos
FROM annotation WHERE deleted = false GROUP BY 1 ORDER BY 1 DESC LIMIT 24;

-- Launches por mes (BD lms)
SELECT DATE_TRUNC('month', e.timestamp) AS mes, et.type, COUNT(*)
FROM event e JOIN event_type et ON e.type_id = et.id GROUP BY 1, 2 ORDER BY 1 DESC;
```

---

## Bloque 3 — Calidad de Datos

### 3.1 Completitud `[REQUIERE BD]`

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

### 3.2 Duplicados `[REQUIERE BD]`

```sql
-- Emails duplicados por authority (BD h)
SELECT email, authority, COUNT(*) AS n FROM "user"
WHERE email IS NOT NULL AND deleted = false
GROUP BY email, authority HAVING COUNT(*) > 1 ORDER BY n DESC LIMIT 20;

-- h_userid duplicados (BD lms)
SELECT h_userid, COUNT(*) FROM lms_user GROUP BY 1 HAVING COUNT(*) > 1;
```

### 3.3 Consistencia `[REQUIERE BD]`

```sql
SELECT COUNT(*) FROM annotation WHERE updated < created; -- Fechas invertidas (BD h)
SELECT COUNT(*) FROM grading_sync_grade WHERE grade < 0 OR grade > 1; -- Notas inválidas (BD lms)
SELECT COUNT(*) FROM lms_course WHERE ends_at < starts_at; -- Fechas de curso inválidas (BD lms)
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
SELECT relname, pg_size_pretty(pg_total_relation_size(relid)) AS tamaño, n_live_tup
FROM pg_stat_user_tables ORDER BY pg_total_relation_size(relid) DESC LIMIT 20;
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

> LTI params purgados a 30 días automáticamente.

#### BD `h` — En memoria, no persistidos

| Evento | Traza disponible |
|--------|-----------------|
| `AnnotationEvent (create/update/delete)` | Solo tabla `annotation` |
| `ModeratedAnnotationEvent` | Solo `moderation_log` |
| `LoginEvent / LogoutEvent / ActivationEvent` | Solo logs, no persistidos |

> **⚠️ Analytics service marcado como TODO. Solo 1 evento se envía desde el client.**

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

### 4.3 Frecuencia `[REQUIERE BD]`

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

## Bloque 5 — Modelo Analítico Futuro

### 5.1 Arquitectura target

```
┌──────────────────────────────────────────────────────────────────┐
│                         DATA SOURCES                             │
│   H (annotations) · LMS (events/grades) · HubSpot · GA · Billing│
└─────────────────────────────┬────────────────────────────────────┘
                              │ ingesta (batch diaria / streaming)
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                          RAW LAYER                               │
│   Réplica fiel. Sin transformaciones. Herramienta: Airbyte/custom│
└─────────────────────────────┬────────────────────────────────────┘
                              │ dbt transformations
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                        STAGING LAYER                             │
│   Limpieza · normalización · deduplicación                       │
│   Join h_userid: lms.lms_user ↔ h.user                          │
│   Normalización resource_type (PDF/video/HTML/book)              │
└─────────────────────────────┬────────────────────────────────────┘
                              │ dbt models
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                       BUSINESS LAYER                             │
│   DimInstitution · DimUser · DimCourse · DimAssignment           │
│   DimResource · DimDate                                          │
│   FactAnnotations · FactEvents · FactGrades · FactSessions       │
│   Métricas gobernadas: MAS, MAI, AnnotationRate, HealthScore     │
└──────────────────────────────┬───────────────────────────────────┘
                               │
          ┌────────────────────┼─────────────────────┐
          ▼                    ▼                      ▼
  ┌──────────────┐    ┌────────────────┐    ┌─────────────────────┐
  │      BI      │    │    Embedded    │    │     ML / AI         │
  │  (Metabase / │    │   Analytics    │    │ Churn prediction    │
  │    Looker)   │    │  (in-product)  │    │ Usage recs          │
  └──────────────┘    └────────────────┘    └─────────────────────┘
```

---

### 5.2 Esquema estrella

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
| `FactSessions` | Hecho | — | ❌ Requiere Fase 1 |

---

## Bloque 6 — Roadmap

> **Orden: Tracking → Data Layer → Data as a Product.** Sin datos de comportamiento, un DW organiza información incompleta.

---

### Fase 1 — Tracking (0-3 meses)

**Objetivo:** Capturar los datos que hoy se pierden.
**Equipo:** 1 Data Engineer + 1 Frontend Engineer. **Costo estimado:** 1-2 meses de trabajo.

| Iniciativa | Impacto en revenue | Complejidad | Outcome esperado |
|------------|-------------------|-------------|-----------------|
| Implementar analytics endpoint en `h` | 🔴 Fundacional | 🟢 Baja | Base de todo analytics futuro. El endpoint ya existe |
| Session tracking en client | 🔴 Tiempo de uso → mejora renovaciones | 🟢 Baja | Primera métrica de engagement real |
| Resource tracking (PDF/video/HTML) | 🔴 Segmentación por contenido | 🟢 Baja | Product puede priorizar inversión por tipo |
| Annotation events explícitos en h | 🟡 Actividad histórica reconstruible | 🟢 Baja | Fuente de verdad para analytics de anotaciones |
| Normalizar `resource_type` en `assignment` | 🟡 Segmentación | 🟢 Baja | Dato estructurado en lugar de parsing de URL |

---

### Fase 2 — Data Layer (3-9 meses)

**Objetivo:** Centralizar y gobernar los datos.
**Equipo:** 2 Data Engineers. **Costo estimado:** 3-4 meses de trabajo.

| Iniciativa | Impacto en revenue | Complejidad | Outcome esperado |
|------------|-------------------|-------------|-----------------|
| Data Warehouse (Redshift/BigQuery) | 🔴 Habilita toda la Fase 3 | 🔴 Alta | Single source of truth para el negocio |
| Pipeline de ingesta con dbt | 🔴 Datos confiables y actualizados | 🟡 Media | Modelo estrella operativo con datos frescos |
| Pipeline HubSpot → DW | 🔴 **Revenue + uso en un solo lugar** | 🟡 Media | CS puede ver churn risk + valor contractual juntos |
| KPIs gobernados y glosario | 🟡 Alineación organizacional | 🟢 Baja | "Usuario activo" tiene una sola definición |
| Alertas de calidad de datos | 🟡 Confiabilidad | 🟢 Baja | Detección temprana de degradación de datos |

---

### Fase 3 — Data as a Product (9-24 meses)

**Objetivo:** Reducir churn, mejorar renovaciones, demostrar ROI a universidades, incrementar adopción.
**Equipo:** Squad dedicada (2 DE + 1 Data Analyst + 1 PM). **Costo estimado:** 6-12 meses.

| Iniciativa | Impacto en revenue | Complejidad | Outcome esperado |
|------------|-------------------|-------------|-----------------|
| Dashboard interno CS/Sales | 🔴 Reducir churn por detección temprana | 🟡 Media | CS prioriza cuentas en riesgo antes de la renovación |
| Dashboard institucional (clientes) | 🔴 **Arma la conversación de renovación** | 🔴 Alta | El comprador ve ROI. Tasa de renovación mejora |
| Dashboard para instructores (embedded) | 🔴 Stickiness del producto | 🔴 Alta | Instruc. ven engagement de sus alumnos — NPS sube |
| Predicción de churn | 🔴 Retención proactiva | 🔴 Alta | Salvar cuentas antes de que decidan no renovar |
| Benchmarking por institución | 🟡 Upsell / expansión | 🟡 Media | "Tu universidad está en el top 20%" — argumento comercial |
| Self-Service Analytics | 🟡 Autonomía interna | 🔴 Alta | Equipos responden sus propias preguntas sin depender de DE |

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

**Para ejecutar la Fase 1:** No se requieren cambios organizacionales. 1 Data Engineer con acceso a los repos es suficiente.

**Para ejecutar la Fase 2:**

| Necesidad | Descripción |
|-----------|-------------|
| **Data Engineering function** | Al menos 2 Data Engineers dedicados. No pueden ser borrowed time de producto |
| **Data ownership formal** | Cada dominio (Annotations, LMS, Revenue) necesita un dueño técnico responsable |
| **Governance mínima** | Glosario de términos compartido. ¿Qué es "usuario activo"? ¿Qué es "institución activa"? |
| **Acceso unificado a datos** | DE necesita acceso de lectura a BD h, BD lms y HubSpot |

**Para ejecutar la Fase 3:**

| Necesidad | Descripción |
|-----------|-------------|
| **Alineación Product + CS + Sales** | Las 3 áreas deben acordar qué métricas son oficiales y cómo se calculan |
| **Data PM o Analytics Lead** | Alguien que traduzca necesidades de negocio en especificaciones de datos |
| **Proceso de data governance** | Revisión regular de calidad, ownership y SLAs de datos |
| **Budget para herramientas** | DW (Redshift/BigQuery), herramienta BI (Metabase/Looker), orquestador (Airflow/Dagster) |

---

## ¿Qué NO sabemos todavía?

### Requiere BD `[REQUIERE BD]`

| Información | Por qué importa |
|-------------|----------------|
| Volumen real de registros | Dimensionar soluciones |
| Crecimiento mensual histórico | Proyectar capacidad del DW |
| Cardinalidad de campos JSONB | Entender metadata no estructurada |
| Distribución real de tipos de eventos | Validar hipótesis de uso |
| Usuarios activos reales (30/90/180 días) | Baseline para North Star Metrics |

### Requiere entrevistas `[REQUIERE ENTREVISTA]`

| Información | Con quién |
|-------------|----------|
| Modelo de pricing | Finance / CEO |
| Proceso de renovación y señales de churn | Customer Success |
| Qué métricas usa Sales para cerrar | Sales |
| OKRs del año | CEO / CTO |
| Roadmap de producto | Product Manager |

### Requiere acceso a herramientas `[REQUIERE ACCESO]`

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

El problema es que hoy la compañía no puede responder la pregunta más importante para cualquier conversación de renovación: **¿cuánto valor genera Hypothesis para esta universidad?** No porque los datos no existan — sino porque el analytics service que los capturaría está marcado como TODO en el código.

Esta brecha crea tres riesgos de negocio concretos:

1. **Riesgo de churn no detectado**: Customer Success no puede identificar instituciones en riesgo antes de que el cliente decida no renovar.
2. **Renovaciones sin evidencia**: Sales negocia contratos sin poder mostrar datos de engagement o ROI.
3. **Decisiones de producto a ciegas**: Product no sabe qué features generan adopción y cuáles no.

La buena noticia es que el costo de entrada es bajo. El endpoint de analytics ya existe. La infraestructura AWS ya está corriendo. Con 1-2 meses de trabajo de un ingeniero, Hypothesis puede capturar datos de sesión, apertura de recursos y eventos de anotación — transformando radicalmente la visibilidad sobre el uso real del producto.

**La recomendación es clara:** priorizar Fase 1 (Tracking) antes de cualquier otra inversión en datos. Un Data Warehouse construido hoy sobre datos incompletos solo organizará información parcial. Construirlo después de Fase 1 organizará el comportamiento real de los usuarios.

A mediano plazo, Hypothesis tiene una oportunidad estratégica que la mayoría de sus competidores no pueden replicar: convertir las anotaciones en **Learning Analytics** — métricas de engagement intelectual que demuestran impacto educativo de forma cuantificable. Eso transforma la propuesta de valor de una herramienta de anotación a una plataforma de evidencia de aprendizaje activo, con implicaciones directas en pricing, retención y diferenciación competitiva.

---

## Apéndice — Próximos pasos

**Semana 1-2:**
- Ejecutar queries de Bloques 2.5, 3.1–3.5 y 4.3
- Solicitar acceso a HubSpot
- Agendar entrevistas: Finance, Sales, CS, Product, CEO

**Sprint 1 (semana 3-4):**
- Implementar analytics endpoint en `h` (2-3 días)
- Session tracking en client (3-5 días)
- Resource tracking en client (2-3 días)

**Sprint 2 (mes 2):**
- Tabla `annotation_event` en h
- Dashboard de adopción básico desde `lms.event`
- Campo `resource_type` en `assignment`

**Q3:**
- Data Warehouse + pipeline dbt
- Pipeline HubSpot → DW
- KPIs gobernados

**Q4:**
- Dashboard interno CS/Sales
- Health Score por institución
- Compliance review con Legal

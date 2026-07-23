# Histórico y reconciliación de compromisos

El valor central del skill: no confiar en la memoria. Cada daily aprobado se guarda en SQLite
y, en cada corrida, los compromisos del "Today" anterior se cruzan contra la evidencia real.
Así se detecta lo que se prometió y quedó sin hacer.

## Almacenamiento

`scripts/standup_db.sh` mantiene dos tablas en `~/.daily-standup/history.db`
(override: `$STANDUP_DB` o `$DAILY_STANDUP_HOME`):

- **reports**: `date` (PK), `full_md`, `notes`, `created_at`.
- **commitments**: `id`, `report_date`, `text`, `status` (`open|done|carried|dropped`),
  `resolved_date`, `resolution`.

## Ciclo por daily

1. **Al empezar** — traer lo pendiente:
   ```bash
   scripts/standup_db.sh pending   # compromisos open|carried de dailys anteriores
   scripts/standup_db.sh last 1    # último reporte completo, para contexto
   ```
2. **Cruzar** cada compromiso abierto contra la evidencia del Paso 2 del workflow y clasificar:
   - `done` → hubo evidencia (commit, PR, issue movido, sesión, mensaje, mail) → va en Yesterday.
   - `carried` → sin evidencia y sigue vigente → se repite en Today y se avisa al usuario.
   - `dropped` → ya no aplica → confirmar con el usuario antes de descartar.
3. **Al aprobar** el usuario — persistir:
   ```bash
   scripts/standup_db.sh save <fecha> <archivo_md> ["notas"]
   scripts/standup_db.sh add-commitment <fecha> "<cada bullet de Today>"
   scripts/standup_db.sh resolve <id> done|carried|dropped ["evidencia"]
   ```

## Reglas

- Un compromiso solo pasa a `done` con evidencia concreta citada en `resolution`.
- Registrá **cada** bullet de Today como compromiso: es lo que se auditará mañana.
- No borres compromisos; `dropped` deja la traza de por qué se descartó.
- El `.md` temporal va al scratchpad de la sesión, no al repo.

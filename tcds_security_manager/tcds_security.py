import uuid
from datetime import datetime

class TCDSSecurityManager:
    def __init__(self) -> None:
        self.session_id = str(uuid.uuid4())  # ID anónimo de sesión
        self.state = self._load_state()

    def _audit(self, *, severity: str, reason: str) -> None:
        """
        Registro simple de eventos de seguridad.
        No almacena IP, IMEI ni datos personales.
        Guarda:
          - timestamp
          - session_id
          - severity
          - reason (texto)
          - estado actual (alert/lock)
        """
        event = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "session_id": self.session_id,
            "severity": severity,
            "reason": reason,
            "alert_flag": self.state.alert_flag,
            "lock_permanent": self.state.lock_permanent,
        }
        try:
            with open("tcds_security_audit.log", "a", encoding="utf-8") as f:
                f.write(json.dumps(event) + "\n")
        except Exception:
            # Entornos sin escritura: no rompemos nada
            pass

    def register_event(self, *, severity: str, reason: str) -> None:
        # ... (lo que ya teníamos)
        # al final de la lógica:
        self._audit(severity=severity, reason=reason)
class TCDSSecurityManager:
    def __init__(self, *, origin: str | None = None, region: str | None = None):
        self.session_id = str(uuid.uuid4())
        self.state = self._load_state()
        self.origin = origin or "unknown"
        self.region = region or "unknown"

    def policy_allows_tcds(self) -> bool:
        """Regla de política general, configurable desde el servidor."""
        # Ejemplo: bloquear TCDS en ciertos orígenes/regiones
        blocked_origins = {"kiosko_publico", "demo_anonima"}
        blocked_regions = {"REGION_SENSIBLE_X"}

        if self.origin in blocked_origins:
            return False
        if self.region in blocked_regions:
            return False
        return True

    def guard_tcds_usage(self) -> None:
        """
        Se llama al inicio de cualquier operación TCDS.
        Aplica:
          - bloqueo permanente si existe,
          - política de origen/región.
        """
        if self.state.lock_permanent:
            raise PermissionError(
                "TCDS_LOCK_PERMANENT: El modo TCDS fue deshabilitado "
                "debido a uso malicioso o no autorizado."
            )

        if not self.policy_allows_tcds():
            raise PermissionError(
                "TCDS_POLICY_BLOCK: El modo TCDS no está permitido "
                "para este origen o región. Operar en modo normal."
            )

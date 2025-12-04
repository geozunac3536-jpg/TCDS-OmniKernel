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

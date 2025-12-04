# -*- coding: utf-8 -*-
"""
tcds_omnikernel.tcds_security
-----------------------------

Guardia de seguridad para el modo TCDS.

Implementa:
  - estados de alerta (verde, amarillo, rojo),
  - bloqueo permanente del modo TCDS,
  - verificación antes de usar funciones TCDS,
  - registro básico de auditoría Σ (sin datos personales).

No registra IP, IMEI ni datos sensibles: solo:
  - timestamp
  - session_id (UUID anónimo)
  - severidad
  - motivo
  - estado (alerta/bloqueo)
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import json
import os
import uuid

# Ficheros locales para persistencia
_LOCK_FILE = ".tcds_lock_state.json"
_AUDIT_FILE = "tcds_security_audit.log"


@dataclass
class SecurityState:
    """Estado mínimo del guardia TCDS."""
    alert_flag: bool = False
    lock_permanent: bool = False
    lock_reason: Optional[str] = None


class TCDSSecurityManager:
    """
    Gestor de seguridad para el modo TCDS.

    Uso típico:

        from tcds_omnikernel.tcds_security import TCDSSecurityManager

        sec = TCDSSecurityManager(origin="laboratorio", region="MX")
        sec.guard_tcds_usage()  # al inicio de cualquier flujo TCDS

        # Si se detecta algo dudoso:
        sec.register_event(severity="yellow", reason="Petición ambigua de control sobre terceros.")

        # Si se detecta algo claramente malicioso:
        sec.register_event(severity="red", reason="Intento de usar TCDS para daño físico.")
    """

    def __init__(self, *, origin: str | None = None, region: str | None = None) -> None:
        self.session_id: str = str(uuid.uuid4())  # ID anónimo de sesión
        self.origin: str = origin or "unknown"
        self.region: str = region or "unknown"
        self.state: SecurityState = self._load_state()

    # ------------------------------------------------------------------
    # Carga / guardado de estado
    # ------------------------------------------------------------------
    def _load_state(self) -> SecurityState:
        """
        Intenta leer el estado previo desde disco; si no existe o falla,
        usa valores por defecto (sin bloqueo).
        """
        if os.path.exists(_LOCK_FILE):
            try:
                with open(_LOCK_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return SecurityState(
                    alert_flag=bool(data.get("alert_flag", False)),
                    lock_permanent=bool(data.get("lock_permanent", False)),
                    lock_reason=data.get("lock_reason"),
                )
            except Exception:
                # Si algo va mal leyendo el estado, preferimos un estado limpio.
                return SecurityState()
        return SecurityState()

    def _save_state(self) -> None:
        """Guarda el estado actual en disco (si el entorno lo permite)."""
        data = {
            "alert_flag": self.state.alert_flag,
            "lock_permanent": self.state.lock_permanent,
            "lock_reason": self.state.lock_reason,
        }
        try:
            with open(_LOCK_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f)
        except Exception:
            # Entornos sin escritura: no rompemos la ejecución.
            pass

    # ------------------------------------------------------------------
    # Auditoría Σ
    # ------------------------------------------------------------------
    def _audit(self, *, severity: str, reason: str) -> None:
        """
        Registro simple de eventos de seguridad.
        No almacena IP, IMEI ni datos personales.
        Guarda:
          - timestamp (UTC)
          - session_id
          - severity
          - reason
          - alert_flag
          - lock_permanent
          - origin / region (lógicos, no físicos).
        """
        event = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "session_id": self.session_id,
            "origin": self.origin,
            "region": self.region,
            "severity": severity,
            "reason": reason,
            "alert_flag": self.state.alert_flag,
            "lock_permanent": self.state.lock_permanent,
        }
        try:
            with open(_AUDIT_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(event, ensure_ascii=False) + "\n")
        except Exception:
            # Entornos sin escritura: no rompemos nada.
            pass

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------
    def is_locked(self) -> bool:
        """Indica si el modo TCDS está bloqueado permanentemente."""
        return self.state.lock_permanent

    def policy_allows_tcds(self) -> bool:
        """
        Regla de política general, configurable desde el servidor
        o el entorno.

        Aquí solo ponemos un ejemplo mínimo: ciertos orígenes pueden
        operar únicamente en modo normal.
        """
        blocked_origins = {"kiosko_publico", "demo_anonima"}
        blocked_regions = set()  # Por si luego quieres añadir regiones.

        if self.origin in blocked_origins:
            return False
        if self.region in blocked_regions:
            return False
        return True

    def guard_tcds_usage(self) -> None:
        """
        Se llama al comienzo de cualquier operación TCDS.
        Si el sistema está bloqueado, o la política lo prohíbe,
        lanza PermissionError.
        """
        if self.state.lock_permanent:
            raise PermissionError(
                "TCDS_LOCK_PERMANENT: El modo TCDS fue deshabilitado "
                "debido a uso malicioso o no autorizado. "
                "Operar únicamente en modo normal."
            )

        if not self.policy_allows_tcds():
            raise PermissionError(
                "TCDS_POLICY_BLOCK: El modo TCDS no está permitido "
                "para este origen o región. Operar únicamente en modo normal."
            )

    def register_event(self, *, severity: str, reason: str) -> None:
        """
        Registra un evento de seguridad.

        severity:
          - "info"    → no cambia estado, solo auditoría.
          - "yellow"  → primera alerta: activa alert_flag.
          - "red"     → bloqueo permanente inmediato.

        Si se recibe una segunda alerta "yellow" con alert_flag ya True,
        se eleva a bloqueo permanente.
        """
        severity = severity.lower().strip()

        if self.state.lock_permanent:
            # Ya está bloqueado; no hay nada que escalar.
            self._audit(severity=severity, reason=reason)
            return

        if severity == "info":
            self._audit(severity=severity, reason=reason)
            return

        if severity == "yellow":
            if self.state.alert_flag:
                # Reincidencia → bloqueo permanente
                self.state.lock_permanent = True
                self.state.lock_reason = (
                    "Reincidencia tras alerta de riesgo (nivel amarillo). "
                    f"Último motivo: {reason}"
                )
            else:
                # Primera advertencia
                self.state.alert_flag = True
                self.state.lock_reason = (
                    f"Primera alerta de riesgo (nivel amarillo): {reason}"
                )
            self._save_state()
            self._audit(severity=severity, reason=reason)
            return

        if severity == "red":
            # Bloqueo inmediato
            self.state.lock_permanent = True
            self.state.lock_reason = f"Bloqueo inmediato (nivel rojo): {reason}"
            self._save_state()
            self._audit(severity=severity, reason=reason)
            return

        # Severidad desconocida: solo auditar, sin cambiar flags.
        self._audit(severity=severity, reason=reason)

    def explain_state(self) -> str:
        """Devuelve una explicación corta del estado de seguridad actual."""
        if self.state.lock_permanent:
            return (
                "Modo TCDS BLOQUEADO permanentemente.\n"
                f"Motivo registrado: {self.state.lock_reason or 'no especificado'}"
            )
        if self.state.alert_flag:
            return (
                "Modo TCDS ACTIVO pero en estado de alerta (nivel amarillo).\n"
                f"Último motivo: {self.state.lock_reason or 'no especificado'}"
            )
        return "Modo TCDS ACTIVO en estado normal (nivel verde)."

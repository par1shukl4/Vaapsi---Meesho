from functools import lru_cache
import os


class Settings:
    service_name: str = "Vaapsi"
    version: str = "0.1.0"
    memory_backend: str = "in_memory"
    default_country_code: str = "+91"
    max_orchestrator_steps: int = 6
    gps_mismatch_threshold_meters: int = 500
    voice_recording_ttl_hours: int = 24
    pii_retention_days: int = 30
    data_region: str = "in"

    def __init__(self) -> None:
        self.service_name = os.getenv("VAAPSI_SERVICE_NAME", self.service_name)
        self.version = os.getenv("VAAPSI_VERSION", self.version)
        self.memory_backend = os.getenv("VAAPSI_MEMORY_BACKEND", self.memory_backend)
        self.default_country_code = os.getenv("VAAPSI_DEFAULT_COUNTRY_CODE", self.default_country_code)
        self.max_orchestrator_steps = self._int_env(
            "VAAPSI_MAX_ORCHESTRATOR_STEPS",
            self.max_orchestrator_steps,
            minimum=1,
            maximum=20,
        )
        self.gps_mismatch_threshold_meters = self._int_env(
            "VAAPSI_GPS_MISMATCH_THRESHOLD_METERS",
            self.gps_mismatch_threshold_meters,
            minimum=50,
        )
        self.voice_recording_ttl_hours = self._int_env(
            "VAAPSI_VOICE_RECORDING_TTL_HOURS",
            self.voice_recording_ttl_hours,
            minimum=1,
        )
        self.pii_retention_days = self._int_env(
            "VAAPSI_PII_RETENTION_DAYS",
            self.pii_retention_days,
            minimum=1,
        )
        self.data_region = os.getenv("VAAPSI_DATA_REGION", self.data_region)

    @staticmethod
    def _int_env(name: str, default: int, minimum: int, maximum: int | None = None) -> int:
        raw = os.getenv(name)
        if raw is None:
            return default
        value = int(raw)
        if value < minimum:
            raise ValueError(f"{name} must be >= {minimum}")
        if maximum is not None and value > maximum:
            raise ValueError(f"{name} must be <= {maximum}")
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()

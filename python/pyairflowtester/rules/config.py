"""
Airflow configuration audit rules (CFG001-CFG015).

These rules check airflow.cfg and runtime configuration for best practices.
"""

from typing import Any, Dict, List


class BaseRule:
    """Base configuration rule."""

    def __init__(self):
        self.id = ""
        self.name = ""
        self.severity = ""
        self.category = ""
        self.execution_mode = ""

    def evaluate(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Evaluate rule against configuration."""
        raise NotImplementedError


class ExecutorConfigurationRule(BaseRule):
    """Check executor type matches workload."""

    def __init__(self):
        super().__init__()
        self.id = "CFG001"
        self.name = "Executor Misconfiguration"
        self.severity = "high"
        self.category = "performance"
        self.execution_mode = "static"

    def evaluate(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check executor configuration."""
        violations = []

        executor = config.get("core", {}).get("executor", "SequentialExecutor")

        # SequentialExecutor only for testing
        if executor == "SequentialExecutor":
            violations.append({
                "rule_id": self.id,
                "severity": "high",
                "affected_resource": "core.executor",
                "message": "Using SequentialExecutor in production (no parallelism)",
                "remediation": "Use LocalExecutor, CeleryExecutor, or KubernetesExecutor",
            })

        # Check KubernetesExecutor has resource limits
        if executor == "KubernetesExecutor":
            if not config.get("kubernetes", {}).get("enable_security_context"):
                violations.append({
                    "rule_id": self.id,
                    "severity": "medium",
                    "affected_resource": "core.executor",
                    "message": "KubernetesExecutor without security context",
                    "remediation": "Enable security context and resource limits",
                })

        return violations


class AirflowCfgPoolConfigurationRule(BaseRule):
    """Check pool configuration in airflow.cfg (CFG002)."""

    def __init__(self):
        super().__init__()
        self.id = "CFG002"
        self.name = "Pool Size Mismatch"
        self.severity = "medium"
        self.category = "reliability"
        self.execution_mode = "static"

    def evaluate(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check pool sizes."""
        violations = []

        default_pool_size = config.get("core", {}).get("default_pool_size", 128)
        max_active_runs = config.get("core", {}).get("max_active_dag_runs", 16)

        if int(default_pool_size) < int(max_active_runs) * 5:
            violations.append({
                "rule_id": self.id,
                "severity": self.severity,
                "affected_resource": "core.default_pool_size",
                "message": f"Pool size ({default_pool_size}) too small for max runs ({max_active_runs})",
                "remediation": "Increase default_pool_size or reduce max_active_dag_runs",
            })

        return violations


class ConcurrencyConfigurationRule(BaseRule):
    """Check DAG/task concurrency settings."""

    def __init__(self):
        super().__init__()
        self.id = "CFG003"
        self.name = "Concurrency Mismatch"
        self.severity = "medium"
        self.category = "performance"
        self.execution_mode = "static"

    def evaluate(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check concurrency configuration."""
        violations = []

        dag_concurrency = int(config.get("core", {}).get("dag_concurrency", 16))
        parallelism = int(config.get("core", {}).get("parallelism", 32))

        if dag_concurrency > parallelism:
            violations.append({
                "rule_id": self.id,
                "severity": self.severity,
                "affected_resource": "core.dag_concurrency",
                "message": f"dag_concurrency ({dag_concurrency}) exceeds parallelism ({parallelism})",
                "remediation": "Reduce dag_concurrency or increase parallelism",
            })

        return violations


class QueueConfigurationRule(BaseRule):
    """Check queue configuration."""

    def __init__(self):
        super().__init__()
        self.id = "CFG004"
        self.name = "Queue Bottleneck"
        self.severity = "medium"
        self.category = "reliability"
        self.execution_mode = "static"

    def evaluate(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check queue configuration."""
        violations = []

        # Check if using single queue for all DAGs
        if "default_queue" in config.get("celery", {}):
            violations.append({
                "rule_id": self.id,
                "severity": self.severity,
                "affected_resource": "celery.default_queue",
                "message": "Single default queue (no prioritization)",
                "remediation": "Create separate queues for priority levels and DAG types",
            })

        return violations


class MaxActiveRunsRule(BaseRule):
    """Check max_active_dag_runs."""

    def __init__(self):
        super().__init__()
        self.id = "CFG005"
        self.name = "Max Active Runs Not Limited"
        self.severity = "high"
        self.category = "reliability"
        self.execution_mode = "static"

    def evaluate(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check max active runs limit."""
        violations = []

        max_active = int(config.get("core", {}).get("max_active_dag_runs", 16))

        if max_active > 32:
            violations.append({
                "rule_id": self.id,
                "severity": self.severity,
                "affected_resource": "core.max_active_dag_runs",
                "message": f"Max active runs too high ({max_active}), risk of runaway backfill",
                "remediation": "Reduce max_active_dag_runs to 8-16",
            })

        return violations


class XComConfigurationRule(BaseRule):
    """Check XCom backend."""

    def __init__(self):
        super().__init__()
        self.id = "CFG006"
        self.name = "XCom Backend Issue"
        self.severity = "medium"
        self.category = "performance"
        self.execution_mode = "static"

    def evaluate(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check XCom configuration."""
        violations = []

        xcom_backend = config.get("core", {}).get("xcom_backend", "airflow.models.xcom.BaseXCom")

        if "BaseXCom" in xcom_backend or "DbXCom" in xcom_backend:
            violations.append({
                "rule_id": self.id,
                "severity": self.severity,
                "affected_resource": "core.xcom_backend",
                "message": "XCom using database backend (causes bloat)",
                "remediation": "Use S3XCom or custom cloud storage backend",
            })

        return violations


class LogRetentionRule(BaseRule):
    """Check log retention."""

    def __init__(self):
        super().__init__()
        self.id = "CFG007"
        self.name = "Insufficient Log Retention"
        self.severity = "medium"
        self.category = "compliance"
        self.execution_mode = "static"

    def evaluate(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check log retention."""
        violations = []

        log_retention = int(config.get("logging", {}).get("log_retention_days", 30))

        if log_retention < 30:
            violations.append({
                "rule_id": self.id,
                "severity": self.severity,
                "affected_resource": "logging.log_retention_days",
                "message": f"Log retention < 30 days ({log_retention}), compliance risk",
                "remediation": "Increase log_retention_days to minimum 30-90 days",
            })

        return violations


class EncryptionConfigurationRule(BaseRule):
    """Check encryption settings."""

    def __init__(self):
        super().__init__()
        self.id = "CFG008"
        self.name = "Encryption Not Configured"
        self.severity = "high"
        self.category = "security"
        self.execution_mode = "static"

    def evaluate(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check encryption."""
        violations = []

        fernet_key = config.get("core", {}).get("fernet_key")

        if not fernet_key or fernet_key == "[NOT CONFIGURED]":
            violations.append({
                "rule_id": self.id,
                "severity": self.severity,
                "affected_resource": "core.fernet_key",
                "message": "Fernet encryption not configured",
                "remediation": "Generate Fernet key: python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key())'",
            })

        return violations


class TLSConfigurationRule(BaseRule):
    """Check TLS settings."""

    def __init__(self):
        super().__init__()
        self.id = "CFG009"
        self.name = "TLS Not Enabled"
        self.severity = "high"
        self.category = "security"
        self.execution_mode = "static"

    def evaluate(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check TLS configuration."""
        violations = []

        enable_ssl = config.get("webserver", {}).get("enable_ssl", False)

        if not enable_ssl:
            violations.append({
                "rule_id": self.id,
                "severity": self.severity,
                "affected_resource": "webserver.enable_ssl",
                "message": "TLS/SSL not enabled for Airflow web UI",
                "remediation": "Set enable_ssl=True and provide cert_file/key_file",
            })

        return violations


class RBACConfigurationRule(BaseRule):
    """Check RBAC settings."""

    def __init__(self):
        super().__init__()
        self.id = "CFG010"
        self.name = "RBAC Disabled"
        self.severity = "high"
        self.category = "security"
        self.execution_mode = "static"

    def evaluate(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check RBAC configuration."""
        violations = []

        auth_backend = config.get("webserver", {}).get("rbac", True)

        if not auth_backend:
            violations.append({
                "rule_id": self.id,
                "severity": self.severity,
                "affected_resource": "webserver.rbac",
                "message": "RBAC disabled, no access control",
                "remediation": "Enable RBAC and configure authentication backend",
            })

        return violations


class SchedulerConfigurationRule(BaseRule):
    """Check scheduler settings."""

    def __init__(self):
        super().__init__()
        self.id = "CFG011"
        self.name = "Scheduler Misconfiguration"
        self.severity = "medium"
        self.category = "performance"
        self.execution_mode = "static"

    def evaluate(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check scheduler configuration."""
        violations = []

        heartbeat_sec = int(config.get("scheduler", {}).get("scheduler_heartbeat_sec", 5))

        if heartbeat_sec < 2:
            violations.append({
                "rule_id": self.id,
                "severity": self.severity,
                "affected_resource": "scheduler.scheduler_heartbeat_sec",
                "message": f"Scheduler heartbeat too frequent ({heartbeat_sec}s), high CPU",
                "remediation": "Increase heartbeat_sec to 5-10 seconds",
            })

        return violations


class WorkerConfigurationRule(BaseRule):
    """Check worker settings."""

    def __init__(self):
        super().__init__()
        self.id = "CFG012"
        self.name = "Worker Misconfiguration"
        self.severity = "medium"
        self.category = "reliability"
        self.execution_mode = "static"

    def evaluate(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check worker configuration."""
        violations = []

        prefetch = int(config.get("celery", {}).get("worker_prefetch_multiplier", 1))

        if prefetch > 2:
            violations.append({
                "rule_id": self.id,
                "severity": self.severity,
                "affected_resource": "celery.worker_prefetch_multiplier",
                "message": f"Worker prefetch multiplier > 2 ({prefetch}), memory risk",
                "remediation": "Reduce to 1-2 and monitor memory usage",
            })

        return violations


class LogStorageRule(BaseRule):
    """Check log storage location."""

    def __init__(self):
        super().__init__()
        self.id = "CFG013"
        self.name = "Local Log Storage"
        self.severity = "high"
        self.category = "reliability"
        self.execution_mode = "static"

    def evaluate(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check log storage."""
        violations = []

        log_folder = config.get("logging", {}).get("base_log_folder", "/var/log/airflow")

        if "/var/log" in log_folder or "/tmp" in log_folder:
            violations.append({
                "rule_id": self.id,
                "severity": self.severity,
                "affected_resource": "logging.base_log_folder",
                "message": "Logs stored on local disk (no HA, no persistence)",
                "remediation": "Use S3, GCS, or HDFS for log storage",
            })

        return violations


class DatabaseBackupRule(BaseRule):
    """Check database backup configuration."""

    def __init__(self):
        super().__init__()
        self.id = "CFG014"
        self.name = "No Database Backup"
        self.severity = "high"
        self.category = "reliability"
        self.execution_mode = "static"

    def evaluate(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check database backup."""
        violations = []

        # Check if backup configuration present
        if "backup" not in str(config).lower():
            violations.append({
                "rule_id": self.id,
                "severity": self.severity,
                "affected_resource": "database",
                "message": "No database backup configuration detected",
                "remediation": "Configure daily backups of Airflow metadata database",
            })

        return violations


class DAGFolderConfigurationRule(BaseRule):
    """Check DAG folder configuration."""

    def __init__(self):
        super().__init__()
        self.id = "CFG015"
        self.name = "DAG Folder On NFS"
        self.severity = "medium"
        self.category = "performance"
        self.execution_mode = "static"

    def evaluate(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check DAG folder location."""
        violations = []

        dag_folder = config.get("core", {}).get("dags_folder", "/airflow/dags")

        if "/mnt" in dag_folder or "/nfs" in dag_folder:
            violations.append({
                "rule_id": self.id,
                "severity": self.severity,
                "affected_resource": "core.dags_folder",
                "message": "DAG folder on NFS mount (parse time issues)",
                "remediation": "Use local SSD storage or container volume mounts",
            })

        return violations

"""Tests for advanced DAG rules (AFW005-AFW015)."""

from pyairflowtester.rules.dag_advanced import (
    AlertingConfigurationRule,
    CatchupConfigRule,
    DocumentationRule,
    HardcodedConnectionRule,
    OperatorDeprecationRule,
    RetryConfigurationRule,
    SecretsInCodeRule,
    SensorTimeoutRule,
    TaskCountRule,
)


class TestTaskCountRule:
    """Test excessive task count detection."""

    def test_high_task_count(self):
        """Test detection of DAGs with >500 tasks."""
        rule = TaskCountRule()
        source_code = "\n".join([f"task_{i} = PythonOperator(task_id='task_{i}')" for i in range(600)])
        violations = rule.evaluate(source_code, "test.py")
        assert len(violations) > 0
        assert violations[0]["rule_id"] == "AFW005"

    def test_normal_task_count(self):
        """Test normal task count doesn't trigger."""
        rule = TaskCountRule()
        source_code = "\n".join([f"task_{i} = PythonOperator(task_id='task_{i}')" for i in range(50)])
        violations = rule.evaluate(source_code, "test.py")
        assert len(violations) == 0


class TestCatchupConfigRule:
    """Test catchup configuration detection."""

    def test_risky_catchup(self):
        """Test detection of catchup=True without strategy."""
        rule = CatchupConfigRule()
        source_code = "dag = DAG('test', catchup=True)"
        violations = rule.evaluate(source_code, "test.py")
        assert len(violations) > 0
        assert violations[0]["rule_id"] == "AFW006"

    def test_safe_catchup(self):
        """Test catchup=True with strategy is safe."""
        rule = CatchupConfigRule()
        source_code = """
dag = DAG('test', catchup=True)
backfill_handler = BackfillDAG(dag)
"""
        violations = rule.evaluate(source_code, "test.py")
        assert len(violations) == 0


class TestHardcodedConnectionRule:
    """Test hardcoded connection detection."""

    def test_hardcoded_connection_string(self):
        """Test detection of hardcoded connection strings."""
        rule = HardcodedConnectionRule()
        source_code = "conn_id = 'postgres://user:pass@localhost:5432/db'"
        violations = rule.evaluate(source_code, "test.py")
        assert len(violations) > 0
        assert violations[0]["rule_id"] == "AFW008"

    def test_hardcoded_host(self):
        """Test detection of localhost references."""
        rule = HardcodedConnectionRule()
        source_code = 'host = "localhost"'
        violations = rule.evaluate(source_code, "test.py")
        assert len(violations) > 0


class TestSecretsInCodeRule:
    """Test secrets detection."""

    def test_hardcoded_password(self):
        """Test detection of hardcoded password."""
        rule = SecretsInCodeRule()
        source_code = 'password = "my_secret_password"'
        violations = rule.evaluate(source_code, "test.py")
        assert len(violations) > 0
        assert violations[0]["rule_id"] == "AFW009"

    def test_hardcoded_api_key(self):
        """Test detection of hardcoded API key."""
        rule = SecretsInCodeRule()
        source_code = 'api_key = "sk-1234567890abcdef"'
        violations = rule.evaluate(source_code, "test.py")
        assert len(violations) > 0

    def test_no_secrets(self):
        """Test clean code passes."""
        rule = SecretsInCodeRule()
        source_code = 'api_key = os.environ["API_KEY"]'
        violations = rule.evaluate(source_code, "test.py")
        assert len(violations) == 0


class TestRetryConfigurationRule:
    """Test retry configuration detection."""

    def test_high_retry_count(self):
        """Test detection of high retry count without backoff."""
        rule = RetryConfigurationRule()
        source_code = "task = PythonOperator(..., retries=10)"
        violations = rule.evaluate(source_code, "test.py")
        assert len(violations) > 0
        assert violations[0]["rule_id"] == "AFW010"

    def test_high_retry_with_backoff(self):
        """Test high retry count with backoff is OK."""
        rule = RetryConfigurationRule()
        source_code = """
task = PythonOperator(
    ...,
    retries=10,
    retry_delay=timedelta(minutes=1),
    retry_exponential_backoff=True
)
"""
        violations = rule.evaluate(source_code, "test.py")
        assert len(violations) == 0


class TestSensorTimeoutRule:
    """Test sensor timeout detection."""

    def test_high_timeout(self):
        """Test detection of sensor with >1h timeout."""
        rule = SensorTimeoutRule()
        source_code = """
sensor = TimeSensor(
    ...
    timeout=7200
)
"""
        violations = rule.evaluate(source_code, "test.py")
        assert len(violations) > 0
        assert violations[0]["rule_id"] == "AFW011"

    def test_reasonable_timeout(self):
        """Test reasonable sensor timeout passes."""
        rule = SensorTimeoutRule()
        source_code = """
sensor = TimeSensor(
    ...
    timeout=1800,
    poke_interval=60
)
"""
        violations = rule.evaluate(source_code, "test.py")
        assert len(violations) == 0


class TestDocumentationRule:
    """Test documentation detection."""

    def test_missing_description(self):
        """Test detection of missing DAG description."""
        rule = DocumentationRule()
        source_code = "dag = DAG('test_dag', start_date=datetime(2024, 1, 1))"
        violations = rule.evaluate(source_code, "test.py")
        assert len(violations) > 0
        assert violations[0]["rule_id"] == "AFW013"

    def test_with_description(self):
        """Test DAG with description passes."""
        rule = DocumentationRule()
        source_code = """
dag = DAG(
    'test_dag',
    description='This is a test DAG',
    start_date=datetime(2024, 1, 1)
)
"""
        violations = rule.evaluate(source_code, "test.py")
        assert len(violations) == 0


class TestAlertingConfigurationRule:
    """Test alerting configuration detection."""

    def test_production_without_alerts(self):
        """Test production DAG without alerts."""
        rule = AlertingConfigurationRule()
        source_code = "dag = DAG('production_etl')"
        violations = rule.evaluate(source_code, "production_etl.py")
        assert len(violations) > 0
        assert violations[0]["rule_id"] == "AFW014"

    def test_production_with_alerts(self):
        """Test production DAG with alerts passes."""
        rule = AlertingConfigurationRule()
        source_code = """
dag = DAG(
    'production_etl',
    on_failure_callback=notify_slack
)
"""
        violations = rule.evaluate(source_code, "production_etl.py")
        assert len(violations) == 0


class TestOperatorDeprecationRule:
    """Test deprecated operator detection."""

    def test_subdagoperator(self):
        """Test detection of SubDagOperator."""
        rule = OperatorDeprecationRule()
        source_code = "task = SubDagOperator(subdag=create_subdag())"
        violations = rule.evaluate(source_code, "test.py")
        assert len(violations) > 0
        assert violations[0]["rule_id"] == "AFW015"

    def test_dummyoperator(self):
        """Test detection of DummyOperator."""
        rule = OperatorDeprecationRule()
        source_code = "task = DummyOperator(task_id='dummy')"
        violations = rule.evaluate(source_code, "test.py")
        assert len(violations) > 0

    def test_modern_operators(self):
        """Test modern operators pass."""
        rule = OperatorDeprecationRule()
        source_code = """
@task
def my_task():
    pass

@task_group
def my_task_group():
    pass
"""
        violations = rule.evaluate(source_code, "test.py")
        assert len(violations) == 0

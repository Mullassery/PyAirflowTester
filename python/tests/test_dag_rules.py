"""Tests for basic DAG rules (dag.py: AFW001-AFW004).

CircularDependencyRule in particular used to crash with
`re.error: invalid group reference 1` on every single invocation (its regex
referenced a backreference group \\1 that the pattern never captured). That
exception propagated up through Scanner.scan_dags' single per-file
try/except and silently zeroed out every other rule's findings too. These
tests lock in the graph-cycle-detection redesign that replaced the broken
regex.
"""

from pyairflowtester.rules.dag import (
    CircularDependencyRule,
    ExpensiveImportsRule,
    MissingSLARule,
    ParseTimeRule,
)


class TestCircularDependencyRule:
    """Test graph-based circular dependency detection."""

    def test_does_not_raise(self):
        """The rule must never raise re.error; previously it always did."""
        rule = CircularDependencyRule()
        rule.evaluate("task1 >> task2 >> task3 >> task1", "test.py")

    def test_detects_three_node_cycle_via_shift_operator(self):
        rule = CircularDependencyRule()
        violations = rule.evaluate("task1 >> task2 >> task3 >> task1", "test.py")
        assert len(violations) == 1
        assert violations[0]["rule_id"] == "AFW001"

    def test_detects_two_node_cycle(self):
        rule = CircularDependencyRule()
        violations = rule.evaluate("a >> b\nb >> a\n", "test.py")
        assert len(violations) == 1

    def test_detects_cycle_via_set_downstream(self):
        rule = CircularDependencyRule()
        source = "a.set_downstream(b)\nb.set_downstream(c)\nc.set_downstream(a)\n"
        violations = rule.evaluate(source, "test.py")
        assert len(violations) == 1

    def test_detects_cycle_via_set_upstream(self):
        rule = CircularDependencyRule()
        # a upstream of b, b upstream of c, c upstream of a -> a<-b<-c<-a cycle
        source = "b.set_upstream(a)\nc.set_upstream(b)\na.set_upstream(c)\n"
        violations = rule.evaluate(source, "test.py")
        assert len(violations) == 1

    def test_no_cycle_on_linear_chain(self):
        rule = CircularDependencyRule()
        violations = rule.evaluate("task1 >> task2 >> task3", "test.py")
        assert violations == []

    def test_no_cycle_on_empty_source(self):
        rule = CircularDependencyRule()
        assert rule.evaluate("", "test.py") == []

    def test_no_false_positive_on_diamond_dependency(self):
        """A >> B, A >> C, B >> D, C >> D is a DAG (diamond), not a cycle."""
        rule = CircularDependencyRule()
        source = "a >> b\na >> c\nb >> d\nc >> d\n"
        violations = rule.evaluate(source, "test.py")
        assert violations == []


class TestMissingSLARule:
    def test_flags_production_dag_without_sla(self):
        rule = MissingSLARule()
        violations = rule.evaluate("dag = DAG('x')", "production_dag.py")
        assert len(violations) == 1
        assert violations[0]["rule_id"] == "AFW002"

    def test_ignores_non_production_dag(self):
        rule = MissingSLARule()
        violations = rule.evaluate("dag = DAG('x')", "test.py")
        assert violations == []


class TestExpensiveImportsRule:
    def test_flags_tensorflow_import(self):
        rule = ExpensiveImportsRule()
        violations = rule.evaluate("import tensorflow as tf\n", "test.py")
        assert any(v["rule_id"] == "AFW003" for v in violations)

    def test_clean_source_has_no_violations(self):
        rule = ExpensiveImportsRule()
        violations = rule.evaluate("import os\n", "test.py")
        assert violations == []


class TestParseTimeRule:
    def test_flags_loop_based_dag_generation(self):
        rule = ParseTimeRule()
        source = "for i in range(10):\n    create_DAG(i)\n"
        violations = rule.evaluate(source, "test.py")
        assert len(violations) == 1
        assert violations[0]["rule_id"] == "AFW004"

    def test_clean_source_has_no_violations(self):
        rule = ParseTimeRule()
        violations = rule.evaluate("dag = DAG('x')", "test.py")
        assert violations == []

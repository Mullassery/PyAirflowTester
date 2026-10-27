# Security Vulnerability Audit - PyAirflowTester

**Audit Date:** 2026-10-27
**Repository:** /Users/georgimullassery/Desktop/Projects/PyAirflowTester
**Total Findings:** 134

## Summary
- **Critical:** 97
- **High:** 2
- **Medium:** 35

## Findings

### 1. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/_pytest/_code/code.py:164
- **Description:** eval()
- **Evidence (Line):** `def eval(self, code, **vars):`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 2. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/_pytest/_code/code.py:173
- **Description:** eval()
- **Evidence (Line):** `return eval(code, self.f_globals, f_locals)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 3. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/_pytest/_code/code.py:326
- **Description:** eval()
- **Evidence (Line):** `# however via `exec(...)` / `eval(...)` they can be other types`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 4. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/_pytest/_code/code.py:326
- **Description:** exec()
- **Evidence (Line):** `# however via `exec(...)` / `eval(...)` they can be other types`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 5. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/_pytest/_py/path.py:1153
- **Description:** exec()
- **Evidence (Line):** `exec(f.read(), mod.__dict__)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 6. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/_pytest/_py/path.py:1159
- **Description:** exec()
- **Evidence (Line):** `def sysexec(self, *argv: os.PathLike[str], **popen_opts: Any) -> str:`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 7. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/_pytest/assertion/rewrite.py:188
- **Description:** exec()
- **Evidence (Line):** `exec(co, module.__dict__)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 8. [Critical] Insecure Deserialization
- **File:** .venv-test/lib/python3.12/site-packages/_pytest/assertion/rewrite.py:393
- **Description:** marshal load
- **Evidence (Line):** `co = marshal.load(fp)`
- **Exploit Scenario:** Attacker could achieve remote code execution
- **Fix Recommendation:** Use safe serialization formats (JSON), avoid pickle/yaml.load with untrusted data
- **Confidence:** High

### 9. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/_pytest/capture.py:1112
- **Description:** os.system()
- **Evidence (Line):** `os.system('echo "hello"')`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 10. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/_pytest/capture.py:1140
- **Description:** os.system()
- **Evidence (Line):** `os.system('echo "hello"')`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 11. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/_pytest/mark/__init__.py:66
- **Description:** eval()
- **Evidence (Line):** `def test_eval(test_input, expected):`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 12. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/_pytest/mark/__init__.py:67
- **Description:** eval()
- **Evidence (Line):** `assert eval(test_input) == expected`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 13. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/_pytest/mark/expression.py:295
- **Description:** eval()
- **Evidence (Line):** `"""Adapts a matcher function to a locals mapping as required by eval()."""`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 14. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/_pytest/mark/expression.py:353
- **Description:** eval()
- **Evidence (Line):** `return bool(eval(self._code, {"__builtins__": {}}, MatcherAdapter(matcher)))`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 15. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/_pytest/pytester.py:296
- **Description:** eval()
- **Evidence (Line):** `if eval(check, backlocals, call.__dict__):`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 16. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/_pytest/skipping.py:92
- **Description:** eval()
- **Evidence (Line):** `If an old-style string condition is given, it is eval()'d, otherwise the`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 17. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/_pytest/skipping.py:119
- **Description:** eval()
- **Evidence (Line):** `result = eval(condition_code, globals_)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 18. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/anyio/_backends/_asyncio.py:2796
- **Description:** exec()
- **Evidence (Line):** `# Use loop.subprocess_shell()/subprocess_exec() rather than their`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 19. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/anyio/_backends/_asyncio.py:2810
- **Description:** exec()
- **Evidence (Line):** `transport, protocol = await loop.subprocess_exec(`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 20. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/anyio/to_interpreter.py:123
- **Description:** exec()
- **Evidence (Line):** `exc_info = _interpreters.exec(self._interpreter_id, _run_func)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 21. [Critical] Insecure Deserialization
- **File:** .venv-test/lib/python3.12/site-packages/anyio/to_interpreter.py:130
- **Description:** pickle load/dumps
- **Evidence (Line):** `res = pickle.loads(res)`
- **Exploit Scenario:** Attacker could achieve remote code execution
- **Fix Recommendation:** Use safe serialization formats (JSON), avoid pickle/yaml.load with untrusted data
- **Confidence:** High

### 22. [Critical] Insecure Deserialization
- **File:** .venv-test/lib/python3.12/site-packages/anyio/to_process.py:95
- **Description:** pickle load/dumps
- **Evidence (Line):** `retval = pickle.loads(pickled_response)`
- **Exploit Scenario:** Attacker could achieve remote code execution
- **Fix Recommendation:** Use safe serialization formats (JSON), avoid pickle/yaml.load with untrusted data
- **Confidence:** High

### 23. [Critical] Insecure Deserialization
- **File:** .venv-test/lib/python3.12/site-packages/anyio/to_process.py:220
- **Description:** pickle load/dumps
- **Evidence (Line):** `command, *args = pickle.load(stdin.buffer)`
- **Exploit Scenario:** Attacker could achieve remote code execution
- **Fix Recommendation:** Use safe serialization formats (JSON), avoid pickle/yaml.load with untrusted data
- **Confidence:** High

### 24. [Critical] Insecure Deserialization
- **File:** .venv-test/lib/python3.12/site-packages/black/cache.py:81
- **Description:** pickle load/dumps
- **Evidence (Line):** `data: dict[str, tuple[float, int, str]] = pickle.load(fobj)`
- **Exploit Scenario:** Attacker could achieve remote code execution
- **Fix Recommendation:** Use safe serialization formats (JSON), avoid pickle/yaml.load with untrusted data
- **Confidence:** High

### 25. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/blib2to3/Grammar.txt:9
- **Description:** eval()
- **Evidence (Line):** `#    eval_input is the input for the eval() and input() functions.`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 26. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/blib2to3/pgen2/conv.py:188
- **Description:** eval()
- **Evidence (Line):** `rawbitset = eval(mo.group(1))`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 27. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/blib2to3/pgen2/conv.py:214
- **Description:** eval()
- **Evidence (Line):** `y = eval(y)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 28. [Critical] Insecure Deserialization
- **File:** .venv-test/lib/python3.12/site-packages/blib2to3/pgen2/grammar.py:124
- **Description:** pickle load/dumps
- **Evidence (Line):** `d = pickle.load(f)`
- **Exploit Scenario:** Attacker could achieve remote code execution
- **Fix Recommendation:** Use safe serialization formats (JSON), avoid pickle/yaml.load with untrusted data
- **Confidence:** High

### 29. [Critical] Insecure Deserialization
- **File:** .venv-test/lib/python3.12/site-packages/blib2to3/pgen2/grammar.py:129
- **Description:** pickle load/dumps
- **Evidence (Line):** `self._update(pickle.loads(pkl))`
- **Exploit Scenario:** Attacker could achieve remote code execution
- **Fix Recommendation:** Use safe serialization formats (JSON), avoid pickle/yaml.load with untrusted data
- **Confidence:** High

### 30. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/blib2to3/pgen2/literals.py:4
- **Description:** eval()
- **Evidence (Line):** `"""Safely evaluate Python string literals without using eval()."""`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 31. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/blib2to3/pgen2/pgen.py:100
- **Description:** eval()
- **Evidence (Line):** `value = eval(label)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 32. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/coverage/execfile.py:222
- **Description:** exec()
- **Evidence (Line):** `exec(code, main_mod.__dict__)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 33. [Critical] Insecure Deserialization
- **File:** .venv-test/lib/python3.12/site-packages/coverage/execfile.py:335
- **Description:** marshal load
- **Evidence (Line):** `code = marshal.load(fpyc)`
- **Exploit Scenario:** Attacker could achieve remote code execution
- **Fix Recommendation:** Use safe serialization formats (JSON), avoid pickle/yaml.load with untrusted data
- **Confidence:** High

### 34. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/coverage/htmlfiles/coverage_html.js:236
- **Description:** exec()
- **Evidence (Line):** `const match = /\.([0-9]+)/.exec(cell.textContent);`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 35. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/coverage/parser.py:691
- **Description:** eval()
- **Evidence (Line):** `return True, eval(node.id)  # pylint: disable=eval-used`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 36. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/coverage/templite.py:70
- **Description:** exec()
- **Evidence (Line):** `exec(python_source, global_namespace)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 37. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/distlib/scripts.py:165
- **Description:** exec()
- **Evidence (Line):** `# shebang, or else using os.exec() to run the entry script will`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 38. [Critical] Hardcoded Secret
- **File:** .venv-test/lib/python3.12/site-packages/httpx/_urls.py:336
- **Description:** Password Assignment detected
- **Evidence (Line):** `username="jo@gmail.com", password="a secret"`
- **Exploit Scenario:** Attacker could extract credentials and gain unauthorized access
- **Fix Recommendation:** Move secrets to environment variables or secret manager, rotate compromised credentials
- **Confidence:** High

### 39. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/mypy/dmypy/client.py:556
- **Description:** os.system()
- **Evidence (Line):** `os.system("")`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 40. [Critical] Insecure Deserialization
- **File:** .venv-test/lib/python3.12/site-packages/mypy/dmypy/client.py:624
- **Description:** pickle load/dumps
- **Evidence (Line):** `options_dict = pickle.loads(b64decode(args.options_data))`
- **Exploit Scenario:** Attacker could achieve remote code execution
- **Fix Recommendation:** Use safe serialization formats (JSON), avoid pickle/yaml.load with untrusted data
- **Confidence:** High

### 41. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/mypy/evalexpr.py:30
- **Description:** eval()
- **Evidence (Line):** `return ast.literal_eval(f"b'{o.value}'")`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 42. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/mypy/evalexpr.py:32
- **Description:** eval()
- **Evidence (Line):** `return ast.literal_eval(f'b"{o.value}"')`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 43. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/mypy/modulefinder.py:864
- **Description:** eval()
- **Evidence (Line):** `sys_path, site_packages = ast.literal_eval(`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 44. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/mypy/test/testdaemon.py:89
- **Description:** subprocess with shell=True
- **Evidence (Line):** `output = subprocess.check_output(`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 45. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/mypyc/test/test_run.py:465
- **Description:** eval()
- **Evidence (Line):** `return ast.literal_eval(m.group(1))`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 46. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/mypyc/test/test_run.py:134
- **Description:** exec()
- **Evidence (Line):** `exec(f.read(), g)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 47. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/packaging/_parser.py:397
- **Description:** eval()
- **Evidence (Line):** `value = ast.literal_eval(python_str)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 48. [Critical] Insecure Deserialization
- **File:** .venv-test/lib/python3.12/site-packages/packaging/_structures.py:10
- **Description:** pickle load/dumps
- **Evidence (Line):** `stand-in classes so that ``pickle.loads()`` can resolve those references.`
- **Exploit Scenario:** Attacker could achieve remote code execution
- **Fix Recommendation:** Use safe serialization formats (JSON), avoid pickle/yaml.load with untrusted data
- **Confidence:** High

### 49. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/pip/_internal/commands/configuration.py:248
- **Description:** subprocess with shell=True
- **Evidence (Line):** `subprocess.check_call(f'{editor} "{fname}"', shell=True)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 50. [Critical] Hardcoded Secret
- **File:** .venv-test/lib/python3.12/site-packages/pip/_internal/network/auth.py:486
- **Description:** Password Assignment detected
- **Evidence (Line):** `password = ask_password("Password: ")`
- **Exploit Scenario:** Attacker could extract credentials and gain unauthorized access
- **Fix Recommendation:** Move secrets to environment variables or secret manager, rotate compromised credentials
- **Confidence:** High

### 51. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/pip/_vendor/distlib/scripts.py:165
- **Description:** exec()
- **Evidence (Line):** `# shebang, or else using os.exec() to run the entry script will`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 52. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/pip/_vendor/packaging/_parser.py:372
- **Description:** eval()
- **Evidence (Line):** `value = ast.literal_eval(python_str)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 53. [Critical] Insecure Deserialization
- **File:** .venv-test/lib/python3.12/site-packages/pip/_vendor/packaging/_structures.py:10
- **Description:** pickle load/dumps
- **Evidence (Line):** `stand-in classes so that ``pickle.loads()`` can resolve those references.`
- **Exploit Scenario:** Attacker could achieve remote code execution
- **Fix Recommendation:** Use safe serialization formats (JSON), avoid pickle/yaml.load with untrusted data
- **Confidence:** High

### 54. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/pip/_vendor/pkg_resources/__init__.py:1714
- **Description:** exec()
- **Evidence (Line):** `exec(code, namespace, namespace)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 55. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/pip/_vendor/pkg_resources/__init__.py:1725
- **Description:** exec()
- **Evidence (Line):** `exec(script_code, namespace, namespace)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 56. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/pip/_vendor/pygments/formatters/__init__.py:91
- **Description:** eval()
- **Evidence (Line):** `this method is equivalent to running ``eval()`` on the input file. The formatter is`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 57. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/pip/_vendor/pygments/formatters/__init__.py:103
- **Description:** exec()
- **Evidence (Line):** `exec(f.read(), custom_namespace)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 58. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/pip/_vendor/pygments/lexers/__init__.py:154
- **Description:** exec()
- **Evidence (Line):** `exec(f.read(), custom_namespace)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 59. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/pip/_vendor/rich/markup.py:190
- **Description:** eval()
- **Evidence (Line):** `meta_params = literal_eval(parameters)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 60. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/pluggy/_hooks.py:512
- **Description:** exec()
- **Evidence (Line):** `return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 61. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/pluggy/_hooks.py:534
- **Description:** exec()
- **Evidence (Line):** `res = self._hookexec(self.name, self._hookimpls.copy(), kwargs, False)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 62. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/pluggy/_hooks.py:573
- **Description:** exec()
- **Evidence (Line):** `return self._hookexec(self.name, hookimpls, kwargs, firstresult)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 63. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/pluggy/_hooks.py:580
- **Description:** exec()
- **Evidence (Line):** `res = self._hookexec(self.name, [method], kwargs, False)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 64. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/pluggy/_manager.py:111
- **Description:** exec()
- **Evidence (Line):** `def _hookexec(`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 65. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/pluggy/_manager.py:120
- **Description:** exec()
- **Evidence (Line):** `return self._inner_hookexec(hook_name, methods, kwargs, firstresult)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 66. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/pluggy/_manager.py:464
- **Description:** exec()
- **Evidence (Line):** `def traced_hookexec(`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 67. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/pre_commit/languages/r.py:35
- **Description:** exec()
- **Evidence (Line):** `_rscript_exec(), *cli_opts, f, *args, cwd=cwd,`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 68. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/pre_commit/languages/r.py:149
- **Description:** exec()
- **Evidence (Line):** `def _rscript_exec() -> str:`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 69. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/pygments/formatters/__init__.py:91
- **Description:** eval()
- **Evidence (Line):** `this method is equivalent to running ``eval()`` on the input file. The formatter is`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 70. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/pygments/formatters/__init__.py:103
- **Description:** exec()
- **Evidence (Line):** `exec(f.read(), custom_namespace)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 71. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/pygments/lexers/__init__.py:154
- **Description:** exec()
- **Evidence (Line):** `exec(f.read(), custom_namespace)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 72. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/pygments/lexers/_julia_builtins.py:150
- **Description:** eval()
- **Evidence (Line):** `v = eval(Symbol(compl.mod))`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 73. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/pygments/lexers/_julia_builtins.py:361
- **Description:** eval()
- **Evidence (Line):** `v = eval(Symbol(compl.mod))`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 74. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/pygments/lexers/special.py:115
- **Description:** eval()
- **Evidence (Line):** `val = ast.literal_eval(val)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 75. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/python_discovery/_py_info_collect.py:165
- **Description:** eval()
- **Evidence (Line):** `tcl_lib = tcl.eval("info library")`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 76. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/python_discovery/_py_info_collect.py:178
- **Description:** eval()
- **Evidence (Line):** `tk_lib = tcl.eval("set tk_library")`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 77. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/python_discovery/_py_info_collect.py:191
- **Description:** eval()
- **Evidence (Line):** `tk_version = tcl.eval("package require Tk")`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 78. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/rich/markup.py:190
- **Description:** eval()
- **Evidence (Line):** `meta_params = literal_eval(parameters)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 79. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/sqlglot/executor/context.py:45
- **Description:** eval()
- **Evidence (Line):** `def eval(self, code):`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 80. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/sqlglot/executor/context.py:46
- **Description:** eval()
- **Evidence (Line):** `return eval(code, self.env)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 81. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/sqlglot/executor/context.py:49
- **Description:** eval()
- **Evidence (Line):** `return tuple(self.eval(code) for code in codes)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 82. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/sqlglot/executor/context.py:84
- **Description:** eval()
- **Evidence (Line):** `rows = [reader.row for reader, _ in self if self.eval(condition)]`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 83. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/sqlglot/executor/python.py:257
- **Description:** eval()
- **Evidence (Line):** `if condition and not context.eval(condition):`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 84. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/sqlglot/executor/python.py:342
- **Description:** eval()
- **Evidence (Line):** `return condition_context.eval(condition) is True`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 85. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/typing_extensions.py:1591
- **Description:** eval()
- **Evidence (Line):** `(unless you are familiar with how eval() and exec() work).  The`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 86. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/typing_extensions.py:4167
- **Description:** eval()
- **Evidence (Line):** `# as a way of emulating annotation scopes when calling `eval()``
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 87. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/typing_extensions.py:4172
- **Description:** eval()
- **Evidence (Line):** `value if not isinstance(value, str) else eval(value, globals, locals)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 88. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/typing_extensions.py:4219
- **Description:** eval()
- **Evidence (Line):** `# If we pass None to eval() below, the globals of this module are used.`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 89. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/typing_extensions.py:4231
- **Description:** eval()
- **Evidence (Line):** `# as a way of emulating annotation scopes when calling `eval()``
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 90. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/typing_extensions.py:4254
- **Description:** eval()
- **Evidence (Line):** `value = eval(code, globals, locals)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 91. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/typing_extensions.py:1591
- **Description:** exec()
- **Evidence (Line):** `(unless you are familiar with how eval() and exec() work).  The`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 92. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/virtualenv/create/creator.py:331
- **Description:** eval()
- **Evidence (Line):** `result = literal_eval(out)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 93. [Critical] Insecure Deserialization
- **File:** docs/archive/DEPENDENCY_CACHING_STRATEGY.md:431
- **Description:** pickle load/dumps
- **Evidence (Line):** `return pickle.loads(value)`
- **Exploit Scenario:** Attacker could achieve remote code execution
- **Fix Recommendation:** Use safe serialization formats (JSON), avoid pickle/yaml.load with untrusted data
- **Confidence:** High

### 94. [Critical] Command Injection
- **File:** htmlcov/coverage_html_cb_15cffcd0.js:236
- **Description:** exec()
- **Evidence (Line):** `const match = /\.([0-9]+)/.exec(cell.textContent);`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 95. [Critical] Hardcoded Secret
- **File:** python/tests/test_dag_advanced_rules.py:92
- **Description:** API Key Assignment detected
- **Evidence (Line):** `source_code = 'api_key = "sk-1234567890abcdef"'`
- **Exploit Scenario:** Attacker could extract credentials and gain unauthorized access
- **Fix Recommendation:** Move secrets to environment variables or secret manager, rotate compromised credentials
- **Confidence:** High

### 96. [Critical] Hardcoded Secret
- **File:** python/tests/test_dag_advanced_rules.py:111
- **Description:** API Key Assignment detected
- **Evidence (Line):** `source_code = 'STRIPE_API_KEY = "not-a-real-key-just-a-fake-test-value-123"'`
- **Exploit Scenario:** Attacker could extract credentials and gain unauthorized access
- **Fix Recommendation:** Move secrets to environment variables or secret manager, rotate compromised credentials
- **Confidence:** High

### 97. [Critical] Hardcoded Secret
- **File:** python/tests/test_dag_advanced_rules.py:84
- **Description:** Password Assignment detected
- **Evidence (Line):** `source_code = 'password = "my_secret_password"'`
- **Exploit Scenario:** Attacker could extract credentials and gain unauthorized access
- **Fix Recommendation:** Move secrets to environment variables or secret manager, rotate compromised credentials
- **Confidence:** High

### 98. [High] SQL Injection
- **File:** .venv-test/lib/python3.12/site-packages/mypy/metastore.py:216
- **Description:** SQL f-string interpolation
- **Evidence (Line):** `cur = db.execute(f"SELECT {field} FROM files2 WHERE path = ?", (name,))`
- **Exploit Scenario:** Attacker could manipulate SQL queries to access/modify/delete data
- **Fix Recommendation:** Use parameterized queries/prepared statements
- **Confidence:** Medium

### 99. [High] SQL Injection
- **File:** python/pyairflowtester/openlineage.py:129
- **Description:** SQL f-string interpolation
- **Evidence (Line):** `return int(self._conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])`
- **Exploit Scenario:** Attacker could manipulate SQL queries to access/modify/delete data
- **Fix Recommendation:** Use parameterized queries/prepared statements
- **Confidence:** Medium

### 100. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/coverage/lcovreport.py:43
- **Description:** MD5 usage
- **Evidence (Line):** `hashed = hashlib.md5(line.encode("utf-8"), usedforsecurity=False).digest()`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 101. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/coverage/lcovreport.py:43
- **Description:** Weak hash algorithm
- **Evidence (Line):** `hashed = hashlib.md5(line.encode("utf-8"), usedforsecurity=False).digest()`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 102. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/distlib/database.py:1001
- **Description:** MD5 usage
- **Evidence (Line):** `def _md5(path):`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 103. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/distlib/database.py:1007
- **Description:** MD5 usage
- **Evidence (Line):** `return hashlib.md5(content).hexdigest()`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 104. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/distlib/database.py:1027
- **Description:** MD5 usage
- **Evidence (Line):** `result.append((p, _md5(p), _size(p)))`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 105. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/distlib/database.py:513
- **Description:** Weak hash algorithm
- **Evidence (Line):** `hasher = hashlib.md5`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 106. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/distlib/database.py:1007
- **Description:** Weak hash algorithm
- **Evidence (Line):** `return hashlib.md5(content).hexdigest()`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 107. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/distlib/index.py:269
- **Description:** MD5 usage
- **Evidence (Line):** `md5_digest = hashlib.md5(file_data).hexdigest()`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 108. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/distlib/index.py:269
- **Description:** Weak hash algorithm
- **Evidence (Line):** `md5_digest = hashlib.md5(file_data).hexdigest()`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 109. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/httpx/_auth.py:309
- **Description:** SHA1 usage
- **Evidence (Line):** `return hashlib.sha1(s).hexdigest()[:16].encode()`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 110. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/httpx/_auth.py:177
- **Description:** Weak hash algorithm
- **Evidence (Line):** `"MD5": hashlib.md5,`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 111. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/httpx/_auth.py:178
- **Description:** Weak hash algorithm
- **Evidence (Line):** `"MD5-SESS": hashlib.md5,`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 112. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/httpx/_auth.py:179
- **Description:** Weak hash algorithm
- **Evidence (Line):** `"SHA": hashlib.sha1,`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 113. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/httpx/_auth.py:180
- **Description:** Weak hash algorithm
- **Evidence (Line):** `"SHA-SESS": hashlib.sha1,`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 114. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/httpx/_auth.py:309
- **Description:** Weak hash algorithm
- **Evidence (Line):** `return hashlib.sha1(s).hexdigest()[:16].encode()`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 115. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/mypy/util.py:579
- **Description:** SHA1 usage
- **Evidence (Line):** `return hashlib.sha1(data).hexdigest()`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 116. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/mypy/util.py:587
- **Description:** SHA1 usage
- **Evidence (Line):** `return hashlib.sha1(data).digest()`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 117. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/mypy/util.py:579
- **Description:** Weak hash algorithm
- **Evidence (Line):** `return hashlib.sha1(data).hexdigest()`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 118. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/mypy/util.py:587
- **Description:** Weak hash algorithm
- **Evidence (Line):** `return hashlib.sha1(data).digest()`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 119. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/mypyc/build.py:302
- **Description:** SHA1 usage
- **Evidence (Line):** `h = hashlib.sha1()`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 120. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/mypyc/build.py:302
- **Description:** Weak hash algorithm
- **Evidence (Line):** `h = hashlib.sha1()`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 121. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/pip/_vendor/requests/auth.py:179
- **Description:** MD5 usage
- **Evidence (Line):** `return hashlib.md5(x, usedforsecurity=False).hexdigest()`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 122. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/pip/_vendor/requests/auth.py:187
- **Description:** SHA1 usage
- **Evidence (Line):** `return hashlib.sha1(x, usedforsecurity=False).hexdigest()`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 123. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/pip/_vendor/requests/auth.py:237
- **Description:** SHA1 usage
- **Evidence (Line):** `cnonce = hashlib.sha1(s, usedforsecurity=False).hexdigest()[:16]`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 124. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/pip/_vendor/requests/auth.py:179
- **Description:** Weak hash algorithm
- **Evidence (Line):** `return hashlib.md5(x, usedforsecurity=False).hexdigest()`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 125. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/pip/_vendor/requests/auth.py:187
- **Description:** Weak hash algorithm
- **Evidence (Line):** `return hashlib.sha1(x, usedforsecurity=False).hexdigest()`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 126. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/pip/_vendor/requests/auth.py:237
- **Description:** Weak hash algorithm
- **Evidence (Line):** `cnonce = hashlib.sha1(s, usedforsecurity=False).hexdigest()[:16]`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 127. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/pip/_vendor/rich/tree.py:18
- **Description:** DES usage
- **Evidence (Line):** `ASCII_GUIDES (GuideType): Guide lines used when Console.ascii_only is True.`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 128. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/pip/_vendor/rich/tree.py:19
- **Description:** DES usage
- **Evidence (Line):** `TREE_GUIDES (List[GuideType, GuideType, GuideType]): Default guide lines.`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 129. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/pre_commit/languages/docker.py:69
- **Description:** MD5 usage
- **Evidence (Line):** `def md5(s: str) -> str:  # pragma: win32 no cover`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 130. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/pre_commit/languages/docker.py:70
- **Description:** MD5 usage
- **Evidence (Line):** `return hashlib.md5(s.encode()).hexdigest()`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 131. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/pre_commit/languages/docker.py:74
- **Description:** MD5 usage
- **Evidence (Line):** `md5sum = md5(os.path.basename(prefix.prefix_dir)).lower()`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 132. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/pre_commit/languages/docker.py:70
- **Description:** Weak hash algorithm
- **Evidence (Line):** `return hashlib.md5(s.encode()).hexdigest()`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 133. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/rich/tree.py:18
- **Description:** DES usage
- **Evidence (Line):** `ASCII_GUIDES (GuideType): Guide lines used when Console.ascii_only is True.`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 134. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/rich/tree.py:19
- **Description:** DES usage
- **Evidence (Line):** `TREE_GUIDES (List[GuideType, GuideType, GuideType]): Default guide lines.`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

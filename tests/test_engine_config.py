"""Unit tests for engine-config.py.

Validates structure, security-critical values, and output formatting
of the CI engine configuration used by GitHub Actions workflows.
"""

import importlib.util
import io
import os
import sys
import tempfile
import unittest

# engine-config.py has a hyphen, so import via importlib
_spec = importlib.util.spec_from_file_location(
    "engine_config",
    os.path.join(os.path.dirname(__file__), "..", ".github", "scripts", "engine-config.py"),
)
ec = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ec)


class TestDomains(unittest.TestCase):
    """Tests for _domains() helper."""

    def test_deduplication(self):
        """Duplicates between common and extra are removed."""
        overlap = [ec.COMMON_DOMAINS[0]]
        result = ec._domains(overlap)
        items = result.split(",")
        self.assertEqual(len(items), len(set(items)))

    def test_sorted(self):
        """Output is lexicographically sorted."""
        result = ec._domains(ec.CLAUDE_EXTRA_DOMAINS)
        items = result.split(",")
        self.assertEqual(items, sorted(items))

    def test_comma_separated(self):
        """Output is comma-separated with no spaces."""
        result = ec._domains([])
        self.assertNotIn(", ", result)
        self.assertNotIn(" ,", result)

    def test_empty_extras(self):
        """Empty extras list returns only common domains."""
        result = ec._domains([])
        items = result.split(",")
        self.assertEqual(set(items), set(ec.COMMON_DOMAINS))


class TestEnginesDict(unittest.TestCase):
    """Tests for the ENGINES configuration dict."""

    EXPECTED_ENGINES = {"claude", "copilot", "codex"}
    REQUIRED_KEYS = {
        "engine_name", "agent_version", "secret_name", "secret_env_name",
        "secret_docs_url", "install_cmd", "setup_node", "awf_extra_flags",
        "model_env_var", "model_detection_env_var", "mcp_config_path",
        "log_parser", "agent_log_path", "concurrency_prefix",
        "extra_agent_env", "mcp_gateway_config_style", "allowed_domains",
        "cli_cmd", "detection_cli_cmd",
    }
    KNOWN_SECRETS = {"ANTHROPIC_API_KEY", "COPILOT_GITHUB_TOKEN", "OPENAI_API_KEY"}

    def test_all_engines_present(self):
        self.assertEqual(set(ec.ENGINES.keys()), self.EXPECTED_ENGINES)

    def test_required_keys(self):
        for name, cfg in ec.ENGINES.items():
            with self.subTest(engine=name):
                self.assertEqual(set(cfg.keys()), self.REQUIRED_KEYS)

    def test_no_extra_keys(self):
        for name, cfg in ec.ENGINES.items():
            with self.subTest(engine=name):
                extra = set(cfg.keys()) - self.REQUIRED_KEYS
                self.assertEqual(extra, set(), f"Unexpected keys: {extra}")

    def test_secret_names_known(self):
        for name, cfg in ec.ENGINES.items():
            with self.subTest(engine=name):
                self.assertIn(cfg["secret_name"], self.KNOWN_SECRETS)

    def test_unique_concurrency_prefixes(self):
        prefixes = [cfg["concurrency_prefix"] for cfg in ec.ENGINES.values()]
        self.assertEqual(len(prefixes), len(set(prefixes)))

    def test_versions_in_install_cmd(self):
        for name, cfg in ec.ENGINES.items():
            with self.subTest(engine=name):
                self.assertIn(cfg["agent_version"], cfg["install_cmd"])


class TestWriteOutputs(unittest.TestCase):
    """Tests for write_outputs() formatting."""

    def _capture_stdout(self, engine_id, config):
        old_env = os.environ.pop("GITHUB_OUTPUT", None)
        try:
            captured = io.StringIO()
            old_stdout = sys.stdout
            sys.stdout = captured
            ec.write_outputs(engine_id, config)
            sys.stdout = old_stdout
            return captured.getvalue()
        finally:
            if old_env is not None:
                os.environ["GITHUB_OUTPUT"] = old_env

    def test_key_value_format(self):
        """Short values use key=value format."""
        output = self._capture_stdout("test", {"engine_name": "Test", "secret_name": "S", "install_cmd": "x", "setup_node": "false"})
        self.assertIn("engine_name=Test", output)

    def test_derived_keys(self):
        """engine_id and detection_* keys are added."""
        output = self._capture_stdout("claude", ec.ENGINES["claude"])
        self.assertIn("engine_id=claude", output)
        self.assertIn("detection_install_cmd", output)
        self.assertIn("detection_secret_name", output)
        self.assertIn("detection_setup_node", output)

    def test_heredoc_for_long_values(self):
        """Values over 200 chars use heredoc delimiter."""
        long_val = "x" * 201
        output = self._capture_stdout("test", {"long_key": long_val, "secret_name": "S", "install_cmd": "x", "setup_node": "false"})
        self.assertIn("long_key<<GH_AW_EOF", output)
        self.assertIn("GH_AW_EOF", output)

    def test_heredoc_for_multiline_values(self):
        """Multiline values use heredoc delimiter."""
        output = self._capture_stdout("test", {"multi": "line1\nline2", "secret_name": "S", "install_cmd": "x", "setup_node": "false"})
        self.assertIn("multi<<GH_AW_EOF", output)

    def test_github_output_file_mode(self):
        """When GITHUB_OUTPUT is set, output goes to that file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            tmp_path = f.name
        try:
            os.environ["GITHUB_OUTPUT"] = tmp_path
            ec.write_outputs("claude", ec.ENGINES["claude"])
            with open(tmp_path) as f:
                content = f.read()
            self.assertIn("engine_id=claude", content)
        finally:
            del os.environ["GITHUB_OUTPUT"]
            os.unlink(tmp_path)

    def test_sorted_output(self):
        """Output keys appear in sorted order."""
        output = self._capture_stdout("claude", ec.ENGINES["claude"])
        keys = []
        in_heredoc = False
        for line in output.strip().split("\n"):
            if in_heredoc:
                if line == "GH_AW_EOF":
                    in_heredoc = False
                continue
            if "<<GH_AW_EOF" in line:
                keys.append(line.split("<<")[0])
                in_heredoc = True
            elif "=" in line:
                keys.append(line.split("=")[0])
        self.assertEqual(keys, sorted(keys))

    def test_no_delimiter_collision(self):
        """GH_AW_EOF does not appear in any real config value."""
        for name, cfg in ec.ENGINES.items():
            for key, val in cfg.items():
                with self.subTest(engine=name, key=key):
                    self.assertNotIn("GH_AW_EOF", str(val))


class TestMain(unittest.TestCase):
    """Tests for CLI entry point."""

    def test_valid_engines(self):
        """Each valid engine name succeeds."""
        for engine in ec.ENGINES:
            with self.subTest(engine=engine):
                old_env = os.environ.pop("GITHUB_OUTPUT", None)
                try:
                    old_argv = sys.argv
                    sys.argv = ["engine-config.py", "--engine", engine]
                    old_stdout = sys.stdout
                    sys.stdout = io.StringIO()
                    ec.main()
                    sys.stdout = old_stdout
                    sys.argv = old_argv
                finally:
                    if old_env is not None:
                        os.environ["GITHUB_OUTPUT"] = old_env

    def test_invalid_engine_exits(self):
        """An invalid engine name raises SystemExit."""
        old_argv = sys.argv
        old_stderr = sys.stderr
        sys.argv = ["engine-config.py", "--engine", "nonexistent"]
        sys.stderr = io.StringIO()
        with self.assertRaises(SystemExit):
            ec.main()
        sys.stderr = old_stderr
        sys.argv = old_argv

    def test_missing_engine_exits(self):
        """Missing --engine flag raises SystemExit."""
        old_argv = sys.argv
        old_stderr = sys.stderr
        sys.argv = ["engine-config.py"]
        sys.stderr = io.StringIO()
        with self.assertRaises(SystemExit):
            ec.main()
        sys.stderr = old_stderr
        sys.argv = old_argv


class TestSecurityCriticalValues(unittest.TestCase):
    """Tests for security-critical configuration values."""

    def test_permission_mode(self):
        """Claude agent CLI uses bypassPermissions mode."""
        self.assertIn("bypassPermissions", ec.CLAUDE_AGENT_CLI)

    def test_detection_tools_subset(self):
        """Detection allowed tools are a subset of agent tools
        plus Bash(cmd) variants."""
        detection = set(ec.CLAUDE_DETECTION_ALLOWED_TOOLS.split(","))
        agent = set(ec.CLAUDE_AGENT_ALLOWED_TOOLS.split(","))
        bash_variants = {t for t in detection if t.startswith("Bash(")}
        non_bash = detection - bash_variants
        self.assertTrue(
            non_bash.issubset(agent),
            f"Detection has tools not in agent set: {non_bash - agent}",
        )

    def test_key_name_consistency(self):
        """secret_name and secret_env_name match for each engine."""
        for name, cfg in ec.ENGINES.items():
            with self.subTest(engine=name):
                self.assertEqual(cfg["secret_name"], cfg["secret_env_name"])


class TestDomainAllowlists(unittest.TestCase):
    """Tests for domain allowlist configuration."""

    def test_no_wildcards_in_common(self):
        """Common domains contain no wildcards."""
        for domain in ec.COMMON_DOMAINS:
            self.assertNotIn("*", domain, f"Wildcard in common domain: {domain}")

    def test_claude_has_anthropic(self):
        """Claude extra domains include anthropic.com."""
        self.assertIn("anthropic.com", ec.CLAUDE_EXTRA_DOMAINS)

    def test_copilot_has_githubcopilot(self):
        """Copilot extra domains include a githubcopilot domain."""
        found = any("githubcopilot" in d for d in ec.COPILOT_EXTRA_DOMAINS)
        self.assertTrue(found, "No githubcopilot domain found in COPILOT_EXTRA_DOMAINS")

    def test_codex_has_openai(self):
        """Codex extra domains include openai.com."""
        self.assertIn("api.openai.com", ec.CODEX_EXTRA_DOMAINS)

    def test_engine_specific_domains_present(self):
        """Each engine's allowed_domains contains its extra domains."""
        for name, cfg in ec.ENGINES.items():
            with self.subTest(engine=name):
                domains = cfg["allowed_domains"].split(",")
                extra_name = f"{name.upper()}_EXTRA_DOMAINS"
                extra = getattr(ec, extra_name)
                for d in extra:
                    if "*" not in d:
                        self.assertIn(d, domains, f"{d} missing from {name} allowed_domains")


if __name__ == "__main__":
    unittest.main()

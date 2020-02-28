"""Tests for anf.deploymentmap."""

import unittest

from anf.deploymentmap import DeploymentMapMaker
from test_anf_deploymentmap.constants import DEFAULT_PF_NAME


class TestDeploymentMap(unittest.TestCase):
    """Test a deploymentmap."""

    def setUp(self) -> None:
        """Set up class for subsequent tests."""
        self.default_args = ["-d", "-p", DEFAULT_PF_NAME, "both", "both"]
        self.subject = DeploymentMapMaker(self.default_args)

    def test_run(self):
        """Test init including parameter file parsing."""

        self.subject.run()

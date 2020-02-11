"""Tests for anf.deploymentmap."""

import unittest

from anf.deploymentmap import DeploymentMapMaker


class TestDeploymentMap(unittest.TestCase):
    """Test a deploymentmap."""

    def test_run(self):
        """Test init including parameter file parsing."""
        args = ["-d", "-p", "usarray_deploy_map", "both", "both"]
        mapmaker = DeploymentMapMaker(args)
        assert mapmaker is not None
        mapmaker.run()
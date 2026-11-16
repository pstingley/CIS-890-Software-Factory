"""Tests for return-to-exit and exception handling in control-flow graphs."""

import unittest
from codeflow.analyzers.python_analyzer import analyze_python_file
from codeflow.graph import NodeType, EdgeType
import tempfile
import os


class TestReturnToExitConnections(unittest.TestCase):
    """Test that returns connect to Normal Exit."""
    
    def _analyze_function(self, source: str, func_name: str):
        """Helper to analyze a Python function."""
        fd, temp_path = tempfile.mkstemp(suffix='.py', text=True)
        try:
            os.write(fd, source.encode('utf-8'))
            os.close(fd)
            result = analyze_python_file(temp_path)
            return result.functions.get(func_name)
        finally:
            try:
                os.unlink(temp_path)
            except:
                pass
    
    def test_simple_return_to_exit(self):
        """Test that a simple return connects to Exit node."""
        source = 'def simple_return():\n    return 42\n'
        cfg = self._analyze_function(source, 'simple_return')
        self.assertIsNotNone(cfg, "Function should be analyzed")
        
        # Should have a Normal Exit node
        self.assertTrue(cfg.exit_node_ids, "Should have a Normal Exit node")
        
        # Check that at least one return connects to exit
        exit_node_id = cfg.exit_node_ids[0]
        edges_to_exit = [e for e in cfg.edges if e.target_id == exit_node_id]
        self.assertTrue(edges_to_exit, "Return should connect to Exit")
    
    def test_fall_through_to_exit(self):
        """Test that normal fall-through connects to Exit."""
        source = 'def fall_through():\n    x = 1\n    y = 2\n'
        cfg = self._analyze_function(source, 'fall_through')
        self.assertIsNotNone(cfg, "Function should be analyzed")
        
        # Should have a Normal Exit node
        self.assertTrue(cfg.exit_node_ids, "Should have a Normal Exit node")
        
        # Last statement should connect to exit
        exit_node_id = cfg.exit_node_ids[0]
        edges_to_exit = [e for e in cfg.edges if e.target_id == exit_node_id]
        self.assertTrue(edges_to_exit, "Fall-through should connect to Exit")
    
    def test_exception_exit_omitted_when_no_raise(self):
        """Test that Exception Exit is omitted when there are no raises."""
        source = 'def no_exceptions():\n    return 42\n'
        cfg = self._analyze_function(source, 'no_exceptions')
        self.assertIsNotNone(cfg, "Function should be analyzed")
        
        # Exception Exit should be empty
        self.assertEqual(len(cfg.exception_exit_node_ids), 0,
                        "Exception Exit should be omitted when no raises present")
    
    def test_exception_exit_present_for_raise(self):
        """Test that Exception Exit is present when there are raises."""
        source = 'def with_raise():\n    raise ValueError("error")\n'
        cfg = self._analyze_function(source, 'with_raise')
        self.assertIsNotNone(cfg, "Function should be analyzed")
        
        # Exception Exit should be present
        self.assertTrue(cfg.exception_exit_node_ids,
                       "Exception Exit should be present for function with raise")
        
        # Raise should create an edge
        self.assertTrue(cfg.edges, "Should have edges from raise statement")


class TestExceptionEdgeTypes(unittest.TestCase):
    """Test that exception edges have correct EdgeType."""
    
    def _analyze_function(self, source: str, func_name: str):
        """Helper to analyze a Python function."""
        fd, temp_path = tempfile.mkstemp(suffix='.py', text=True)
        try:
            os.write(fd, source.encode('utf-8'))
            os.close(fd)
            result = analyze_python_file(temp_path)
            return result.functions.get(func_name)
        finally:
            try:
                os.unlink(temp_path)
            except:
                pass
    
    def test_raise_has_exception_edge_type(self):
        """Test that raise statements create exception-type edges."""
        source = 'def test_raise():\n    raise ValueError()\n'
        cfg = self._analyze_function(source, 'test_raise')
        self.assertIsNotNone(cfg, "Function should be analyzed")
        
        # Find edges with EXCEPTION type
        exc_edges = [e for e in cfg.edges if e.edge_type == EdgeType.EXCEPTION]
        self.assertTrue(exc_edges, "Should have edges with EdgeType.EXCEPTION")


if __name__ == '__main__':
    unittest.main()

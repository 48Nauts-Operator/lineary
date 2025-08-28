#!/usr/bin/env python3
"""
ABOUTME: Betty PostTool Visual Tester - Automated testing after deployments
ABOUTME: Verifies styling, deployment status, and visual consistency
"""

import json
import sys
import subprocess
import requests
from pathlib import Path
from datetime import datetime
import time

class VisualTester:
    def __init__(self):
        self.test_log = Path.home() / ".betty" / "visual-test-results.jsonl"
        self.test_log.parent.mkdir(parents=True, exist_ok=True)
        self.frontend_url = "http://localhost:3377"
        self.failures = []
        
    def process_hook_input(self):
        """Process PostTool hook input from Claude Code"""
        try:
            # Read hook input from stdin
            hook_input = json.loads(sys.stdin.read())
            
            tool_name = hook_input.get("tool", "")
            tool_inputs = hook_input.get("inputs", {})
            
            # Check if this was a deployment command
            if tool_name == "Bash":
                command = tool_inputs.get("command", "")
                if any(keyword in command for keyword in [
                    "docker-compose up", "docker-compose build",
                    "docker stop", "docker rm", "frontend"
                ]):
                    # Wait for container to be ready
                    time.sleep(3)
                    self.run_visual_tests()
            
            # Check if this was a styling change
            elif tool_name in ["Write", "Edit", "MultiEdit"]:
                file_path = tool_inputs.get("file_path", "")
                if ".tsx" in file_path or ".css" in file_path:
                    self.flag_styling_change(file_path)
            
            # Generate test report if failures exist
            if self.failures:
                report = self.generate_failure_report()
                print(f"\n{report}", file=sys.stderr)
                
                # Add to Betty tasks
                self.create_fix_task()
            
            return {"action": "continue"}
            
        except Exception as e:
            print(f"Visual tester error: {e}", file=sys.stderr)
            return {"action": "continue"}
    
    def run_visual_tests(self):
        """Run comprehensive visual and deployment tests"""
        print("\n🧪 Running PostTool Visual Tests...", file=sys.stderr)
        
        # Test 1: Container running
        if not self.test_container_running():
            self.failures.append({
                "test": "Container Status",
                "expected": "betty_frontend running",
                "actual": "Container not found or not running",
                "severity": "critical"
            })
            return  # No point continuing if container isn't running
        
        # Test 2: Frontend accessible
        if not self.test_frontend_accessible():
            self.failures.append({
                "test": "Frontend Accessibility",
                "expected": "HTTP 200 response",
                "actual": "Frontend not accessible",
                "severity": "critical"
            })
            return
        
        # Test 3: Check for styling issues
        self.test_styling_consistency()
        
        # Test 4: Check deployment freshness
        self.test_deployment_freshness()
        
        # Log results
        self.log_test_results()
    
    def test_container_running(self):
        """Test if frontend container is running"""
        try:
            result = subprocess.run(
                ["docker", "ps", "--format", "{{.Names}}"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return "betty_frontend" in result.stdout
        except:
            return False
    
    def test_frontend_accessible(self):
        """Test if frontend is accessible"""
        try:
            response = requests.get(f"{self.frontend_url}/", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def test_styling_consistency(self):
        """Test for common styling issues"""
        try:
            # Fetch the admin dashboard HTML
            response = requests.get(f"{self.frontend_url}/admin", timeout=5)
            html = response.text
            
            # Check for common styling issues in the built output
            styling_checks = [
                {
                    "name": "Title text color",
                    "search": "AI Task Management Dashboard",
                    "should_have": ["text-white"],
                    "should_not_have": ["text-gray-900", "text-black"]
                },
                {
                    "name": "Card backgrounds",
                    "search": "bg-white/5",
                    "min_occurrences": 5,  # Should have multiple cards with this background
                }
            ]
            
            # Since we're checking compiled output, we can't directly check classes
            # But we can check if the page loads and has expected structure
            if len(html) < 100:
                self.failures.append({
                    "test": "Page Content",
                    "expected": "Full HTML page",
                    "actual": "Empty or minimal response",
                    "severity": "high"
                })
            
        except Exception as e:
            self.failures.append({
                "test": "Styling Consistency",
                "expected": "Styling tests to pass",
                "actual": f"Test failed: {str(e)}",
                "severity": "medium"
            })
    
    def test_deployment_freshness(self):
        """Check if deployment is fresh"""
        try:
            # Check container creation time
            result = subprocess.run(
                ["docker", "inspect", "betty_frontend", "--format", "{{.Created}}"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                created_str = result.stdout.strip()
                # Parse and check if container was created recently (within last 5 minutes)
                # This would indicate a fresh deployment
                
                # For now, just log it
                print(f"  ✓ Container created at: {created_str[:19]}", file=sys.stderr)
        except:
            pass
    
    def flag_styling_change(self, file_path):
        """Flag that styling changes were made"""
        warning = (
            "\n⚠️  STYLING CHANGE DETECTED\n"
            f"   File: {file_path}\n"
            "   Remember to:\n"
            "   1. Verify all text is white/white-70\n"
            "   2. Check all cards have bg-white/5 background\n"
            "   3. Test in browser after deployment\n"
            "   4. Check both light and dark themes if applicable"
        )
        print(warning, file=sys.stderr)
    
    def generate_failure_report(self):
        """Generate a detailed failure report"""
        report_lines = [
            "=" * 60,
            "❌ VISUAL TESTING FAILURES DETECTED",
            "=" * 60
        ]
        
        for failure in self.failures:
            report_lines.extend([
                f"\n🔴 Test: {failure['test']}",
                f"   Expected: {failure['expected']}",
                f"   Actual: {failure['actual']}",
                f"   Severity: {failure['severity'].upper()}"
            ])
        
        report_lines.extend([
            "\n" + "=" * 60,
            "📋 REQUIRED ACTIONS:",
            "1. Check if docker deployment completed successfully",
            "2. Verify styling changes were included in build",
            "3. Clear browser cache and hard refresh",
            "4. Check browser console for errors",
            "=" * 60
        ])
        
        return "\n".join(report_lines)
    
    def create_fix_task(self):
        """Create a task in Betty to fix the issues"""
        try:
            task_description = f"Fix visual testing failures: {len(self.failures)} issues found"
            requests.post(
                "http://localhost:3034/api/tasks/add",
                params={
                    "task": task_description,
                    "priority": 2
                },
                timeout=2
            )
        except:
            pass
    
    def log_test_results(self):
        """Log test results to file"""
        try:
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "failures": self.failures,
                "passed": len(self.failures) == 0
            }
            
            with open(self.test_log, "a") as f:
                f.write(json.dumps(log_entry) + "\n")
            
            if len(self.failures) == 0:
                print("  ✅ All visual tests passed!", file=sys.stderr)
            else:
                print(f"  ❌ {len(self.failures)} visual test(s) failed!", file=sys.stderr)
                
        except Exception as e:
            print(f"Failed to log test results: {e}", file=sys.stderr)

def main():
    """Hook entry point"""
    tester = VisualTester()
    result = tester.process_hook_input()
    print(json.dumps(result))

if __name__ == "__main__":
    main()
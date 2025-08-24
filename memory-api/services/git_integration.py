# ABOUTME: Git Integration Service for Enhanced Task Management System
# ABOUTME: Handles branch creation, commit tracking, PR management, and git workflow automation

import asyncio
import subprocess
import re
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
import structlog
from pathlib import Path

logger = structlog.get_logger(__name__)

class GitIntegrationService:
    """
    Service to integrate tasks with git operations
    """
    
    def __init__(self, repo_path: Optional[str] = None):
        self.repo_path = Path(repo_path or "/home/jarvis/projects/Betty")
        self.default_remote = "origin"
        
    async def create_task_branch(
        self,
        task_id: str,
        title: str,
        task_type: str,
        base_branch: str = "main",
        naming_convention: str = "feature"
    ) -> Dict[str, Any]:
        """
        Create a new git branch for a task
        """
        try:
            # Generate branch name
            branch_name = self._generate_branch_name(
                task_id=task_id,
                title=title,
                task_type=task_type,
                naming_convention=naming_convention
            )
            
            # Check if branch already exists
            existing_branches = await self._get_all_branches()
            if branch_name in existing_branches:
                return {
                    "branch_name": branch_name,
                    "base_branch": base_branch,
                    "created": False,
                    "remote_tracking": False,
                    "error": f"Branch {branch_name} already exists"
                }
            
            # Ensure we're on the base branch and it's up to date
            await self._checkout_and_update_branch(base_branch)
            
            # Create new branch
            create_result = await self._run_git_command([
                "checkout", "-b", branch_name
            ])
            
            if create_result["success"]:
                # Push to remote with tracking
                push_result = await self._run_git_command([
                    "push", "-u", self.default_remote, branch_name
                ])
                
                remote_tracking = push_result["success"]
                
                logger.info(
                    "Git branch created for task",
                    task_id=task_id,
                    branch_name=branch_name,
                    base_branch=base_branch,
                    remote_tracking=remote_tracking
                )
                
                return {
                    "branch_name": branch_name,
                    "base_branch": base_branch,
                    "created": True,
                    "remote_tracking": remote_tracking,
                    "error": None
                }
            else:
                return {
                    "branch_name": branch_name,
                    "base_branch": base_branch,
                    "created": False,
                    "remote_tracking": False,
                    "error": create_result["error"]
                }
                
        except Exception as e:
            logger.error(
                "Failed to create git branch",
                task_id=task_id,
                error=str(e)
            )
            return {
                "branch_name": None,
                "base_branch": base_branch,
                "created": False,
                "remote_tracking": False,
                "error": str(e)
            }
    
    async def track_commits_for_task(
        self,
        task_id: str,
        branch: str,
        since_timestamp: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Track all commits for a task's branch
        """
        try:
            # Get commits from the branch
            commits = await self._get_branch_commits(branch, since_timestamp)
            
            # Filter and format commits
            tracked_commits = []
            for commit in commits:
                # Check if commit message references the task
                if (task_id.lower() in commit["message"].lower() or 
                    branch in commit["branch"]):
                    
                    tracked_commits.append({
                        "task_id": task_id,
                        "commit_hash": commit["hash"],
                        "commit_message": commit["message"],
                        "author": commit["author"],
                        "branch": branch,
                        "files_changed": commit["files_changed"],
                        "lines_added": commit["lines_added"],
                        "lines_removed": commit["lines_removed"],
                        "commit_timestamp": commit["timestamp"],
                        "ai_generated": self._is_ai_generated_commit(commit["message"])
                    })
            
            logger.info(
                "Tracked commits for task",
                task_id=task_id,
                branch=branch,
                commit_count=len(tracked_commits)
            )
            
            return tracked_commits
            
        except Exception as e:
            logger.error(
                "Failed to track commits for task",
                task_id=task_id,
                branch=branch,
                error=str(e)
            )
            return []
    
    async def generate_commit_message(
        self,
        task_id: str,
        title: str,
        change_description: str,
        files_changed: List[str],
        task_type: str = "feature"
    ) -> str:
        """
        Generate an AI-optimized commit message for a task
        """
        try:
            # Analyze the type of changes
            change_type = self._analyze_change_type(files_changed, change_description)
            
            # Generate conventional commit format
            commit_prefix = self._get_commit_prefix(task_type, change_type)
            
            # Create concise but descriptive message
            commit_message = f"{commit_prefix}: {change_description}"
            
            # Add task reference
            if not task_id.lower() in commit_message.lower():
                commit_message += f"\n\nTask: {task_id}"
            
            # Add file context if significant
            if len(files_changed) <= 3:
                files_str = ", ".join([Path(f).name for f in files_changed])
                commit_message += f"\nFiles: {files_str}"
            elif len(files_changed) > 10:
                commit_message += f"\nFiles: {len(files_changed)} files modified"
            
            # Add AI generation marker
            commit_message += "\n\n🤖 Generated with Betty Task Management"
            
            return commit_message
            
        except Exception as e:
            logger.error(
                "Failed to generate commit message",
                task_id=task_id,
                error=str(e)
            )
            # Fallback to simple message
            return f"{task_type}: {change_description}\n\nTask: {task_id}"
    
    async def create_pull_request(
        self,
        task_id: str,
        task_title: str,
        branch: str,
        target_branch: str = "main",
        include_automated_tests: bool = True,
        reviewers: List[str] = None
    ) -> Dict[str, Any]:
        """
        Create a pull request for a task (using GitHub CLI if available)
        """
        try:
            # Check if gh CLI is available
            gh_available = await self._check_gh_cli()
            
            if not gh_available:
                return {
                    "url": None,
                    "title": task_title,
                    "description": "",
                    "labels": [],
                    "reviewers": reviewers or [],
                    "automated_checks": [],
                    "error": "GitHub CLI not available"
                }
            
            # Generate PR title and description
            pr_title = f"[{task_id}] {task_title}"
            pr_description = await self._generate_pr_description(
                task_id=task_id,
                task_title=task_title,
                branch=branch,
                target_branch=target_branch,
                include_automated_tests=include_automated_tests
            )
            
            # Create PR using GitHub CLI
            gh_command = [
                "gh", "pr", "create",
                "--title", pr_title,
                "--body", pr_description,
                "--base", target_branch,
                "--head", branch
            ]
            
            # Add labels
            labels = self._generate_pr_labels(task_id, task_title)
            if labels:
                gh_command.extend(["--label", ",".join(labels)])
            
            # Add reviewers
            if reviewers:
                gh_command.extend(["--reviewer", ",".join(reviewers)])
            
            result = await self._run_command(gh_command)
            
            if result["success"]:
                # Extract PR URL from output
                pr_url = result["output"].strip()
                
                logger.info(
                    "Pull request created for task",
                    task_id=task_id,
                    pr_url=pr_url,
                    branch=branch,
                    target_branch=target_branch
                )
                
                return {
                    "url": pr_url,
                    "title": pr_title,
                    "description": pr_description,
                    "labels": labels,
                    "reviewers": reviewers or [],
                    "automated_checks": await self._get_pr_checks(pr_url),
                    "error": None
                }
            else:
                return {
                    "url": None,
                    "title": pr_title,
                    "description": pr_description,
                    "labels": labels,
                    "reviewers": reviewers or [],
                    "automated_checks": [],
                    "error": result["error"]
                }
                
        except Exception as e:
            logger.error(
                "Failed to create pull request",
                task_id=task_id,
                error=str(e)
            )
            return {
                "url": None,
                "title": task_title,
                "description": "",
                "labels": [],
                "reviewers": reviewers or [],
                "automated_checks": [],
                "error": str(e)
            }
    
    async def validate_merge_readiness(
        self,
        task_id: str,
        branch: str,
        target_branch: str = "main"
    ) -> Dict[str, Any]:
        """
        Validate if a task branch is ready for merging
        """
        try:
            validation_results = []
            
            # Check if branch is up to date with target
            behind_commits = await self._check_branch_behind(branch, target_branch)
            if behind_commits > 0:
                validation_results.append({
                    "check_name": "branch_up_to_date",
                    "passed": False,
                    "message": f"Branch is {behind_commits} commits behind {target_branch}",
                    "severity": "warning",
                    "auto_fixable": True
                })
            else:
                validation_results.append({
                    "check_name": "branch_up_to_date",
                    "passed": True,
                    "message": "Branch is up to date",
                    "severity": "info",
                    "auto_fixable": False
                })
            
            # Check for merge conflicts
            conflicts = await self._check_merge_conflicts(branch, target_branch)
            validation_results.append({
                "check_name": "merge_conflicts",
                "passed": not conflicts,
                "message": "No merge conflicts" if not conflicts else "Merge conflicts detected",
                "severity": "error" if conflicts else "info",
                "auto_fixable": False
            })
            
            # Check if all commits are pushed
            unpushed = await self._check_unpushed_commits(branch)
            validation_results.append({
                "check_name": "commits_pushed",
                "passed": not unpushed,
                "message": "All commits pushed" if not unpushed else f"{unpushed} unpushed commits",
                "severity": "warning" if unpushed else "info",
                "auto_fixable": True
            })
            
            # Calculate overall readiness
            critical_failures = [v for v in validation_results if v["severity"] == "error" and not v["passed"]]
            ready_to_merge = len(critical_failures) == 0
            
            remaining_requirements = [
                v["message"] for v in validation_results 
                if not v["passed"] and v["severity"] in ["error", "warning"]
            ]
            
            logger.info(
                "Merge validation completed",
                task_id=task_id,
                branch=branch,
                ready_to_merge=ready_to_merge,
                requirements_count=len(remaining_requirements)
            )
            
            return {
                "ready_to_merge": ready_to_merge,
                "validation_results": validation_results,
                "remaining_requirements": remaining_requirements,
                "conflicts_detected": conflicts,
                "checks_passing": len(critical_failures) == 0
            }
            
        except Exception as e:
            logger.error(
                "Failed to validate merge readiness",
                task_id=task_id,
                branch=branch,
                error=str(e)
            )
            return {
                "ready_to_merge": False,
                "validation_results": [],
                "remaining_requirements": [f"Validation failed: {str(e)}"],
                "conflicts_detected": True,
                "checks_passing": False
            }
    
    # =============================================================================
    # PRIVATE HELPER METHODS
    # =============================================================================
    
    def _generate_branch_name(
        self,
        task_id: str,
        title: str,
        task_type: str,
        naming_convention: str
    ) -> str:
        """Generate a standardized branch name"""
        # Clean title for branch name
        clean_title = re.sub(r'[^a-zA-Z0-9\s-]', '', title)
        clean_title = re.sub(r'\s+', '-', clean_title.strip())
        clean_title = clean_title.lower()[:40]  # Limit length
        
        # Format: type/TASK-ID-title
        if naming_convention == "feature":
            return f"{task_type}/{task_id}-{clean_title}"
        elif naming_convention == "conventional":
            return f"{task_type}-{task_id}-{clean_title}"
        else:
            return f"task-{task_id}-{clean_title}"
    
    async def _run_git_command(self, args: List[str]) -> Dict[str, Any]:
        """Run a git command and return result"""
        return await self._run_command(["git"] + args, cwd=self.repo_path)
    
    async def _run_command(self, args: List[str], cwd: Optional[Path] = None) -> Dict[str, Any]:
        """Run a shell command asynchronously"""
        try:
            process = await asyncio.create_subprocess_exec(
                *args,
                cwd=cwd or self.repo_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            return {
                "success": process.returncode == 0,
                "output": stdout.decode() if stdout else "",
                "error": stderr.decode() if stderr else "",
                "return_code": process.returncode
            }
            
        except Exception as e:
            return {
                "success": False,
                "output": "",
                "error": str(e),
                "return_code": -1
            }
    
    async def _get_all_branches(self) -> List[str]:
        """Get list of all branches"""
        result = await self._run_git_command(["branch", "-a"])
        if result["success"]:
            branches = []
            for line in result["output"].split('\n'):
                line = line.strip()
                if line and not line.startswith('*'):
                    # Remove remote prefix if present
                    branch = line.replace('remotes/origin/', '')
                    if branch not in branches:
                        branches.append(branch)
            return branches
        return []
    
    async def _checkout_and_update_branch(self, branch: str):
        """Checkout and update a branch"""
        # Checkout branch
        await self._run_git_command(["checkout", branch])
        
        # Pull latest changes
        await self._run_git_command(["pull", self.default_remote, branch])
    
    async def _get_branch_commits(
        self,
        branch: str,
        since: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Get commits from a branch"""
        git_args = [
            "log", branch, 
            "--pretty=format:%H|%an|%ad|%s", 
            "--date=iso",
            "--numstat"
        ]
        
        if since:
            git_args.append(f"--since={since.isoformat()}")
        
        result = await self._run_git_command(git_args)
        
        commits = []
        if result["success"]:
            # Parse git log output
            # This is a simplified parser - would need more robust implementation
            for line in result["output"].split('\n'):
                if '|' in line:
                    parts = line.split('|')
                    if len(parts) >= 4:
                        commits.append({
                            "hash": parts[0],
                            "author": parts[1],
                            "timestamp": parts[2],
                            "message": parts[3],
                            "branch": branch,
                            "files_changed": 0,  # Would be parsed from numstat
                            "lines_added": 0,
                            "lines_removed": 0
                        })
        
        return commits
    
    def _is_ai_generated_commit(self, message: str) -> bool:
        """Check if commit message appears to be AI-generated"""
        ai_markers = [
            "🤖",
            "Generated with Betty",
            "Generated with Claude",
            "AI-generated",
            "Betty Task Management"
        ]
        return any(marker in message for marker in ai_markers)
    
    def _analyze_change_type(self, files: List[str], description: str) -> str:
        """Analyze the type of changes being made"""
        # Check file types
        has_tests = any('test' in f.lower() or 'spec' in f.lower() for f in files)
        has_docs = any(f.endswith('.md') or 'doc' in f.lower() for f in files)
        has_config = any(f.endswith(('.json', '.yaml', '.yml', '.toml')) for f in files)
        
        # Check description keywords
        desc_lower = description.lower()
        
        if 'fix' in desc_lower or 'bug' in desc_lower:
            return 'fix'
        elif has_tests or 'test' in desc_lower:
            return 'test'
        elif has_docs or 'doc' in desc_lower:
            return 'docs'
        elif has_config or 'config' in desc_lower:
            return 'config'
        elif 'refactor' in desc_lower:
            return 'refactor'
        else:
            return 'feat'
    
    def _get_commit_prefix(self, task_type: str, change_type: str) -> str:
        """Get conventional commit prefix"""
        prefix_map = {
            'feature': 'feat',
            'bug': 'fix',
            'enhancement': 'feat',
            'refactor': 'refactor',
            'test': 'test',
            'docs': 'docs'
        }
        
        return prefix_map.get(task_type, change_type)
    
    async def _check_gh_cli(self) -> bool:
        """Check if GitHub CLI is available"""
        result = await self._run_command(["gh", "--version"])
        return result["success"]
    
    async def _generate_pr_description(
        self,
        task_id: str,
        task_title: str,
        branch: str,
        target_branch: str,
        include_automated_tests: bool
    ) -> str:
        """Generate PR description"""
        description = f"""## Task: {task_id}

### Summary
{task_title}

### Changes
- Implementation details will be filled automatically
- Branch: `{branch}` → `{target_branch}`

### Testing
"""
        
        if include_automated_tests:
            description += "- [ ] Automated tests pass\n"
            description += "- [ ] Code coverage maintained\n"
        
        description += """- [ ] Manual testing completed
- [ ] Edge cases considered

### Checklist
- [ ] Code follows project standards
- [ ] Documentation updated if needed
- [ ] No breaking changes or clearly documented
- [ ] Performance impact considered

---
🤖 Generated with Betty Enhanced Task Management System
"""
        
        return description
    
    def _generate_pr_labels(self, task_id: str, title: str) -> List[str]:
        """Generate appropriate labels for PR"""
        labels = []
        
        title_lower = title.lower()
        
        if 'fix' in title_lower or 'bug' in title_lower:
            labels.append('bug')
        elif 'feat' in title_lower or 'feature' in title_lower:
            labels.append('enhancement')
        elif 'doc' in title_lower:
            labels.append('documentation')
        elif 'test' in title_lower:
            labels.append('testing')
        elif 'refactor' in title_lower:
            labels.append('refactoring')
        
        # Add task management label
        labels.append('betty-task')
        
        return labels
    
    async def _get_pr_checks(self, pr_url: str) -> List[Dict[str, Any]]:
        """Get automated checks for a PR (placeholder)"""
        # This would integrate with GitHub's checks API
        return [
            {
                "name": "CI/CD Pipeline",
                "status": "pending",
                "description": "Running automated tests and builds",
                "details_url": None
            }
        ]
    
    async def _check_branch_behind(self, branch: str, target_branch: str) -> int:
        """Check how many commits a branch is behind target"""
        result = await self._run_git_command([
            "rev-list", "--count", f"{branch}..{target_branch}"
        ])
        
        if result["success"]:
            try:
                return int(result["output"].strip())
            except ValueError:
                return 0
        return 0
    
    async def _check_merge_conflicts(self, branch: str, target_branch: str) -> bool:
        """Check if there would be merge conflicts"""
        # This is a simplified check - would need more sophisticated implementation
        result = await self._run_git_command([
            "merge-tree", 
            f"$(git merge-base {branch} {target_branch})",
            branch,
            target_branch
        ])
        
        return result["success"] and "<<<<<<< " in result["output"]
    
    async def _check_unpushed_commits(self, branch: str) -> int:
        """Check for unpushed commits"""
        result = await self._run_git_command([
            "rev-list", "--count", f"origin/{branch}..{branch}"
        ])
        
        if result["success"]:
            try:
                return int(result["output"].strip())
            except ValueError:
                return 0
        return 0
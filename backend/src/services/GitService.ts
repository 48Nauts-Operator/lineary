// ABOUTME: Git service for managing worktrees and branches
// ABOUTME: Automatically creates branches and worktrees for each issue

import simpleGit, { SimpleGit } from 'simple-git';
import { promises as fs } from 'fs';
import path from 'path';
import slugify from 'slugify';

export interface WorktreeInfo {
  branch: string;
  path: string;
  head: string;
}

export class GitService {
  private git: SimpleGit;
  private worktreesBasePath: string;
  
  constructor(repoPath: string = process.cwd()) {
    this.git = simpleGit(repoPath);
    this.worktreesBasePath = path.join(repoPath, 'worktrees');
  }
  
  async initialize(): Promise<void> {
    // Ensure worktrees directory exists
    try {
      await fs.mkdir(this.worktreesBasePath, { recursive: true });
    } catch (error) {
      console.error('Failed to create worktrees directory:', error);
    }
    
    // Verify git repository
    const isRepo = await this.git.checkIsRepo();
    if (!isRepo) {
      throw new Error('Not a git repository');
    }
  }
  
  async createIssueWorktree(issueId: string, title: string): Promise<{ branch: string; path: string }> {
    const branchName = this.generateBranchName(issueId, title);
    const worktreePath = path.join(this.worktreesBasePath, branchName);
    
    try {
      // Check if branch already exists
      const branches = await this.git.branch();
      const branchExists = branches.all.includes(branchName);
      
      if (!branchExists) {
        // Create new branch from main
        await this.git.checkoutBranch(branchName, 'main');
        await this.git.checkout('main'); // Switch back to main
      }
      
      // Check if worktree already exists
      const worktrees = await this.listWorktrees();
      const worktreeExists = worktrees.some(w => w.branch === branchName);
      
      if (!worktreeExists) {
        // Add worktree
        await this.git.raw(['worktree', 'add', worktreePath, branchName]);
      }
      
      return {
        branch: branchName,
        path: worktreePath
      };
    } catch (error) {
      console.error('Failed to create worktree:', error);
      throw error;
    }
  }
  
  async removeIssueWorktree(issueId: string, title: string): Promise<void> {
    const branchName = this.generateBranchName(issueId, title);
    const worktreePath = path.join(this.worktreesBasePath, branchName);
    
    try {
      // Remove worktree
      await this.git.raw(['worktree', 'remove', worktreePath, '--force']);
      
      // Delete branch if it's not the current branch
      const currentBranch = await this.git.revparse(['--abbrev-ref', 'HEAD']);
      if (currentBranch !== branchName) {
        await this.git.deleteLocalBranch(branchName, true);
      }
    } catch (error) {
      console.error('Failed to remove worktree:', error);
      // Ignore errors as worktree might not exist
    }
  }
  
  async listWorktrees(): Promise<WorktreeInfo[]> {
    try {
      const output = await this.git.raw(['worktree', 'list', '--porcelain']);
      const worktrees: WorktreeInfo[] = [];
      const lines = output.split('\n');
      
      let current: Partial<WorktreeInfo> = {};
      
      for (const line of lines) {
        if (line.startsWith('worktree ')) {
          if (current.path) {
            worktrees.push(current as WorktreeInfo);
          }
          current = { path: line.substring(9) };
        } else if (line.startsWith('HEAD ')) {
          current.head = line.substring(5);
        } else if (line.startsWith('branch ')) {
          current.branch = line.substring(7);
        }
      }
      
      if (current.path) {
        worktrees.push(current as WorktreeInfo);
      }
      
      return worktrees;
    } catch (error) {
      console.error('Failed to list worktrees:', error);
      return [];
    }
  }
  
  async getDiff(branch: string, baseBranch: string = 'main'): Promise<string> {
    try {
      const diff = await this.git.diff([`${baseBranch}...${branch}`]);
      return diff;
    } catch (error) {
      console.error('Failed to get diff:', error);
      return '';
    }
  }
  
  async getChangedFiles(branch: string, baseBranch: string = 'main'): Promise<string[]> {
    try {
      const diff = await this.git.diff([`${baseBranch}...${branch}`, '--name-only']);
      return diff.split('\n').filter(file => file.length > 0);
    } catch (error) {
      console.error('Failed to get changed files:', error);
      return [];
    }
  }
  
  async commitChanges(
    worktreePath: string,
    message: string,
    files?: string[]
  ): Promise<string> {
    const worktreeGit = simpleGit(worktreePath);
    
    try {
      // Add files
      if (files && files.length > 0) {
        await worktreeGit.add(files);
      } else {
        await worktreeGit.add('.');
      }
      
      // Commit
      const result = await worktreeGit.commit(message);
      return result.commit;
    } catch (error) {
      console.error('Failed to commit changes:', error);
      throw error;
    }
  }
  
  async pushBranch(branch: string, remote: string = 'origin'): Promise<void> {
    try {
      await this.git.push(remote, branch);
    } catch (error) {
      console.error('Failed to push branch:', error);
      throw error;
    }
  }
  
  async createPullRequest(
    branch: string,
    title: string,
    description: string,
    baseBranch: string = 'main'
  ): Promise<{ url: string }> {
    // This would integrate with GitHub/GitLab API
    // For now, return a placeholder
    console.log(`Creating PR: ${title} (${branch} -> ${baseBranch})`);
    
    return {
      url: `https://github.com/repo/pull/new/${branch}`
    };
  }
  
  private generateBranchName(issueId: string, title: string): string {
    const slug = slugify(title, {
      lower: true,
      strict: true,
      trim: true
    });
    
    // Limit branch name length
    const maxSlugLength = 50;
    const truncatedSlug = slug.substring(0, maxSlugLength);
    
    return `issue/${issueId}-${truncatedSlug}`;
  }
  
  async getCommitHistory(branch: string, limit: number = 10): Promise<any[]> {
    try {
      const log = await this.git.log({
        from: 'main',
        to: branch,
        maxCount: limit
      });
      
      return log.all;
    } catch (error) {
      console.error('Failed to get commit history:', error);
      return [];
    }
  }
  
  async mergeBranch(
    branch: string,
    targetBranch: string = 'main',
    squash: boolean = false
  ): Promise<void> {
    try {
      await this.git.checkout(targetBranch);
      
      if (squash) {
        await this.git.merge([branch, '--squash']);
        await this.git.commit(`Merge ${branch} into ${targetBranch}`);
      } else {
        await this.git.merge([branch]);
      }
    } catch (error) {
      console.error('Failed to merge branch:', error);
      throw error;
    }
  }
}
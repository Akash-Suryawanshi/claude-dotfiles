# Analyze Git Changes and Plan Feature Commits

Analyze the current git repository's staged and unstaged changes, intelligently group files by feature/functionality, and present a commit plan with one feature per commit.

## Instructions

1. **Get Current Branch**: Run `git rev-parse --abbrev-ref HEAD` to get the branch name (JIRA ticket ID)

2. **Analyze Changes**:
   - Run `git status --short` to see all changes
   - Run `git diff --cached --stat` for staged changes
   - Run `git diff HEAD --stat` for all changes including unstaged
   - Run `git diff --cached` and `git diff HEAD` to see actual code changes if needed for better grouping

3. **Intelligent File Grouping**:
   Group related files by feature area using these heuristics:
   - **Path-based**: Files in same directory/module (e.g., `src/auth/*` → authentication feature)
   - **Naming patterns**: Similar prefixes/suffixes (e.g., `user_*.py` → user management)
   - **File types**: Related functionality (e.g., `*.test.js` with `*.js` → testing updates)
   - **Logical relationships**: Config files with their implementations, models with their migrations, etc.
   - **Common features**: Authentication, API endpoints, UI components, database, tests, config, documentation

4. **Generate Commit Plan**:
   For each feature group, create:
   - **Feature name**: Clear, concise description
   - **File list**: All files in this commit
   - **Commit message**: Use format `<branch_name>:- <message>`
     - Message should be 1 line
     - Focus on "why" not "what"
     - Professional and concise (e.g., "Add thread-safe progress tracking", "Fix authentication flow in worker threads")
     - NO Claude Code credits

5. **Author Configuration**:
   - Author: akash-ezzz <akash.sur@imerit.net>
   - Set using: `git commit -m "<message>" --author="akash-ezzz <akash.sur@imerit.net>"`

6. **Output Format**:
   Present the commit plan clearly:
   ```
   ## Commit Plan for Branch: <branch-name>

   ### Commit 1: <Feature Name>
   Files:
   - path/to/file1.py
   - path/to/file2.js

   Commit command:
   git add <files>
   git commit -m "<branch-name>:- <commit message>" --author="akash-ezzz <akash.sur@imerit.net>"

   ### Commit 2: <Feature Name>
   ...
   ```

## Important Notes
- If changes are unrelated, suggest separate commits
- If changes are tightly coupled, group into one commit
- Aim for 1-3 commits typically (avoid over-splitting or under-splitting)
- Each commit should be atomic and functional
- DO NOT include "\🤖 Generated with Claude Code" or similar credits

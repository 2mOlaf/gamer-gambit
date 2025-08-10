# Branch Protection Setup Guide

## GitHub Branch Protection Rules

### Main Branch (Production)
- Navigate to: https://github.com/2mOlaf/gamer-gambit/settings/branches
- Add rule for 'main' branch:
  ✅ Require pull request reviews before merging
  ✅ Require status checks to pass before merging
  ✅ Require branches to be up to date before merging
  ✅ Include administrators
  ✅ Allow force pushes (for hotfixes only)

### Develop Branch (Staging)  
- Add rule for 'develop' branch:
  ✅ Require pull request reviews before merging
  ✅ Require status checks to pass before merging
  ✅ Allow force pushes

## Workflow
1. **Feature Development**:
   - Create feature branch from 'develop'
   - Make changes and test locally
   - Push to GitHub and create PR to 'develop'

2. **Staging Testing**:
   - PR to 'develop' triggers test environment deployment
   - Test bot functionality on test Discord server
   - Merge PR after testing

3. **Production Release**:
   - Create PR from 'develop' to 'main'
   - Review and approve changes
   - Merge triggers production deployment
   - Production bot automatically restarts with new code

## Environment Mapping
- **main** → Production Discord server (gamer-gambit namespace)
- **develop** → Test Discord server (gamer-gambit-test namespace)
- **feature/*** → Local development/testing

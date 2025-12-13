# GitHub Repository Rename Instructions

This document provides step-by-step instructions for renaming the GitHub repository from `code-graph-rag` to `weavr`.

## Prerequisites

- All code changes have been completed (package name, imports, CLI commands, documentation)
- All tests pass: `uv run pytest`
- All CLI commands work: `weavr --help`, `weavr index`, `weavr chat`, `weavr mcp`, `weavr http`
- You have admin access to the GitHub repository

## Repository Rename Steps

### Step 1: Verify Code Changes Are Complete

Before renaming the repository, verify that all code changes are in place:

```bash
# Verify CLI command works
weavr --help

# Verify imports work
python -c "from weavr.services import GraphService; print('Imports OK')"

# Run full test suite
uv run pytest

# Check for any remaining old references in code (not docs/git history)
rg "codebase_rag" weavr/ --type py  # Should return no results
rg "code-graph-rag" weavr/ --type py  # Should return no results
```

### Step 2: Update Local Git Configuration (Optional)

Update your local git remote to prepare for the new repository name:

```bash
# Check current remote
git remote -v

# After the GitHub rename, update your local remote:
git remote set-url origin https://github.com/username/weavr.git
```

### Step 3: Rename Repository on GitHub

1. Go to the repository settings page
   - Navigate to `https://github.com/username/code-graph-rag/settings`

2. Scroll down to the "Danger Zone" section

3. Click on "Rename this repository"

4. In the text field, replace `code-graph-rag` with `weavr`

5. Click "Rename" to confirm

### Step 4: Verify the Rename

After renaming, GitHub will automatically:
- Redirect the old URL to the new one
- Update repository URLs in your local git configuration
- Preserve all git history, issues, pull requests, and wiki content

### Step 5: Update Local Repository (If Needed)

If you cloned from the old URL, update your local configuration:

```bash
# Check your current remote
git remote -v

# The remote should now point to the new URL:
# origin  https://github.com/username/weavr.git (fetch)
# origin  https://github.com/username/weavr.git (push)

# If not, update it manually:
git remote set-url origin https://github.com/username/weavr.git

# Verify the update
git remote -v
```

### Step 6: Update Documentation Links

Update any documentation that references the repository URL:

1. **README.md**: Update repository URL in any installation or setup instructions
2. **CONTRIBUTING.md**: Update clone URL in contribution guidelines
3. **CI/CD workflows**: Update any hardcoded repository names in GitHub Actions workflows
4. **External documentation**: Update any links on external websites or documentation

### Step 7: Verify CI/CD and Workflows

1. Check that GitHub Actions workflows still trigger correctly
2. Verify that any webhook integrations still work
3. Test that the build pipeline completes successfully

## What Gets Preserved

When you rename a GitHub repository:

- ✅ All git history and commits
- ✅ All branches (including protected branches)
- ✅ All releases and tags
- ✅ All pull requests and their discussion
- ✅ All issues and their discussion
- ✅ All wiki pages and README
- ✅ GitHub Pages configuration (if enabled)
- ✅ All repository settings and permissions

## What Gets Updated Automatically

GitHub automatically handles:

- ✅ URL redirects from old name to new name (for 12 months)
- ✅ Dependency references in dependent repositories (if you use GitHub package registry)
- ✅ SSH keys and SSH clone URLs
- ✅ Repository links in profile
- ✅ Starring and watching records

## What Requires Manual Updates

You may need to update:

- ❌ Local git clones (update remote URL)
- ❌ External links in documentation
- ❌ CI/CD pipelines outside of GitHub Actions
- ❌ Scripts that reference the repository name
- ❌ Package manager references (PyPI, etc.)

## Package Manager Updates

If the package is published to PyPI or other package managers:

### PyPI (Python Package Index)

1. The PyPI package name is already updated to `weavr`
2. Old package `graph-code` remains archived (optional deprecation notice)
3. Users must update their installation commands:

```bash
# Old
pip install graph-code

# New
pip install weavr
# or for development
pip install -e .
```

## Rollback (If Needed)

If you need to revert the rename:

1. Go back to repository settings
2. Click "Rename this repository" again
3. Change the name back to `code-graph-rag`
4. Update local clones

**Note**: Rollback is recommended only within the first 12 months, as GitHub maintains redirects for that period.

## Timeline

- **Before Rename**: All code changes completed and tested
- **Rename Day**: Repository renamed on GitHub
- **After Rename**: Documentation and links updated, CI/CD verified
- **12 Months**: Old URL redirects expire (not critical, but good to know)

## Verification Checklist

After completing the rename:

- [ ] Old repository URL redirects to new URL
- [ ] New repository URL is accessible
- [ ] Local git clone works with new URL
- [ ] All GitHub Actions workflows trigger and pass
- [ ] All issues and PRs are accessible
- [ ] Wiki and README display correctly
- [ ] Documentation links are updated
- [ ] Package manager shows new package name
- [ ] CI/CD pipeline completes successfully
- [ ] All tests pass in new repository

## Troubleshooting

### Issue: Git push fails after rename

**Solution**: Update your local remote URL:
```bash
git remote set-url origin https://github.com/username/weavr.git
```

### Issue: Old URL still shows in some places

**Solution**: GitHub maintains redirects for 12 months. Wait a moment and try again, or manually update the URL.

### Issue: Webhooks or integrations fail

**Solution**:
1. Check webhook configuration in repository settings
2. GitHub automatically updates webhooks that reference the repository
3. For external integrations, update the repository URL in the integration settings

### Issue: Package manager still shows old name

**Solution**:
- For PyPI: The new package `weavr` is already published
- Remove the old `graph-code` from your requirements
- Update to `weavr`

---

## Additional Resources

- [GitHub: Renaming a repository](https://docs.github.com/en/repositories/creating-and-managing-repositories/renaming-a-repository)
- [GitHub: Redirects and the old repository name](https://docs.github.com/en/repositories/creating-and-managing-repositories/renaming-a-repository#about-redirects-for-renamed-repositories)

## Support

If you encounter issues:

1. Check the GitHub documentation linked above
2. Review this document's troubleshooting section
3. Verify all code changes are in place
4. Confirm all tests pass before and after rename

---

**Next Steps**:

After repository rename is complete:

1. Update any external documentation or links
2. Announce the rename to users (if applicable)
3. Update CI/CD pipelines in other repositories that depend on this one
4. Monitor for any integration issues in the first week

For more information, see:
- [MIGRATION.md](MIGRATION.md) - User and developer migration guide
- [README.md](README.md) - Project overview
- [CONTRIBUTING.md](CONTRIBUTING.md) - Contribution guidelines

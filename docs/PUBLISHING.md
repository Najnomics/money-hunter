# Publishing Money Hunter

`money-hunter` is its own repository. It is not part of the `bugbounty-intel`
repository, and the intel corpus is never vendored here.

## What is already done

The canonical remote is [Najnomics/money-hunter](https://github.com/Najnomics/money-hunter).

```bash
git log --oneline -1
git status
```

## Create the remote and push

```bash
git remote add money https://github.com/Najnomics/money-hunter.git
git push -u money HEAD:main
```

## What is intentionally excluded

`.gitignore` excludes:

- `.apex/` — per-target campaign state and exploit evidence
- `bugbounty-intel/` and `intel/` — the corpus is cloned separately
- `.venv/`, caches, logs

Confirm before pushing:

```bash
git status --short
git ls-files | grep -E 'bugbounty-intel|\.apex/' || echo "clean"
```

## How teammates get the latest intel

They clone the tool once, then:

```bash
./scripts/sync-intel.sh
```

That clones or fast-forwards:

```text
~/.apex/intel/bugbounty-intel
```

`check_intel` reports the corpus revision and commit date in its notes, so a
stale clone is visible in the campaign output.

If the corpus repository moves, set:

```bash
export APEX_INTEL_REPO=git@github.com:<org>/bugbounty-intel.git
```

## Release flow

Recommended:

1. Commit changes to `main`.
2. Tag a version when the tool contract changes:
   ```bash
   git tag -a v0.2.0 -m "Coverage loop and feedback tool"
   git push origin main --tags
   ```
3. Teammates update with:
   ```bash
   git pull
   ./scripts/setup.sh --skip-install
   ```

Campaign state is in each target's `.apex/`, so updating the tool never deletes
a campaign.

## Do not

- Commit a target’s `.apex/` folder.
- Commit the 53 MB intel corpus.
- Force-push `main` after teammates have campaigns pinned to it.
- Publish exploit evidence in the tool repository.

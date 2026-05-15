# fix-non-ascii
Pre-commit hook to fix and validate non-ASCII characters in source files

```yaml
- repo: https://github.com/sethrj/fix-non-ascii
  rev: <rev>
  hooks:
    - id: fix-non-ascii
```

The bundled hook keeps the original Celeritas file matcher:
`\.(cc|hh|cu|cmake)$|CMakeLists\.txt$`. Override `files:` in your
`.pre-commit-config.yaml` if you want to target different file types.

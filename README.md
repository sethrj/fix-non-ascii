# fix-non-ascii

[Pre-commit](https://pre-commit.com) hook to validate and fix non-ASCII
characters in source files.

```yaml
- repo: https://github.com/sethrj/fix-non-ascii
  rev: v1.0.0
  hooks:
    - id: fix-non-ascii
      files: '\.(cc|hh|cu)' # optional
```

The bundled hook matches C, C++, CUDA, and CMake files by default: see the
pre-commit documentation for additional options under 'hooks'.

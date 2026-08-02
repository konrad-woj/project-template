# Project Template

> TL;DR:

## TOC


## 📚 Documentation

See [openwiki/index.md](openwiki/index.md) for the full repository wiki (architecture, design, operations, and per-package docs), kept up to date by OpenWiki.

## Installation


## Usage
### Getting Started


### Examples


### API Reference


### Guardrails

`claude-sandbox.sb` is a macOS Seatbelt profile that blocks Claude Code (or any wrapped process) from reading credentials — SSH keys, `.aws/`, `.gcp/`, `.azure/`, `.env` files, etc. — even if it tries to `cat` or `Read` them directly.

Run any command sandboxed with `sandbox-exec`:

```sh
sandbox-exec -f claude-sandbox.sb <command> [args...]
```

For example, to launch Claude Code itself under the profile:

```sh
sandbox-exec -f claude-sandbox.sb claude
```

Note: `sandbox-exec` is deprecated by Apple (no replacement CLI has shipped as of macOS 15), but it remains functional and is still the standard way to apply a custom Seatbelt profile from the command line.

### Evaluation


## License


## Contributing


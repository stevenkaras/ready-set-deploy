# Ready-Set-Deploy!

RSD is a deployment framework designed to use set theory to issue the least number of commands to bring a system to a desired state.

# Usage

```bash
rsd validate state.json
rsd gather PROVIDER.ID > provider_state.json
rsd gather ALL > host_state.json
rsd diff --from host_state.json --to role_state.json > plan.json
rsd commands plan.json

# Altogehter now
bash -x <(rsd commands <(rsd diff --from <(rsd gather PROVIDER.ID) --to role_state.json ) )
```

# Design

RSD uses a three phase process: fact gathering, diff, and execution.
Plugins provide functionality for all three phases, although each come with defaults.

The main design goal is minimal computational effort.

Feature goals (some out of scope for the core project):

* Modular plugin system

# v1.0.0 Progress

- [ ] CLI Interface
    - [x] gather
    - [x] gather ALL
    - [x] diff
    - [ ] commands
    - [ ] validate
- [x] Modular providers

Example providers:

- [ ] Homebrew
- [ ] APT
- [ ] ASDF
- [ ] IPTables
- [ ] File content
- [ ] Docker
- [ ] Pip
- [ ] Pipx

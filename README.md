# Ready-Set-Deploy!

RSD is a deployment framework designed to work offline-first without a centralized controller.
RSD is not an execution framework, nor does it specify how desired state is defined.

# Usage

```bash
rsd validate role_state.json
rsd gather PROVIDER1.ID > provider1_state.json
rsd gather PROVIDER2.ID > provider2_state.json
rsd combine provider1_state.json provider2_state.json > host_state.json
rsd diff host_state.json role_state.json > plan.json
rsd commands plan.json

# As individual steps
bash -x <(rsd diff <(rsd providers role_state.json | rsd gather-all) role_state.json | rsd commands -)
# Or all together in a single command
bash -x <(rsd apply role_state.json)
```

# Design

RSD uses a three phase process: fact gathering, diff, and execution.
Plugins provide functionality for all three phases, although each come with defaults.

The main design goal is minimal computational effort.

Feature goals (some out of scope for the core project):

* Modular plugin system

# v1.0 Progress

- [x] CLI Interface
    - [x] gather
    - [x] gather ALL
    - [x] diff
    - [x] commands
    - [x] combine
    - [x] validate
- [x] Modular providers
- [x] config file discovery
- [x] builtin config

## Core providers:

- [x] Homebrew
- [ ] File content

# v1.1 Progress

- [ ] external process providers
- [ ] unit tests for core logic
- [ ] unit tests for core providers
- [ ] better CLI support for filtering/extracting information
- [x] gather multiple providers/qualifiers in one invocation
- [ ] manpage
- [ ] bash completion

## Core providers

- [ ] Aptitude
- [ ] IPTables
- [ ] ASDF
- [ ] Pip
- [ ] Pipx
- [ ] Docker

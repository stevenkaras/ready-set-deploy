# Ready-Set-Deploy!

RSD is a deployment framework designed to work offline-first without a centralized controller.
RSD is not an execution framework, nor does it specify how desired state is defined.

# Usage

```bash
rsd gather PROVIDER1.ID > provider1_state.json
rsd gather PROVIDER2.ID > provider2_state.json
rsd combine provider1_state.json provider2_state.json > host_state.json
rsd diff host_state.json role_state.json > plan.json
rsd commands plan.json

# As individual steps with some shortcuts
bash -x <(rsd diff <(rsd providers role_state.json | rsd gather-all) role_state.json | rsd commands -)
# Or all together in a single command
bash -x <(rsd apply-local role_state.json)
```

# Design

RSD is split into three basic parts: gathering the state, operations on the theoretical state, and rendering a diff into commands.
The main design goal is to minimize computational effort and enabling offline manipulation of the ideal system configuration state.

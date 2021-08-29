# Ready-Set-Deploy!

RSD is a deployment framework designed to use set theory to issue the least number of commands to bring a system to a desired state.

# Usage

```bash
rsd role.py > role_state.json
rsd role.bash > role_state.json  # rsd runs any executable file with some small hooks to validate output
rsd gather HOST > host_state.json
rsd diff --from host_state.json --to role_state.json > plan.json
rsd apply HOST --plan plan.json

# Altogehter now
rsd apply HOST --plan <(rsd diff --from <(rsd gather HOST) --to <(rsd role.py) )
# or as a convenience (invokes the above somewhat more intelligently for multiple hosts)
rsd execute HOST --role role.py
```

# Design

RSD uses a three phase process: fact gathering, diff, and execution.
Plugins provide functionality for all three phases, although each come with defaults.

The main design goal is minimal effort.

Feature goals (some out of scope for the core project):

* Centralized execution against remote hosts
* Agent execution with arbitrary triggering (cron, pubsub, etc)
* Modular plugin system

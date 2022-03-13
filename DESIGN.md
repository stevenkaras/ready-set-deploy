# Design and architecture philosophy

This document aims to lay out the design philosophy and motivations behind RSD.

## Why existing solutions weren't sufficient

Other systems take an imperative approach towards defining system state.
Even those that ostensibly don't really do, just with a tiny bit of 

## Driving tenets

- Always do the absolute minimum amount of actual work needed to deploy a system
- Decouple defining the desired state from the actual execution
- Provide tooling to help bootstrap deployment definitions easily
- Provide a robust framework for quickly building new providers
- Define the desired state as small as possible, but operate on as complete a state as possible
- RSD is not a front-end or a back-end. It's the plumbing in the middle.

### Why do the absolute minimum?

By the absolute minimum, it means that RSD should avoid emitting commands unless they will have a known effect.
Many existing systems will go to great lengths to determine idempotent commands to mutate system state.
This should minimize the amount of time it takes to actually execute a deployment.

### Why decouple execution from defining the desired state?

Most systems have tight coupling between the two.
This means that you're either using an agentless or an agent based system by definition, and the cost of switching is enormous.
By forgoing execution altogether, RSD is simpler and easier to reason about.
It also opens the possibility for impressively simple or complex systems to be built on top of RSD:

- publishing desired state changes over pubsub and each server applies the diff locally
- setting up a cronjob to pull desired state from a central git repo
- tracking the current state of all servers in a central repo
- running deploys over ssh from a CI/CD pipeline

### What sort of tooling is needed to bootstrap definitions?

This means that providers must be capable of gathering system state (potentially incrementally if it helps them execute faster).
Bidirectional compilers should be able to convert commands to and from other systems such as ansible.

### What sort of framework is needed to build providers quickly?

Boilerplate logic is a pain - no one wants to write the set logic that determines the diff between lists of installed packages more than once.
RSD should allow providers to be built in whatever language/framework is easiest for them to work with, invoking them through a configurable module system.

### What does it mean that RSD is not a front end?

RSD doesn't provide an API or interface for generating partial states.
Use something like ansible to define your desired state and have it generate the partial state file.
RSD can then combine with a baseline configuration to determine the full desired system state, then diff from the last known state to find the minimal steps to deploy.

### What does it mean that RSD is not a back end?

RSD doesn't execute any commands, and will never learn how to. If you want to execute commands, you will need to pipe it to bash or ssh or somesuch.

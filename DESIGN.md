# Design and architecture philosophy

This document aims to lay out the design philosophy and motivations behind RSD.

## Why existing solutions weren't sufficient

Other systems take an imperative approach towards defining system state.
Even those that ostensibly use declarative state don't really, and rely on idempotent actions instead.
This means that dependencies between actions aren't resolved automatically and instead left as an exercise to the end user to order properly.
Moreover, all existing solutions that I've seen don't allow inspecting the desired state when the network is down.

## Driving tenets

- Minimize the amount of work done to deploy a system
- Decouple defining the desired state from the actual execution
- Provide tooling to bootstrap baseline system state easily
- Provide a robust framework for building new providers quickly
- RSD is not a front-end or a back-end. It's the plumbing in the middle

### Why minimize work? What does that even mean?

Some systems will bend over backwards to find idempotent commands that won't actually change anything in a system that's already in the desired state.
However, they still need to be executed, tracked, results gathered, and often interpreted as having done something or not.
This encourages small playbooks, leaving the rest of the system to be undefined which can result in state drift.

By taking the diff between the current and desired state, RSD can determine exactly what needs to change.
Moreover, by defining dependencies between components, it's possible to perform many actions in parallel, further speeding up deployment to a host.

### Why decouple execution from defining the desired state?

Most systems have tight coupling between the two.
This means that you're either using an agentless or an agent based system by definition, and the cost of switching is enormous.
By forgoing execution altogether, RSD is simpler and easier to reason about.
It also opens the possibility for impressively simple or complex systems to be built on top of RSD:

- publishing desired state changes over pubsub and each server applies the diff locally
- setting up a cronjob to pull desired state from a central git repo
- tracking the current state of all servers in a central repo
- running deploys over ssh from a CI/CD pipeline

### Why is bootstrapping baseline state important?

I want to see RSD in widespread use.
The best way to convince people to use your system is to reduce barriers to entry and egress (make it easy to start or stop using).
By reducing the initial bootstrapping as much as possible, it's easy to convince users they should try it out.
By providing easy to understand scripts that gather typical deployment patterns, it's possible to try out RSD and show off how it can be useful.

Ideally, it will be possible to target RSD as a virtual execution target in ansible, and render an RSD diff as an ansible role.
This makes it much easier to integrate RSD into existing workflows and even augment them to allow for offline introspection or efficient execution.

### Why is it building new providers so important?

No matter which providers come baked in, there will always be another package manager, another abstraction, another something that works every so slightly differently.
The expectation is that most non-trivial systems will want to implement their own custom providers that handle their organizational idiosyncrasies.

### What does it mean that RSD is not a front end?

RSD doesn't provide an API or interface for generating partial states.
Use something like ansible to define your desired state and have it generate the partial state file, or generate the full state and then diff against the current state.
RSD can then combine with a baseline configuration to determine the full desired system state, then diff from the last known state to find the minimal steps to deploy.

### What does it mean that RSD is not a back end?

RSD only includes the most minimal renderer possible for applying a partial state.
RSD doesn't execute any commands, and will never learn how to. If you want to execute commands, you will need to pipe it to bash or ssh or somesuch.

## Typed vs dynamic sections of code

The core theory for RSD is well defined and can be implemented from the spec.
The need to build providers quickly runs counterpoint to that though - it's a lot easier to write untyped code than typed.
To balance the safety we gain from strict typing with the developer productivity gained from allowing untyped code it's important to allow a trap door to move between the two.
This almost by definition should be separate from the serialization format, as some of the core abstractions (e.g. unordered sets of elements) do not have good representations in most serialization formats.

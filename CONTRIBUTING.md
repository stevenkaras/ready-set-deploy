# So you want to help out?

Great! This project will only improve with more contributions.

Below are some basic guides on how you can help out:

# Improve documentation

Fix typos, suggest better examples, anything and everything.
Nothing is too small!

# Adding a new provider

A provider is a gatherer which defines how to gather a component type, and a renderer which defines how to convert a diff component into commands to run.
Between the two of them, they need to define the "shape" of the component - the names and types of the elements.
Qualifiers are used to define dependencies between components - when a component is removed as part of a diff, everything that depends on it is also removed.

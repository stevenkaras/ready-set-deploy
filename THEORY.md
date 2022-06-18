# The theory of RSD

RSD is built on top of a simple hierarchy:

- System
- Component
- Element

## Elements

Elements come in one of the following types:

- Unordered
    - Atom
    - Set
    - Map
- Ordered
    - List

There are three operations defined on elements.
The first is apply (denoted as "A + D = B").
This performs the changes described by D to mutate A into some desired state B.
This operation is idempotent.
The second operation is diff (denoted as "B - A = D"), which produces the corresponding diff type that when applied will mutate A into B.
The third operation is combine (denoted as "A & B = C"), which produces a possible combination of the two full elements.
This is roughly equivalent to: "A + (0 - B) = C".
This operation should be idempotent.

Elements have a total order defined for each type (so Atoms are comparable to Atoms, but not to Sets).

### Atoms

Atoms are unsplittable, and are just immutable text.

#### Diff:

Replaces the left side with the right.

#### Combine:

Produces the right side.

#### Ordering:

Lexicographically ordered.

Diffs are lexicographically ordered.

### Sets

Sets are unordered collections of unique instances of elements.

#### Diff:

Produces the items to add (B - A), and the items to remove (A - B)

#### Combine:

Produces the union of the sets.

#### Ordering:

Ordered by comparing sorted items in the set - absence of a corresponding element is considered smaller, such that `{A}` is smaller than `{A, B}`.
However, note that `{A, B}` is smaller than `{B}` because `A` is smaller than `B`.

### Maps

Maps are mappings from Atoms to other elements.

#### Diff:

Produces a set of keys to remove.
Also produces key value pairs of those in B that are not in A, and those which are in both, but have different values.

#### Combine:

Produces a map that is the recursive combination of shared keys, and the union of the disjoint mappings.

#### Ordering:

Ordered by comparing sorted key value pairs - absence of a key is considered smaller.

### Lists

Lists of atoms - text can be represented as a list of lines, or a list of words.

#### Diff:

Diffs are a bit special because we want the action to be idempotent.
As such, we need to store some context to ensure it isn't lost.
More interestingly, sacrificing some efficiency can produce diffs that more accurately preserve the intent of the change.

In terms of implementation guidance: stand on the shoulders of giants. Encoding lists to make diffs easier is a very valid strategy.

#### Combine:

Produces the naive merge based on the diff-basically adding both sides of the diff.

#### Ordering:

Ordered by comparing atoms in the order they appear in the list.

### Where practice departs from theory

Above, I defined the result of diff D as only ever being applied on the element A to produce B.
However, there is great utility in taking the diff D and applying it to C in an attempt to move it largely in the same direction towards C'.
As such, it's important to capture the intent of the diff, which may vary significantly from the most efficient form.

Unfortunately, because intent is subjective the only mathematically proven algorithms all target the most efficient form.
The only method I'm aware of that provably produces diffs closer to the intent requires historical context which I cannot provide.

## Components

A component represents a cohesive set of system configuration state. Components should be independent of each other.
Components have one or more elements, a type, a qualifier, and any number of dependencies.
The type of component determines the type of elements it has.
A component depends on the existence of a component with the type/qualifier specified by each of its dependencies.

The qualifier is a list of path segments.

Components define the diff/apply/combine operations, but merely delegate them to the underlying elements. As such, a diff Component is populated solely by diff-Elements.

### Where practice departs from theory

Some components such as filesystems are inefficient to include fully, and as such may be defined in ways that potentially contradict one another. For example, a file's contents may be defined, but the entry in the directory not included.

## Systems

Systems are sets of components.

Systems also define the diff/apply/combine operations, delegating to components for these with matching type and qualifier. When removing a component, a special marker indicates that the component shall be removed. Similarly for components with no matching type/qualifier a special marker indicating a "full" component shall be added.

As such, Systems are either "partial" or "full" based on their components.

Also note that all the dependencies of all components in the system must be present for the system to be "valid".

---
title: Data structures toolkit for technical interviews
subtitle: Think quickly under pressure

categories: [Tips, Interviews]
redirect_from:
  - /blog/interview-ds-toolkit/
---

I'm horrible at technical interviews. 😥 Recently, one actionable reason for the struggle donned on
me: I can't find the breathing space to think straight and evaluate all my options when designing an
algorithm or trying to improve it.

In an attempt to help myself think under pressure, I've come up with a list of common tricks to
evaluate while solving a problem:

- Is the set of inputs a fixed size? Counting or bucketing them might help.
- Is there possible nesting in the input sequence? Consider stacks or queues.
- Would sorting simplify the problem? Consider scooting start and end pointers along instead of
  using recursion.
- Would using complements help? (E.g. find the target sum by keeping track of previously seen
  elements and searching for the current one's compliment.)

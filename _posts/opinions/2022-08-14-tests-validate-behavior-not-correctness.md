---
title: Tests validate behavior, not correctness
subtitle: In other words, tests document program behavior

categories: [Opinions, Testing, TDD]
redirect_from:
  - /blog/behavior-not-correctness/
---

Is it better to have tests that confirm incorrect behavior, or none at all? I'm here to argue that
tests are valuable even when they assert what a human considers to be an incorrect result. Pushing
this idea even further, a test asserting incorrect behavior should be added in a separate commit
*before* fixing the behavior in another commit.

## Why behavior instead of correctness?

Tests compare expected output with actual output—there's no fundamental contract that says the
expected output is intrinsically correct. For that matter, "correct" may change over time as a piece
of software evolves. Thus, tests assert the behavior of a program, not its correctness.

By limiting ourselves to testing correctness, we miss changes in behavior.

Suppose you discover a bug in some piece of software. If the software was perfectly tested, then
this bug would be present in some test you could point to and say, "I think the result should be
Y, but the program is currently outputting X as seen in this test." Of course, when there's a bug,
it's most likely because you didn't know you were missing a test for that behavior. Thus, being a
good TDD citizen, you add a test for the expected behavior, confirm that it fails locally, then fix
the bug to see the test go green before putting up the change for review.

The reviewer now needs to trust that your test actually works. This means additional cognitive
overhead trying to understand how the test is set up that detracts from checking the results of the
test. If instead, a test is added that asserts the present behavior followed by a commit that
updates said behavior, the reviewer can easily confirm their understanding of the program pre-fix
and then see *just the parts of the test that changed* due to the fix.

By adding tests that assert the present behavior of the program, every transition from one behavior
to another is documented rather than being implicit in the addition of a test with a bug fix.

## Why separate changes?

Suppose you are working on a large change in behavior (i.e. the functionality is not completely new)
that requires several commits to implement. Adding tests as you go runs afoul of the same issues
described above. A better approach is to add all the tests upfront, thereby separating behavior
changes from test additions.

The multi-commit approach shows your reviewer what is changing and what is not. For example, some
tests may be added for behavior that won't be changing. By separating the addition of tests from
their behavioral changes, you make it extremely easy for your reviewer to see which tests changed
(i.e. the behavioral transitions) in step N of the implementation.

Another benefit is the additional scrutiny given to your tests. When a PR is completely dedicated to
adding tests, you (and your reviewer) will be more inclined to find ways of minimizing boilerplate
and improving your testing infrastructure.

> Note: I haven't seen a way of following these practices when functionality is completely new and
> tests cannot be written because the code that should be tested doesn't exist yet.

---

To recap, adding tests separately from updating them documents the current behavior of a program and
makes behavioral transitions explicit which helps you and your reviewer better understand the
codebase as it evolves.

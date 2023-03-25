---
title: Fast Unix Commands
subtitle: The world's fastest `rm` command and one of the fastest `cp` commands

categories: [Projects, Performance, Files, FUC]
redirect_from:
  - /blog/fuc-overview/
---

[Fast Unix Commands](https://github.com/SUPERCILEX/fuc) (FUC) is a project that aims to create the
world's fastest Unix commands. Currently, this means `rm` and `cp` replacements `rmz` and `cpz` (the
'z' stands for "zippy"). When better performance cannot be achieved, the nest highest priority is
efficiency. In practice, `rmz` appears to be the fastest file deleter available while `cpz` wins in
most cases, only losing in flat directory hierarchies.

## Myth busting

Many a Stack Overflow answer will tell you to use this or that as a faster alternative to `rm`
or `cp`. Let's look at the [data](https://github.com/SUPERCILEX/fuc/tree/master/comparisons)!

### Rsync

Using `rsync` for copying is always slower that I can tell. This should not come as a surprise given
that it performs data integrity checks. Interestingly enough, `rsync` deletes very large directories
faster than `rm`, but is slower in all other cases.

### Find

`find` and `rm` are approximately equivalent in terms of performance.

### Tar

Shockingly, collecting a directory into a tarball and then extracting it into a new directory to
copy it is often faster than `cp`.

## Technical overview

Both tools are built using the same scheduling algorithm, following similar principles
to [FTZZ's scheduler](/blog/ftzz-overview#scheduling-algorithm). The key insight is that file
operations in separate directories don't (for the most part) interfere with each other, enabling
parallel execution. Thus, the goal is to schedule one task per directory and execute each task in
parallel.

Doing this for copies is relatively easy: iterate through every directory, spawning a new task when
a directory is encountered and copying files inplace. File removal is far more interesting because
you cannot remove a directory until all of its children (including subdirectories) have been fully
removed. As a consequence, file removal tasks must wait until their children have completed before
finally removing the current directory. Unfortunately, this approach is slow: memory and time must
be spent keeping track of child tasks, and children must somehow notify their parents of completion.

Flipping the problem on its head reveals a beautiful solution: what if children were in charge of
deleting their parents? With a little bit of atomic reference counting, this solution is
straightforward to implement and comes at almost no additional cost. While traversing directories,
each spawned child directory task includes a parent (smart) pointer, implicitly creating a dynamic
tree structure that models the directory hierarchy. These parent pointers are reference counted and
trigger the directory deletion when fully freed. Additionally, each task decrements its reference
count upon completion. That it! Now, regardless of whether a parent finishes after all of its
children or vice versa, the last "user" of a directory will delete its directory chain.

Pseudocode might make this clearer:

```python
def delete_dir(node @ Node { dir, parent, ref_count }, task_queue):
    for file in dir:
        if file is dir:
            ref_count++
            task_queue.spawn(new Node { dir: file, parent: node, ref_count: 1 })
        else:
            file.delete()

    ref_count--
    while node.ref_count == 0:
        node.dir.delete()
        node = node.parent
        node.ref_count--
```

---

Enjoy blazing fast copies and deletions! 🚀

---
title: File Tree Fuzzer
subtitle: Technical and performance overview

categories: [Projects, Performance, Files, FTZZ]
redirect_from:
  - /blog/ftzz/
  - /blog/ftzz-overview/
mathjax: true
---

[File Tree Fuzzer](https://github.com/SUPERCILEX/ftzz) (FTZZ) is a CLI tool written in Rust that
lets you generate pseudo-random directory hierarchies filled with some number of files, each of
which can be empty or contain some number of pseudo-random bytes. The *pseudo* part is important: it
means FTZZ will generate the exact same directory hierarchy given the same inputs. This makes FTZZ
useful for benchmarking other programs like `rm` or `cp` since you can run them again and again on
the same exact set of files.

## Technical overview

In a file system like ext4, independent directories can be operated on in parallel without
triggering locking inside the kernel (for the most part). Thus, FTZZ's goal is to schedule one file
generating task per directory. In its simplest form, the algorithm determines the number of files
and directories to generate according to some distribution, schedules a task to generate those files
and dirs, and repeats up to some max depth.

### Determining the file distribution

Given a target number of files, the file to directory ratio (i.e. the number of files per
directory), and the maximum tree depth, we can compute the number of directories per directory
needed to evenly spread the files across a tree of the given depth.

First, we find the total number of directories needed:
$\text{num_dirs} = \frac{\text{num_files}}{\text{file_to_dir_ratio}}$.

Next, we solve the following tree equation to find the number of dirs per dir (i.e. the fan-out rate
of the tree): $\text{num_dirs} = \text{dirs_per_dir}^\text{max_depth}$. Rearranged, we get:
$\text{dirs_per_dir} = \text{num_dirs}^\frac{1}{\text{max_depth}}$.

Finally, a normal distribution is used to add jitter to $\text{file_to_dir_ratio}$ and
$\text{dirs_per_dir}$ such that each generated directory is unique.

#### Error correction

Generating close to the target number of files is surprisingly difficult when the number of
directories is randomized. This is because parent directories have cascading effects on the total
number of files generated.

Suppose we want to generate 1000 files with 8 files per directory and max depth 3. Our formula tells
us that we need $(\frac{1000}{8})^\frac{1}{3} = 5$ directories per directory. Notice that this is an
over-approximation: $8 \* \sum_{d=0}^3 5^d = 1248$ since the formula from the previous section only
accounts for the number of directories in the last level of the tree. The correct equation involves
solving for the base of a geometric series which (I believe) does not have a closed-form solution.

Setting aside the over-approximation for a moment, let's say we generate a tree in which the normal
distribution decides the root should have 7 directories and everything else gets the mean of 5
except for one other directory which only has 3 subdirectories. In such a case, we will generate
$8 + (8 \* 7) + (8 \* 7\*5) + (8 * 7\*5\*5 - 2\*8) = 1728$ files. What about the other way around
(3 root dirs, one 7 dir leaf): $8 + (8 \* 3) + (8 \* 3\*5) + (8 * 3\*5\*5 + 2\*8) = 768$. As you can
see, small changes in the number of root directories has disproportionately large effects on the
total number of files generated.

To solve these two issues, we treat the $\text{dirs_per_dir}$ value as a guess and dynamically
update the mean of $\text{file_to_dir_ratio}$ to keep us on target. That is, we solve for
$\text{file_to_dir_ratio}$ at each level of the tree given the $\text{num_files}$ that have been
generated so far.

### Scheduling algorithm

The scheduling algorithm uses a combination of ideas from breadth-first and depth-first search to
minimize memory usage and kernel locking.

If we scheduled directory creation depth-first, creating the parent directory almost certainly
wouldn't finish before we tried to create its children, thereby causing contention within the kernel
as multiple threads attempt to create the same directory (since the child will attempt to create its
parent).

Using a breadth-first approach fixes this problem since we'll try to create a directory's children
after creating all of its siblings, thereby giving parent creation enough time to complete.
Unfortunately, memory usage in breadth-first algorithms scales with the width of each level, which
grows exponentially in our case.

To avoid contention while minimizing memory usage, FTZZ creates directory trees by scheduling
creation of all the direct children at once for each node being traversed. The following picture
illustrates this {depth,breadth}-first scheduling combination:

{% include article-image.html src="assets/projects/ftzz/scheduling-order.svg" alt="Scheduling order tree diagram" %}

## Performance overview

While the file creation scheduling algorithm has the biggest impact on performance, there are many
other small tweaks that become significant when applied together:

- On linux, using the `mknod` syscall to create empty files chops the syscall count in half
  (compared to `open`/`close`).
- When creating millions of files, using a name cache becomes important to eliminate the cost of
  converting integers to strings for use in file paths. (FTZZ names files and directories using
  monotonically increasing integers.)
    - Adding a cache is not as simple as it may seem: we cannot build it as we go as this would
      require locking of some kind (which must be avoided at all costs). Instead, we must
      pre-compute the cache in advance, hoping its entries are used. Furthermore, Rust does not
      allow you to share a heap-allocated object across threads without reference counting (since it
      needs to know when the object can be dropped), but this (again) requires locking in the form
      of an `Arc`. Thus, we must use unsafe raw pointers and manually manage the allocated memory.
- Scheduling a huge number of tasks at once should be avoided in any language as this will incur
  unnecessary memory usage. Instead, schedule tasks in batches and wait for some portion of the
  tasks to complete before scheduling the next batch.
- Re-use allocated memory where possible. Thanks to the batched scheduling and waiting, tasks can
  return heap-allocated objects for use in an object pool. In FTZZ's case, this saves dozens of
  millions worth in allocations.

---

Happy fuzzing!

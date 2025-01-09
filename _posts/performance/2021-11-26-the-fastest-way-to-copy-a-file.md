---
title: The fastest way to copy a file
subtitle: With benchmarks!

image: assets/performance/file-cp-benches/1kib-memcache2.svg
image_alt: Benchmark of copying 1 KiB files with the Kernel cache enabled
image_caption: "TL;DR: use the <code>copy_file_range</code> syscall if you can"

categories: [Performance, Files, Kernel]
redirect_from:
  - /blog/fastest-cp/
---

> Update: the ideas from this post have been implemented in
> [Fast Unix Commands](https://github.com/SUPERCILEX/fuc/tree/master/cpz).

I'm on a mission to find the fastest way to copy and delete files on a modern machine. I thought a
quick Google search would reveal the answer, but I only found this
[Stack Overflow post](https://stackoverflow.com/questions/7463689/most-efficient-way-to-copy-a-file-in-linux)
with people's opinion on the matter (but no proof), a [discussion](https://lwn.net/Articles/789623/)
on what the kernel can do to improve performance, and various articles claiming you should tar
directories to copy them faster (there's no chance of that being faster than a properly written
parallel cp implementation).

The only way to get an objective answer is by writing benchmarks, so
[here they are](https://github.com/SUPERCILEX/fuc/blob/fb0ec728dbd323f351d05e1d338b8f669e0d5b5d/cpz/benches/copy_methods.rs).
😁 The results will be highly dependent on your specific system, so I would recommend simply running
those benchmarks yourself if you're curious. However, I'll share my findings from running these on
my ext4 XPS 17 and an APFS Macbook.

## Findings

Honestly, the results are a little disappointing. With very small files (1 KiB), the fastest option
is to use `copy_file_range`[^1kib-memcache], but that's expected since you're going from four
syscalls (`open`/`read` /`write`/`close`) to one. However, running the same benchmark with
medium-sized files (1 MiB) results in a win for the `mmap` variant[^1mib-memcache] (with direct I/O
too[^1mib-uncached]). Finally, with large files (32 MiB), the method of copy doesn't matter since
the disk can't keep up[^32mib-memcache].

All is not lost though, as I did learn a few things:

- Write only `mmap`s are consistently terrible, don't use them. If you want to use `mmap`, set up a
  read-only `mmap` for the *from* file and then copy the bytes using `write` with the memory address
  of your `mmap` as the buffer for the *to* file.
- `copyfile` performs extraordinarily well on macOS, presumably because APFS supports copy
  acceleration (meaning the files aren't actually copied, instead only needing to update
  copy-on-write metadata). I'm guessing if my machine used Btrfs instead of ext4, I would see
  similar gains.
- Curiously enough, using `fadvise` with `POSIX_FADV_SEQUENTIAL` seemed to have no effect or make
  performance slightly worse. I'm not quite sure why that is — if I had to guess, I would say that
  being I/O bound means it doesn't matter how far the kernel tries to read ahead because it'll never
  fill its readahead buffer.
- Using `fallocate` or `truncate` to set the file length upfront (and thereby minimize metadata
  updates) improves performance on Linux, but seems to have no effect or slightly worsen performance
  on macOS.

My main takeaway is that **you should just use
[`copy_file_range`](https://man7.org/linux/man-pages/man2/copy_file_range.2.html)
(or
[`copyfile`](https://developer.apple.com/library/archive/documentation/System/Conceptual/ManPages_iPhoneOS/man3/copyfile.3.html)
on macOS) where possible** since it's good enough, will handle stuff like `fadvise` and `fallocate`
for you, uses copy acceleration when the file system supports it, and will come with free
improvements as the kernel is updated.

---

## Sample benchmarks

### Copying 1 KiB files with the Kernel cache enabled {#fn:1kib-memcache}

[^1kib-memcache]:
{% include article-image.html src="assets/performance/file-cp-benches/1kib-memcache2.svg" alt="Benchmark results" %}

<a href="#fnref:1kib-memcache" class="reversefootnote" role="doc-backlink">↩</a>

### Copying 1 MiB files with the Kernel cache enabled {#fn:1mib-memcache}

[^1mib-memcache]:
{% include article-image.html src="assets/performance/file-cp-benches/1mib-memcache2.svg" alt="Benchmark results" %}

<a href="#fnref:1mib-memcache" class="reversefootnote" role="doc-backlink">↩</a>

### Copying 1 MiB files with the Kernel cache disabled for reads {#fn:1mib-uncached}

[^1mib-uncached]:
{% include article-image.html src="assets/performance/file-cp-benches/1mib-uncached2.svg" alt="Benchmark results" %}

<a href="#fnref:1mib-uncached" class="reversefootnote" role="doc-backlink">↩</a>

### Copying 32 MiB files with the Kernel cache enabled {#fn:32mib-memcache}

[^32mib-memcache]:
{% include article-image.html src="assets/performance/file-cp-benches/32mib-memcache2.svg" alt="Benchmark results" %}

Ignore the extra probability of `copy_file_range` completing in 20ms, that's just happens to be the
first benchmark that ran before the system reached saturation.

<a href="#fnref:32mib-memcache" class="reversefootnote" role="doc-backlink">↩</a>

<!-- Hack to hide the actual footnotes since they don't support Jekyll includes -->
<!--suppress CssUnusedSymbol -->
<style>.footnotes { display: none; }</style>

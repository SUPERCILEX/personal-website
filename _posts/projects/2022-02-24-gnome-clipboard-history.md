---
title: Gnome Clipboard History
subtitle: Technical and performance overview

categories: [Projects, Performance, Gnome, GCH]
redirect_from:
  - /blog/gch-overview/
---

[Gnome Clipboard History](https://github.com/SUPERCILEX/gnome-clipboard-history) (GCH) is a Gnome
extension that saves what you've copied into an easily accessible, searchable history panel. The
primary innovation over existing clipboard managers is the use of a compacting log for persistent
storage.

* TOC
{:toc}

## Design constraints and choices

GCH is a rewrite of
[Clipboard Indicator](https://github.com/Tudmotu/gnome-shell-extension-clipboard-indicator) and had
the original goal of upstreaming any changes. This meant GCH needed feature parity with Clipboard
Indicator. Of those existing features, the following have performance implications that influenced
the rewrite's design decisions:

- Any history changes (including newly copied entries) are immediately written to disk.
- Previously copied items are resurfaced instead of creating duplicates (implying the need to search
  through the history to know if what has just been copied is a new or existing entry).
- Entries anywhere in the list can be modified or deleted.
- You can cycle through entries.
- The clipboard history is searchable.

Given those features' performance implications, several data structure choices naturally emerged:

- An append-only persistent storage structure (i.e. a log)
- A linked list to store in-memory entries
- A map and reverse lookup index that stores entries keyed by transient, globally unique IDs

On copy, the reverse lookup index minimizes the work done to find duplicates while the log minimizes
the work done to store new entries. The log also minimizes the work done when modifying arbitrary
entries. Similarly, the linked list minimizes the in-memory work done to add/remove/move those
entries. Search is still an open problem, but I discuss that [later](#search).

## The compacting log

GCH uses a relatively simple binary encoding to store copied entries:

```
[op type][ data  ]
[1 byte ][N bytes]
```

The first byte of an operation is always its type while the succeeding bytes are whatever an
operation desires. For example, an add operation looks like this:

```
             UTF-8 data bytes
             ∨
00000000  01 49 20 77 61 73 20 63  6f 70 69 65 64 21 00     |.I was copied!.|
          ∧                                          ∧
          Add op type                   NUL terminator
```

It would be preferable to store the length of the text instead of a NUL terminator, but no Gnome API
exists to read N bytes. Now let's see what happens when you favorite that entry, delete it, and then
copy and favorite another entry:

```
                                         Favorite op type
                                                        ∨
00000000  01 49 20 77 61 73 20 63  6f 70 69 65 64 21 00 03  |.I was copied!..|
          4-byte Little Endian ID (=1)
          ∨
00000010  01 00 00 00 02 01 00 00  00 01 4d 65 20 74 6f 6f  |..........Me too|
                      ∧  ∧
         Delete op type  4-byte Little Endian ID (=1)
00000020  00 03 02 00 00 00                                 |......|
             ∧  ∧
   Favorite op  4-byte Little Endian ID (=2)
```

There's a lot going on, so let's break it down.

First, you'll notice the implicit creation of IDs for our items. Since the log is append-only and we
always read it in its entirety on start, we can infer globally unique IDs based the position of
added entries.

Furthermore, because the log is append-only, deleting entries doesn't actually delete anything
(that's where [compaction](#compaction) comes in). Instead, we simply mark the entry as having been
deleted — in the exact same way as we mark an entry as being favorited. When parsing the log,
deleted items are appended to the in-memory linked list and later deleted when we reach the delete
operation.

The IDs are monotonically increasing and stored in Little Endian because I expect most people to be
using x86, thus saving some bit manipulation. I could have gotten a little fancier by using varints
instead, but fighting JavaScript didn't seem worth it.

> Future research: using mmap (or seek) to start reading somewhere near the end of the file.
> Supporting arbitrary starting decoding positions would require self-synchronization, but lets the
> decoder only read the last N entries (until the user requests more).

That's about it! There are a few other operations, but they all work similarly.

### Compaction

This is arguably the most interesting part of the log: compaction is what allows it to stay
append-only. On compaction, the entire log is deleted and recreated from scratch with inverting
operations removed. Inverting operations are those that cancel each other out. For example, adding
and deleting an item can be replaced with doing nothing.

After compaction, the example from above looks like this:

```
00000000  01 4d 65 20 74 6f 6f 00  03 01 00 00 00           |.Me too......|
```

All traces of the `I was copied!` entry have been removed and `Me too`'s ID has been shifted down.
IDs are therefore globally unique only between compaction intervals, meaning in-memory data
structures must be updated after each compaction.

> Upon reflection, I probably should have stored the ID with the add operation to minimize the work
> done on compaction. The only issue would be ID overflow, but that can be handled by keeping the
> set of active IDs to know if one has already been used. In any case, the current approach has the
> benefit of minimizing wasted space since add is the primary operation.

### When to perform compaction?

Since compaction is expensive and requires rewriting the entire history, we'd ideally like to
perform compaction... well, never! Unfortunately, never compacting means your on-disk history will
grow forever and parsing the log will become increasingly slow due to the number of inverting
operations. On the other hand, we could perform compaction anytime something changes, thereby
resulting in the minimal log size and no inverting operations.

Thus, the goal is to strike a balance between the number of compactions and the number of wasted
(i.e. inverting) operations. Surprisingly, it's very easy to keep track of wasted operations: if you
delete something, then you've wasted two operations (one for the add and one for the delete).
Similar logic follows for other operations.

Next, pick some threshold for the number of wasted operations and perform compaction if the
threshold is exceeded. Easy!

## The linked list

In memory, the clipboard history is stored in a doubly linked list, allowing for instant deletion
and easy pagination. Pagination is important for GCH because Gnome does not have a UI list API (like
a RecyclerView) that is capable of scaling to the history sizes I wanted to support.

The biggest challenge is in trying to minimize iteration since linked lists have such terrible
memory access patterns.

## The reverse lookup index

The index (from text to entry ID) is implemented as a fairly standard chaining hash table. To
maximize hashing performance while minimizing collisions, a special hashing function is used that
takes advantage of assumptions about our corpus. Notably, long strings are unlikely to have length
collisions (e.g. why would someone copy two *different* strings that are exactly 30224 characters
long?) whereas short strings are (e.g. someone copies "abc" and "123"). We therefore arrive at the
following hash function:

- When the text is very long, its length is used as the hash.
- When the text is short, a proper hash function is used.

## Search

Search uses regex queries and returns paginated results sorted by recency to try and perform the
minimal number of matches. While ok, this is clearly suboptimal as we should be using a proper
index. That said, I found performance to be adequate and decided to let it be.

## Developer experience musings

GCH is written in JavaScript because it is the only language supported by Gnome extensions. As a
performance-minded individual, I've found the Gnome extension developer experience to be deeply
dissatisfactory: the language choice makes it impossible to do certain things. Of note:

- The linked list could have been optimized to store nodes as cache-line-sized blocks.
- A proper map implementation could have been used instead of my poorly optimized version, but the
  JS Map does not support custom hash functions.
- A proper serialization library could have been used (like Serde) which would have made the initial
  implementation much easier.
- Anything to do with multi-threading (such as running search in a background thread) is impossible.
- The log uses an op queue to ensure serializability — this would have been trivial to implement in
  a language that supports single-threaded executors.
- Powerful programming patterns like
  [RAII](https://doc.rust-lang.org/rust-by-example/scope/raii.html) don't exist.
- I have more complaints, but I'll spare you.

In brief, I'm excited to see what Pop!_OS does with their
[COSMIC DE](https://www.omgubuntu.co.uk/2021/11/system76-is-building-its-own-desktop-environment).

---

Happy copying! Oh, and of course: RiiR.

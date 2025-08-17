---
title: 'The need for new instructions: atomic bit fill and drain'
subtitle: Hardware acceleration for lockless channels

categories: [Opinions, Performance, Lockness]
redirect_from:
  - /blog/atomic-bit-fill/
---

In the [previous article](/blog/opinions/performance/lockness/lockless-queues-are-not-queues), I
proposed a new lockless channel architecture based on two bit vectors. One is used to reserve access
to a memory region, the other to commit changes. I showed promising theoretical performance
improvements: whereas existing architectures pay the cost of linearizability without clients being
able to take advantage of such consistency, lockless bags allow each element in the channel to be
operated upon fully independently. In theory.

In practice, hardware processes atomic operations by locking cache lines. Readers and writers in
lockless bags need to modify both bit vectors, which means locking both cache lines and neutering
any performance benefits offered by lockless bags. How can we fix this?

Hardware needs to give software an efficient mechanism for locking memory regions.

## New instructions: `atomic_bit_{fill,drain}` and `atomic_bit_set`

Here are the proposed signatures:

```
atomic_bit_{fill,drain}: {cache line address, max # bits} => {changed bit mask}
atomic_bit_set: {cache line address, bit mask} => {}
```

Given a cache line and a maximum number of bits *M* to fill, `atomic_bit_fill` scans the cache line
for zeros and flips at most *M* of them to ones. It returns the mask of flipped bits.
`atomic_bit_drain` operates identically except that it scans for ones and returns them to zero.
These instructions could operate on machine words, but the more bits you have the deeper your
channel queue can be. I assume it wouldn't be too difficult to return 512-bit change masks and use
AVX-512 instructions to compute indices out of the mask.

## How do you use these instructions?

The concepts from lockless bags apply mechanically:

1. To prepare *M* elements, call `atomic_bit_fill` on the reservation bit vector.
2. Use the returned mask to write your elements into their corresponding array slots. An empty mask
   means the channel is full.
3. Once the elements have been written, call `atomic_bit_set` to update the commit bit vector.

Receive elements by using `atomic_bit_drain` instead.

## Why are these instructions more powerful than existing atomics?

`atomic_bit_{fill,drain}` offer novel acceleration opportunities: the key idea is that **cores may
issue requests without knowing the state of the bit vectors**. This bears repeating: `cmpxchg` and
atomic bitwise instructions require knowing the state of the word being operated upon prior to
modification. On the other hand, `atomic_bit_{fill,drain}` instructions do not need to know the
state of the word and therefore do not need to own the memory being operated upon, meaning **cores
can issue fill/drain requests in parallel**.

Put another way, cores never need to pull the cache lines down. A synchronization point to process
incoming requests remains, but in the time it takes the on-chip network to return the resulting bit
mask to the originating core, other requests may have been issued and serviced, changing the state
of our bit vector.

We've found a way to let cores communicate their ownership over memory regions concurrently! Global
linearizability has been vanquished at last: operations over a particular element in the bit vectors
are linearized, but each element's operations are fully independent.

That's not all! We have a poor man's
[Intel Dynamic Load Balancer](https://dl.acm.org/doi/pdf/10.1145/3695053.3731026), but that doesn't
mean we can't get a little fancy:

- The L1 data pre-fetcher could intelligently start loading the corresponding cache lines of the
  array slots we claimed when executing an `atomic_bit_{fill,drain}` instruction.
- The CPU could move the bit vector cache lines around dynamically based on load. For example the
  lines could be in L3 if most cores are using it, or moved into the L2 of a core near the main
  sources of request traffic.
  - Taking this idea further, the 512 bits could be dynamically partitioned by the CPU to local core
    complexes. Say your chip is organized such that groups of cores have faster means of
    communication amongst themselves than going to L3. Each group could get ownership over a slice
    of the 512 bits and fall back to asking other groups for bits only if the local partition is
    full/empty. Perhaps more interesting is partitioning across NUMA nodes.
- Cores could develop affinities/flows on a best effort basis. Say core A is frequently publishing
  data while another core B is frequently consuming data. The server handling fill/drain requests
  could learn this pattern and try to ensure B gets masks primarily containing A's data to
  potentially improve locality.

## The nitty-gritty

The instruction signatures I proposed above aren't quite enough for a fully featured MPMC channel.

To implement sleeping on an empty or full channel, hardware support is required (unless the
fill/drain instructions are implemented on 32-bit words). A sleeping bit will need to be reserved
somewhere in the cache line. The `atomic_bit_set` instruction will need to support setting the
sleeping bit atomically with the changed mask and return the previous state of the sleeping bit.

The fill/drain instructions also need to return a dead bit so channel disconnects can be handled
properly.

Both of these bits can be placed at the end of the cache line and normal atomic bitwise operations
need to be supported on the last 32 bits of the cache line so these bits can be updated as needed
and used as a futex.

Additionally, the `atomic_bit_set` instruction doesn't make sense as is: set the bits to what? So
there could be two variants of the instruction, one to set the mask bits to zero and another to set
them to one. Or the instruction could be expressed in terms of OR and AND operations, where the
change mask is inverted when passed into the AND variant of the change mask update instruction.

Finally, `atomic_bit_set` should support acquire/release memory orderings.

## MPSC channel support

To support MPSC channels, additional hardware support is required. I couldn't figure out a good way
to maintain independence between
[streams](/blog/opinions/performance/lockness/lockless-queues-are-not-queues#mpsc-queues-are-special),
so we return to global linearizability by implementing software lockless queues in hardware. The
hardware can reserve some bits to represent head/tail pointers in each bit vector's cache line,
marking where the next bits should be filled/drained. The `atomic_bit_drain` instruction would only
be allowed to return a non-empty mask when the head points to filled bits. Note that this approach
incurs the same problems as described in
[the previous article](/blog/opinions/performance/lockness/lockless-queues-are-not-queues#lockless-queues-are-slow)
around unfortunately timed context switches blocking the entire channel.

However, hardware acceleration maintains the advantage of supporting concurrent requests to add
elements to the channel.

## Recap

Existing lockless channels can only operate as fast as the hardware can move a cache line between
cores, which can be
[terribly slow](https://chipsandcheese.com/p/core-to-core-latency-data-on-large-systems). This novel
approach proposes a stateless hardware acceleration method for lockness channels: with it, cores can
independently and concurrently request modification to the lockless channel. In essence, the new
approach deeply pipelines updates while existing channels serialize updates.

Please reach out if you're building something like this, I'd be very interested in providing the
software implementation.

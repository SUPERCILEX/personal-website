---
title: Your MPSC/SPMC/MPMC queue is not a queue
subtitle: Rethinking our approach to lockless channels

categories: [Opinions, Performance, Lockness]
redirect_from:
  - /blog/not-a-queue/
---

Lockless queues let multiple cores communicate with each other without mutexes, typically to move
work around for parallel processing. They come in four variants: `{single,multi}`-producer
`{single,multi}`-consumer. A producer gives data to a consumer, each of which can be limited to a
single thread (i.e. a single-`{producer,consumer}`) or shared across **multi**ple threads. But only
the single-producer single-consumer (SPSC) queue is actually a queue!

> This article is part of [a series](/blog/tags/lockness) building
> [Lockness](https://github.com/SUPERCILEX/lockness/blob/master/README.md), a high-performance
> blocking task executor.

<style>.too-big img { max-height: 50vh }</style>

## SPMC/MPMC queues are broken

Consider the so-called SPMC queue. By definition, received messages cannot be processed in a total
global order without additional external synchronization. First, the single, ordered input stream is
arbitrarily split amongst each consumer. Then, each message is removed from the queue in the same
order. But from this moment onwards, the consumer thread can be paused at any moment (even within
the library implementation that is still copying the data into your code). Consequently, another
thread can process an element from the future before your code has even had a chance to see that it
claimed an element, now from the past.

Acausality *within* consumers is the only upheld invariant: a consumer will not see any elements
prior to the last element it has seen. This guarantee is almost certainly too weak to be useful as
consumers have no control over which set of elements are seen, meaning arbitrary elements from the
future may have been processed on other threads.

<div class="too-big">
{% include article-image.html src="assets/lockness/acausal-recv.svg" alt="Diagram of a SPMC channel exhibiting non-queue-like behavior." caption="An example SPMC queue where element B is processed on thread 2 acausally before A on thread 1" %}
</div>

Similar logic applies to MPMC channels with the additional weakening that different producer streams
are processed in no particular order. To work around this, some implementations use many SPMC
channels to make a MPMC channel. They introduce the concept of a token which lets consumers
optionally choose a specific producer to consume. Were this token to guarantee exclusive access to
the producer, you've just created a poor man's SPSC queue. Without exclusivity, you get all the same
problems as SPMC channels (items being processed out-of-order by other threads).

## MPSC queues are special

While additional synchronization can be applied on top of SPMC and MPMC channels to provide ordering
guarantees, the more useful abstraction is a stream. MPSC channels are special in that each producer
can be thought of as its own stream, even though no ordering guarantees are provided between streams
(producers). The consumer will see each stream in order with interleavings between streams. In
hardware terms, it's a multiplexer.

Consumer threads can then be set up for specific purposes. For example,
[Ringboard](https://github.com/SUPERCILEX/clipboard-history/blob/master/README.md) uses two consumer
threads following the actor model in its UI implementations. Any thread can request state changes
and/or submit view updates, but state changes and view updates are each processed serially on their
own threads. Since I only have two consumer threads, this is effectively a mini
model-view-controller framework: the controller thread handles model updates and the main thread
updates the view. Notice that order within streams is important: the controller should process user
input in the order in which actions occurred. However, other updates (i.e. other streams/producers)
like an image loader having finished retrieving an image from a background thread can be interleaved
arbitrarily with the user input stream.

Thus, MPSC channels as a whole aren't queues, but each producer is its own queue which provides
useful guarantees.

## The rundown

To summarize, SPMC queues and by extension MPMC queues don't have useful ordering guarantees—calling
them queues is silly. MPSC queues can be thought of as a set of producer queues multiplexed
together.

> Note: I've left SPSC queues out of this discussion because they are real queues with a generally
> agreed upon optimal implementation: power-of-2 queue capacity backed by duplicated mmaps with
> cached head/tail pointers expressed in terms of elements written/read, and optional
> [get_robust_list](https://man7.org/linux/man-pages/man2/get_robust_list.2.html) support to handle
> multiprocess shared memory dead counterparty notification.

## Lockless queues are slow

Lockless queues are so named by virtue of being implemented with a queue, namely circular buffers or
variations on linked lists. This is problematic because the queue linearizes updates to the channel
where no such global ordering can be observed as explained above.

<div class="too-big" id="mpmc-diagram">
{% include article-image.html src="assets/lockness/mpmc-blocking.svg" alt="Diagram of MPMC channel contention." caption="Blocked producers and consumers in a MPMC channel, due to linearization" %}
</div>

The implementation of a lockless queue can be conceptualized through four pointers:

- The tail: producers increment it to reserve a slot to work within.
  - Slots in <span style="text-decoration: underline; text-decoration-color: #e03131">red</span> are
    being written to without interfering with consumers.
- The committed pointer: producers have finished writing to all slots past this offset.
  - Slots in <span style="text-decoration: underline; text-decoration-color: #f08c00">orange</span>
    should be ready to be consumed, but the shaded slot hasn't finished its write, thereby blocking
    consumers from accessing subsequent elements.
- The head: consumers increment it to claim a slot for consumption.
  - Slots in <span style="text-decoration: underline; text-decoration-color: #2f9e44">green</span>
    are ready to be read without interfering with producers.
- The consumed pointer: consumers have finished reading all slots past this offset.
  - Slots in <span style="text-decoration: underline; text-decoration-color: #1971c2">blue</span>
    should be ready to be written to, but the shaded slot hasn't finished its read, thereby blocking
    producers from writing to subsequent elements.

This approach is not wait-free: a context-switched producer or consumer in the middle of writing or
reading a value will prevent further progress.

## Lockless algorithm fundamentals

The core problem in lockless algorithms is mediating access to shared memory. SPSC queues have it
easy: they can prepare work and only commit it once they're ready. Once you allow multiple threads
to compete for the ability to access the same memory, they must go through stages:

1. A thread must exclude other competitors accessing a chunk of memory.
2. The thread uses the memory (non-atomically). This stage should be as fast as possible and is
   typically just a `memcpy`.
3. The thread commits (publishes) its change.

Producers reserve memory to publish to consumers while consumers claim memory to be read and then
released back to publishers.

## Lockless bags as a new approach

We've established that queue-based lockless channels pay the cost of linearizability without being
able to take advantage of it. We've also seen that the only true requirement for a lockless channel
is the ability to lock a region of memory.

Instead of a queue, let's use a bag! What's a bag? Well, uhhhh... It's a bag. You can put stuff in,
rummage around, and take stuff out. Notice that I said nothing about _what_ you get out—if it's in
the bag, it's a valid item to be taken out at any time (i.e. in an unspecified order).

The fastest single-threaded bag implementation is of course a stack. But this is the multithreaded
world, so let's instead use an array and two bitvectors. The first bitvector will be our
reservations: producers atomically set bits to gain exclusive access to the corresponding array
slot. The second bitvector is the list of committed slots: once producers are done with a slot, they
set its corresponding commit bit. Conversely, consumers unset commit bits to read the slot and unset
the reservation bit to return the slot to producers.

<div class="too-big">
{% include article-image.html src="assets/lockness/mpmc-bag.svg" alt="Diagram of a bag-based MPMC channel." caption="Threads in a lockless bag independently control their slots" %}
</div>

In this scheme, every producer and consumer operates independently. If a thread is stuck between
stages, it has no effect on the progress of other threads. We have ourselves a wait-free MPMC
channel!

## You don't need unbounded channels

Limitless anything doesn't exist in the real world, as much as we love to pretend it does. Unbounded
channels introduce a lot of complexity in an attempt to paper over poorly engineered systems. If
consumers cannot keep up, producers must slow down. The best way to go about this is to apply
backpressure, but sadly this is rarely an option. Dropping the messages is a possibility, though a
distasteful one. Alternatively, producers can cheat and buffer messages locally while waiting for
space to free up when consumers are full. This last approach is the one taken throughout Lockness,
minimizing communication and therefore contention when it is most critical (the channel is
overloaded).

For this reason (and let's be real mostly because unbounded channels are hard), the lockless bags
I've implemented are unconfigurably bounded.

### But here's an idea to support unbounded lockless bags

Make it a tree! Right now, the bitset represents data slots in an array, but it could additionally
allow pointers to sub-nodes. This feels like a reasonable approach, though I haven't thought too
hard about a precise implementation.

## Introducing Lockness Bags

[Lock**n**ess Bags](https://github.com/SUPERCILEX/lockness/blob/master/bags/README.md) implement the
ideas described above and might be used to build the
[Lockness Executor](https://github.com/SUPERCILEX/lockness/blob/master/executor/README.md) should
benchmarking show an advantage.

### Are Lockness bags fast?

No :(

Queue-based channel implementations win over bags on current hardware by disjointing their producer
and consumer memory writes. Remember the `consumed` and `committed` pointers from
[the diagram](#mpmc-diagram)? In practice, these are implemented in a distributed fashion: each slot
has a flag that marks it as readable or writable. To start, all slots are writable and transition to
readable and back as you write and read the slots. The head pointer can only advance if its current
slot is readable and conversely for the tail pointer. Crucially, this means consuming a slot almost
never touches a cache line producers are actively working with.

On the other hand, lockless bags are implemented with two atomics each representing a bitvector. To
produce and consume a value, you must always update both bitvectors. This means producers *and*
consumers are all contending over the same two cache lines. On the other hand, lockless queues limit
contention for producers to the tail cache line and similarly consumers only contend on the head
cache line.

## The future: hardware accelerating lockless bags

The [next article](/blog/opinions/performance/lockness/atomic-bit-fill) in the series explores the
idea of novel instructions that would hardware accelerate lockless bags to significantly outperform
all possible software channel implementations.

## Appendix: alternative approaches and their pitfalls

This problem has been itching the back of my brain for close to five years now. As part of the
journey, I've toyed with many different approaches that were rejected.

### Why doesn't a stack work for MPSC channels?

Instead of a circular buffer, couldn't we use a stack? Producers would compete to place items at the
top and the single consumer takes items down. Unfortunately, the consumer would need to block
producers from raising the stack, otherwise the consumer could end up in a situation where it is
trying to out an already stacked upon element. You can hack around this, but it doesn't seem better
than a queue.

### Why not use many SPSC queues to make a MPSC channel?

Generalizing the question, why not use multiple stricter channels to build a weaker one? On the
surface, this appears to be a straightforward solution, but you run into two problems:

- Load balancing: it is difficult to share resources. For example, consider using many SPMC channels
  to make a MPMC channel. If one producer has a spike in load while the others remain quiet, there
  is no way to use the available capacity of the other producers' channels.
- Poor scaling with high core counts: either producing or consuming values must scale linearly with
  the number of threads to scan across the individual queues. That said, this can be worked around
  by developing affinities, e.g. a consumer can keep reading from the same producer if it always has
  values. But if your load is so well-balanced that consumers could just pair with producers, you
  may as well do that instead.

Additionally, orchestrating the addition/removal of individual queues in the channel and supporting
sleeping becomes difficult.

### Why are tunnel channels bad?

Tunnels are the simplest MPMC channel: they hold no values and thus require a pairing between
producer and consumer to transfer a value onto the consumer's stack. Consequently, either the
producer or consumer must sleep to accept the next value, every time. This is painfully slow.

### Why not store machine-word sized elements in the channel?

Instead of supporting arbitrarily sized values in the channel, what if we only accepted values that
could fit in an atomic? More specifically pointers? Surprisingly, this doesn't really help. If your
only state is the array of atomic pointers, there's no easy way to find free/filled slots. Thus, you
need to go back to a circular buffer which has the same contention problems when the head/tail are
updated but the slot hasn't been atomically swapped to its new value. An alternative could be to
scan the array for empty/filled slots until one is found, but under contention you'll be fighting
over the same slots.

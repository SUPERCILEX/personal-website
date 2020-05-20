---
title: Advanced Kotlin Coroutines tips and tricks
subtitle: Learn about a few snags and how to get around them
---

{% include article-image.html src="/assets/kotlin/kotlin-banner.webp" alt="Kotlin Banner" caption="Coroutines are stable as of 1.3!" %}

Kotlin Coroutines starts off incredibly simple: just put some long running operation in `launch` and
you're good, right? For simple cases, sure. But pretty soon, the complexity inherent to concurrency
and parallelism starts piling up.

Here's what you need to know when you're knee deep in the coroutine trenches.

## Cancellation + blocking work = 😈

There's no way to get around it: you'll have to use good ol' Java streams at some point or another.
One problem (of many 😉) with streams is that they block the current thread. That's bad news in the
coroutines world. Now, if you want to cancel a coroutine, you'll have to wait for the read or write
to complete before you can continue.

As a simple reproducible example, let's say you open a `ServerSocket` and wait for a connection with
a 1 second timeout:

{% gist 7494c19538579dd0567853fe3251a973 %}
<div style="text-align: center" class="text-gray"><p class="gist-caption">Should work, right? Nope.</p></div>

Now you're feeling a bit like this: 😖. So how do we fix it?

When `Closeable` APIs are well built, they support closing the stream from any thread and will fail
appropriately.

> Note: in general, APIs from the JDK follow those best practices, but beware of any third party
`Closeable` APIs that may not. You've been warned.

Thanks to the `suspendCancellableCoroutine` function, we can close any stream when a coroutine is
cancelled:

{% gist ebacfb46c24156c7af020da63cf37822 %}
<div style="text-align: center" class="text-gray"><p class="gist-caption">Be sure this works with the API you are using!</p></div>

Now that our blocking `accept` call is wrapped in `useCancellably`, the coroutine will fail when the
timeout occurs.

{% gist 05c9453e8afd48fc1651b2b611a2f3cf %}
<div style="text-align: center" class="text-gray"><p class="gist-caption">Success!</p></div>

But what if you can't support cancellation at all? Here's what you need to watch out for:

- If you use any instance properties/functions from your coroutine's enclosing class, it will be
  leaked even if you cancel the coroutine. This is especially relevant if you think you're cleaning
  up resources in `onDestroy`. **Workaround:** move the coroutine to a `ViewModel` or other
  non-context class and subscribe to its result.
- Make sure to use `Dispatchers.IO` for blocking work since that allows Kotlin to set aside some
  threads that it expects to be waiting indefinitely.
- Use `suspendCancellableCoroutine` over `suspendCoroutine` wherever possible.

## `launch` vs. `async`

Since the top SO answers about these two builders are out-of-date, I thought I'd touch upon their
differences again.

### `launch` bubbles up exceptions

When a coroutines crashes, its parent is cancelled which in turn cancels all the parent's children.
Once coroutines throughout the tree have finished cancelling, the exception is sent to the current
context's exception handler. On Android, that means *your app will crash*, regardless of what
dispatcher you were using.

### `async` holds on to its exceptions

That means `await()` explicitly handles all exceptions and installing a `CoroutineExceptionHandler`
will have no effect.

### `launch` "blocks" the parent scope

While the function will return immediately, its parent scope will *not* finish until all coroutines
built with `launch` have completed one way or another. This makes calling `join()` for all your
child jobs at the end of the parent unnecessary if you simply want to wait for those coroutines to
finish.

Unlike what you might expect, the outer scope will still wait for `async` coroutines to complete
even if `await()` is not called.

### `async` returns a result

This one's pretty simple: if you need a result out of your coroutine, `async` is your only option.
If you don't need a result, use `launch` to create side effects. And only if you need those side
effects to complete before moving on do you need to use `join()`.

### `join()` vs. `await()`

`join()` does *not* rethrow exceptions while `await()` will. However, `join()` cancels your
coroutine if an error occurred, meaning any code after the suspending call to `join()` is not
invoked.

## Logging exceptions

Now that you understand how differently exceptions are handled depending on which builder you use,
you're left with a dilemma: you want to log exceptions without crashing (so we can't use `launch`),
but you don't want to manually `try`/`catch` them all (so we can't use `async`). So that leaves us
with… nothing? Thankfully not.

Logging exceptions is where the `CoroutineExceptionHandler` comes in handy. But first, let's take a
moment to understand what actually happens when an exception is thrown in a coroutine:

1. The exception is caught and then resumed through a `Continuation`.
1. If your code doesn't handle the exception and it isn't a `CancellationException`, the first
   `CoroutineExceptionHandler` is requested through the current `CoroutineContext`.
1. If a handler isn't found or it errors, the exception is sent to platform specific code.
1. On the JVM, a `ServiceLoader` is used to locate global handlers.
1. Once all handlers have been invoked or one of them errors, the current thread's exception handler
   gets invoked.
1. If the current thread doesn't handle the exception, it bubbles up to the thread group and then
   finally to the default exception handler.
1. Crash!

With that in mind, we have a few options:

- Install a handler per thread, but that's not realistic.
- Install the default handler, but then errors from the main thread won't crash your app and you'll
  be left in a potentially bad state.
- [Add the handler as a service](https://gist.github.com/SUPERCILEX/f4b01ccf6fd4ef7ec0a85dbd59c89d6c)
  which will be invoked when any coroutine built with `launch` crashes (hacky).
- Use your own custom scope with a handler attached instead of `GlobalScope` or add the handler to
  every scope you use, but that's annoying and makes logging optional instead of the default.

That last solution is preferred because it is flexible while requiring minimal code and hacks.

For app wide jobs, you'll use an `AppScope` with a logging handler. For any other jobs, you can add
the handler when logging is appropriate over crashing.

{% gist 0dcb8468c7b19ff1a901dc730fb86828 %}
<div style="text-align: center" class="text-gray"><p class="gist-caption">Not too shabby</p></div>

## Closing thoughts

Anytime we have to deal with edge cases, things get messy pretty fast. I hope this article helped
you understand the variety of problems you can run into given subpar conditions and what potential
solutions you can apply.

<hr/>

Happy Kotlining!

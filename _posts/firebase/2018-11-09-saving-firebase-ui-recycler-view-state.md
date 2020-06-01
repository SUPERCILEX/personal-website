---
title: Saving FirebaseUI RecyclerView state
subtitle: Hot starts, cold starts, and even process deaths — your state is always restored
categories: [Firebase, Android]
redirect_from:
  - /blog/fui-rv-state/
---

FirebaseUI's database libraries are a great way to quickly and seamlessly bind data to the UI.
Unfortunately, that emphasis on ease-of-use and configurability makes automagically saving and
restoring RecyclerView state on the library side of things extremely difficult. Luckily, it's not
too hard to do yourself.

## Manually building database observables

When you first start out with FUI, you'll most likely be creating an adapter from a query directly:

{% gist b4d7a8595cdfe8eaa47e378cd4bcca27 %}
<div style="text-align: center" class="text-gray"><p class="gist-caption">Back to the basics</p></div>

Under the hood, the adapter is actually building a *backing observable snapshot array*. That's a lot
of fancy words, so let's parse them into something simpler:

- *Backing*: it's the data source powering your RecyclerView
- *Observable*: you can be notified when data changes
- *Snapshot*: these are your conventional `DocumentSnapshot`s for Firestore and `DataSnapshot`s in
  the RTDB's case
- *Array*: it's a list of those snapshots

At a high level, you can think of the `ObservableSnapshotArray` as an always up-to-date window into
your data.

With that in mind, we can manually build the adapter options from a custom array:

{% gist f77831b9f0019dd7ed0ff1cb444af354 %}
<div style="text-align: center" class="text-gray"><p class="gist-caption">👋 boilerplate</p></div>

## Keeping data hot

Currently, that array is going to be recreated and its data re-queried *every single time* our
activity starts. That's obviously not what we want. 😢

To make sure we never have to reload the same data twice while our app is in memory, we can create a
ViewModel to store the array with an always-on listener:

{% gist cee381d62cde2668b640d0d976f66834 %}
<div style="text-align: center" class="text-gray"><p class="gist-caption">The noop listener tells FUI to keep an active connection even when your view is gone</p></div>

When creating the adapter, simply use the array stored in your `ChatsHolder`:

{% gist 2ea6f2b106dd746b8954bcf617a17d4d %}
<div style="text-align: center" class="text-gray"><p class="gist-caption">The VM saves us from re-querying our data</p></div>

## Creating an infallible adapter

Now that your data isn't reloaded on activity start, there's just one problem left to solve:
restoring the user's scroll position. Because the array can change even though the adapter isn't
listening for updates, FUI has to clear the adapter.

To get around this issue, we can manually save the LayoutManager's state, which includes scroll
position:

{% gist d5c9a3ce8e9af686976212efd44a2db9 %}
<div style="text-align: center" class="text-gray"><p class="gist-caption">This is ugly, I know 😢</p></div>

Just remember to call the adapter's `onSaveInstanceState` in your fragment or activity.

## Background considerations

Even though everything is now working, there's one last consideration to keep in mind: what happens
when your app is in the background for extended periods of time? Thanks to the ViewModel, you'll
keep an active connection to the database until your activity dies — but that wastes the user's data
and your money.

Thankfully, the lifecycle team thought of this and created the `ProcessLifecycleOwner`, which allows
you to know when your app is in the background as opposed to updating because of a configuration
change. Here's how you would kill your database connection when your app goes into the background:

{% gist 07ac24ce65a8da118c913d3b37c9cfa7 %}
<div style="text-align: center" class="text-gray"><p class="gist-caption">Your users will thank you later</p></div>

## Closing thoughts

I hope you found this short guide to saving and restoring RecyclerView states helpful. Ideally,
we'll find a way to fix this directly in FirebaseUI, but that's unlikely to happen anytime soon.
Please let me know if there's anything else you're struggling with and I might write another
piece. 😊

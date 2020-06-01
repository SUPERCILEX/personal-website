---
title: Save money with this one Firestore free quota trick for CRON jobs
subtitle: No, seriously!
categories: Firebase
redirect_from:
  - /blog/firebase-quota-hack/
---

I'm sorry, but I just couldn't resist that clickbaity title. 😛 Jokes aside, let's say you have a
monthly CRON job that empties out your users' trash and does some other Firestore related cleanup.
This is a great use of Firebase Cloud Functions, but it comes at a cost: you're
creating/updating/deleting documents all in one go.

Remember, Firestore free quota resets daily. So if you're too small to max out your free quota every
day, but too big to stay on the Spark plan, you should consider running *daily* jobs instead.

As long as your Cloud Functions only query the data they're going to process, then it'll be far
cheaper to run a job every day and take full advantage of that free quota. As an added bonus, you'll
be able to better predict your monthly bill because you'll be spreading out Firestore usage over
each day.

{% include article-image.html src="/assets/chris-pratt.gif" alt="Chris Pratt Happy" caption="Free money?" %}

## Running daily jobs

Running a daily CRON job is ridiculously easy to do: simply create a
[Cloud Scheduler](https://cloud.google.com/scheduler/) job set to run at 3am each morning
(`0 3 * * *`) that publishes an empty data payload (`{}`) to a topic of your choice (`daily-tick`).
It'll look something like this:

{% include article-image.html src="/assets/firebase/daily-tick.webp" alt="GCP Scheduler Daily Tick" caption="This tick is completely free!" %}

In your functions' index file, subscribe to the `daily-tick` pubsub event and you're good to go.

<hr/>

Hopefully this will help you save a few bucks. Happy coding!

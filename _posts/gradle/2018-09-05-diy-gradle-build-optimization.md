---
title: DIY Gradle build optimization
subtitle: The definitive guide to Gradle build performance optimization
---

{% include article-image.html src="/assets/gradle/abstract-build.webp" alt="Abstract Gradle Builds" caption='Beautiful builds. Source: <a href="https://gradle.com">gradle.com</a>' %}

If you're anything like me a few months ago, you've hit a breaking point. You're feeling something
akin to desperation and you don't know what to do. You've already tried all the classic tricks like
fiddling with JVM args and Gradle properties, but to no avail.

I'm going to show you how to *actually* improve your build performance through rigorous analysis and
testing. That means I'm not going to throw random hacks at you for copypastaing — if you were hoping
for a quick fix, dry up your tears and buckle up, 'cause we're about to get into the nitty-gritty by
analysing your build to find the bottlenecks.

## Gradle 101

For any job, I think it's important to understand the fundamentals of your tooling. As an Android
developer, the official tool is Gradle, which I feel comes with a lot of misconceptions. To start,
let's dispel some of the common ones.

### What's the difference between Android Studio and Gradle?

This is something a lot of people struggle with: they equate Studio with Gradle. While the two tools
do talk to each other (hence those annoying "Update the Gradle plugin" dialogs), they have very few
similarities. One is a fancy editor, the other an automation tool.

Case in point, Gradle couldn't care less who's using it — heck, you could be writing code in
Notepad++ (ew!) or vim (☠️) and Gradle would be none the wiser. For example, everything could be
underlined in red in the IDE, but running `./gradlew assembleDebug` works just fine. (That usually
means you have to delete the `.idea/libraries` folder to force IntelliJ to refresh its indices BTW.)

**At its core, Gradle primarily cares about the files it gobbles up, and those it spits out.**

> Tip: if you want to improve your understanding of Gradle, migrate to the
[Kotlin DSL](https://github.com/gradle/kotlin-dsl) using
[this handy guide](https://guides.gradle.org/migrating-build-logic-from-groovy-to-kotlin/) — you'll
be able to Ctrl + B to your heart's content.

### So what's the Android Gradle Plugin then?

Well, Gradle on its own doesn't actually do anything. If you don't apply any plugins, you'll only
get built-in tasks like `help`, `tasks`, and `buildEnvironment` — those aren't going to build your
brilliant ideas. Wait, I figured it out! That's the secret to getting sub-second builds: don't
actually build anything!

Jokes aside, Gradle is an *automation* tool, not necessarily a build tool — it merely operates on
input files to generate output files. The rest is whatever you make of it: network requests, running
shell scripts… anything you can do from the command line, you can do it from Gradle.

However, if you're going to do something, Gradle needs to know what that something is — that's where
plugins come in: they *configure* your build. They tell Gradle what units of work, or *tasks*, are
available for you to run.

**TL;DR: plugins such as the Android Gradle Plugin (AGP) tell Gradle what tasks are available
(configuration step) and you then run them (execution step).**

## Analysing your current build performance

With the basics out of the way, we're going to optimize your build scripts, plugin configuration,
and task execution. Now, remember how I said this would be an involved process? Well, you're being
involved. 😁

### Add the build scan plugin

While Gradle includes the build scan plugin by default since v2.0, you'll want to add it manually to
ensure you get the latest version and don't have to agree to the ToS every time.

{% gist 1a45522316213336b2d92fb280833058 %}
<div style="text-align: center" class="text-gray"><p class="gist-caption">Simple build scan plugin configuration</p></div>

### Gather basic benchmarks

Run `./gradlew help` twice and then open up the scan for the second run. Ditto for
`./gradlew assembleDebug --rerun-tasks` and `./gradlew assembleDebug`.

> Note: we're running the build twice to get the best approximation of your real-world build
performance, including any caching and other optimizations.
>
>If you're able to invest the extra time and effort to step up your game,
**[benchmark](https://github.com/gradle/gradle-profiler#benchmarking-a-build) your builds with the
[Gradle Profiler](https://github.com/gradle/gradle-profiler) to get much more accurate results.**

You now have three benchmarks:

1. Configuration time
1. Clean build execution time
1. Incremental build execution time

These are the 3 scenarios we're going to be optimizing, starting with configuration time.

> Tip: whenever you change something, rerun the build to make sure said change had the impact you
thought it did.

### Project stats

To give you a better idea of how your build should be performing compared to mine, here are the
<span data-proofer-ignore>
[stats for my test project](https://api.codetabs.com/v1/loc?github=SUPERCILEX/Robot-Scouter).
</span>
(~15 modules and ~20,000 lines of Android related code as of this writing.)

<div class="slim-title">
{% assign repository = site.github.public_repositories | where: 'full_name', 'SUPERCILEX/Robot-Scouter' %}
{% assign repository = repository[0] %}
{% include repo-card.html %}
</div>

## General optimization

Before getting into the specifics, let's make sure you have the basics down:

- [Latest](https://gradle.org/releases/) Gradle version
- [Latest](https://developer.android.com/studio/releases/gradle-plugin) AGP version
- [Latest](https://blog.jetbrains.com/kotlin/category/releases/) Kotlin version
- Don't disable the Gradle Daemon
- Make sure [`org.gradle.caching=true`](https://docs.gradle.org/current/userguide/build_cache.html)
  in your `gradle.properties` file
- If possible, enable
  [`org.gradle.parallel`](https://guides.gradle.org/performance/#parallel_execution) too, especially
  if you have multiple modules

> Tip: since keeping track of the latest version of X is always a pain, I'd recommend using a
[version checker plugin](https://github.com/ben-manes/gradle-versions-plugin). TBH, I'm not sure why
this isn't part of Gradle by default.
>
>Bonus: if you're using an age-old machine, do yourself a favor and toss it out. At the end of the
day, crappy hardware equals crappy performance. The only solution there is getting a new machine.

## Optimizing configuration time

Getting back to business, you should have a build scan that looks something like this:

{% include article-image.html src="/assets/gradle/build-scan-summary.webp" alt="Build Scan Summary" caption="The Summary tab" %}

Drilling down into the Performance tab, you'll find all sorts of details about your build:

{% include article-image.html src="/assets/gradle/build-scan-performance.webp" alt="Build Scan Performance" caption="The Performance overview tab" %}

If your configuration time is above 10 seconds (and you don't have 300+ modules), something is
wrong. Otherwise, as long as you're happy with your configuration time, feel free to skip this section.

> Note: 4 seconds to configure the build is actually terrible — it should only be 1–2 seconds.
Unfortunately, the Kotlin plugin
[incorrectly resolves dependencies at configuration time](https://youtrack.jetbrains.com/issue/KT-26065).

Ready? Let's optimize the 💩 out of that configuration time.

### Cache network requests

If you're doing [this](https://stackoverflow.com/a/14804849/4548500), scroll up to find the
[better answer](https://docs.gradle.org/current/userguide/dependency_management.html#sec:refreshing-dependencies).

Check the network activity tab and make sure there were no requests:

{% include article-image.html src="/assets/gradle/build-scan-network.webp" alt="Build Scan Network Activity" caption="Zero is my hero" %}

### Don't do expensive operations

Look for bottleneck scripts dominating your configuration time. It could be file I/O, processing
hashes (Git), or anything else unusually expensive. Basically, you shouldn't ever be executing stuff
at *configuration* time.

Aside from my slow `afterEvaluate` block (caused by that Kotlin bug I mentioned earlier), everything
else passes the test with flying colors:

{% include article-image.html src="/assets/gradle/build-scan-script-configuration.webp" alt="Build Scan Script Configuration" caption="Example script configuration time" %}

### Don't use the old task APIs

Gradle 4.9 came out with a new API that enables
[task configuration avoidance](https://docs.gradle.org/current/userguide/task_configuration_avoidance.html).
As of this writing, the AGP doesn't yet support the new APIs, but the upgrade is targeted for v3.3
alpha 9.

In the meantime, make sure you **aren't using any of the
[APIs that force task configuration](https://docs.gradle.org/current/userguide/task_configuration_avoidance.html#sec:old_vs_new_configuration_api_overview)**
— those will come back to haunt you later.

### Use the new task APIs

Conversely, make sure any tasks you create in your build scripts use `register` instead of `create`
(explicitly or implicitly).

### Profile the build

If you've found a bottleneck but can't figure out where the problem is coming from, it's time to
[profile your build](https://github.com/gradle/gradle-profiler). I'd recommend using
[JFR](https://github.com/gradle/gradle-profiler#java-flight-recorder) (you'll need the
[Oracle JDK](https://askubuntu.com/a/521154/456255) and Linux to get Flame graphs):

```bash
$ ./gradle-profiler --profile jfr --project-dir "..." help
```

For example, you can see how naughty the Kotlin plugin is (`o.j.kotlin.g.i.AndroidSubplugin` is
forcing Gradle to resolve artifacts):

{% include article-image.html src="/assets/gradle/build-flame-graph.png" alt="Build Profile Flame Graph" caption="🔥" %}

And if you can't figure out whose fault it is but don't think it's yours, the Gradle team is always
happy to take a look at the profiling snapshots: [performance@gradle.com](mailto:performance@gradle.com).

## Optimizing clean build execution time

To be fair, I haven't really invested in this area because it doesn't matter all that much for my
day-to-day development. However, there are still a few basic steps you can take to make sure your
full builds aren't excessively slow.

### Tune JVM args

Ah yes, the classic trick every Gradle build performance article seems to mention. It turns out that
unless wildly misconfigured, they don't matter all that much.

In essence, your goal is to minimize garbage collection while also keeping your overall system
healthy. So if your heap size is too small, the GC will be thrashing constantly. Too large, and
you'll start running out of system memory for other things like Chrome or IntelliJ. As Thanos said,
you want it to be "perfectly balanced, as all things should be." Minus all the killing.

{% gist a8c09c08e7417c8d784840c7a6602600 %}

Now look for "Total garbage collection time" and make sure it doesn't account for more than 5% of
your build:

{% include article-image.html src="/assets/gradle/build-scan-gc-performance.webp" alt="Build Scan GC Performance" caption="4/124 = 3.2%, looks good" %}

If it's anything more than that, give the Daemon another GB. Rinse & repeat.

### Report excessively slow tasks to the offending parties (and disable them if possible)

If a single task is dominating your build, something is wrong. For example, the Firebase Performance
plugin is notoriously slow — something that's painfully obvious in the timeline view:

{% include article-image.html src="/assets/gradle/build-scan-timeline-bad.webp" alt="Build Scan Timeline" caption="Ouch" %}

When the task isn't needed for your dev builds, don't run it. You can do that by either not applying
the plugin, or disabling the task itself:

{% gist 054d90c063605c3a3d1ff611ed3d9111 %}

Now, you'll have an evenly spread out timeline with the longest tasks rightfully being those like
`compileDebugKotlin`:

{% include article-image.html src="/assets/gradle/build-scan-timeline-good.webp" alt="Build Scan Timeline" caption="Balance" %}

Here's another example: I noticed that builds running `installDebug` were excessively slow because
of `makeApkFromBundleForDebug`, so I
[reported it](https://issuetracker.google.com/issues/112180979). The Studio team found multiple bugs
and missed performance optimizations.

## Optimizing incremental build execution time

The importance of incremental builds is second only to configuration time. You'll be running them
dozens (if not hundreds) of times a day, so optimizing them is key.

### Ensure no incremental tasks are running

If you haven't changed anything, nothing should happen when you rerun a build. The Studio team is
doing a great job on this front, but the Play Services team sadly still hasn't made their
`GoogleServicesTask` incremental:

{% include article-image.html src="/assets/gradle/build-scan-incremental-timeline.webp" alt="Build Scan Incremental Timeline" caption="C'mon, we're sooo close!" %}

If there are tasks you don't think should be running, click on them to see why the cache was
invalidated. You're most likely configuring your build non-deterministically and accidentally
changing inputs each time.

### Minimize annotation processor use (or use [incremental ones](https://github.com/gradle/gradle/issues/5277))

Are you using Glide modules just for the prettier `RequestOptions` syntax? Ask yourself this: *is
losing incremental compilation really worth it?* For me, the answer is no.

### Modularize your build

Yes, I know this one is also a tough cookie, but it'll pay off in the end. You'll not only improve
build performance, but also code quality by enforcing clean separation of concerns between your
different feature modules.

> Caveat: the Kotlin plugin doesn't yet support
[compilation avoidance](https://blog.gradle.org/incremental-compiler-avoidance) so you won't see
huge performance benefits when editing non-leaf modules as of this writing. To be fair, this is
[Gradle's fault](https://github.com/gradle/gradle/issues/5226#issuecomment-393647155).

### Replace `api` dependencies with `implementation` wherever possible

Once you've modularized your build, you'll want to have as many leaf modules as possible. Otherwise,
their children have to be recompiled whenever they change.

## Next steps

While you may have made performance gains today, that doesn't mean you won't mess it up again
tomorrow. (That was super cynical of me, sorry 😊.) **Share this article with your colleagues** —
make sure they aren't accidentally breaking the rules established throughout the guide.

I'd also recommend taking advantage of the
[Gradle Enterprise free trial](https://gradle.com/enterprise/trial/) to collect a few weeks worth of
data and make sure everyone on your team is getting the best possible performance.

<hr/>

Well, that's a wrap. I hope I've given you the tools to fight back growing build times and maximize
your productivity.

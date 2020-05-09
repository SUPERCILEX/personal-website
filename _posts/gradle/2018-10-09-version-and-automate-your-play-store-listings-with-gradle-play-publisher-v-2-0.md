---
title: Version and automate your Play Store listings with Gradle Play Publisher v2.0
---

<img src="/assets/gradle/gpp.webp" loading="lazy" width="100%" alt="Gradle Play Publisher Logo"/>
<div style="text-align: center" class="text-gray"><p class="caption">Android App Bundles, Gradle cache and incremental compilation, version conflict resolution strategies, massive API improvements, and everything in between now available in v2.0</p></div>

Have you ever wanted to keep track of changes going into your Play Store listings? Are you on a big
team where managing “who has access to what” is a nightmare? Or, are you perhaps managing dozens of
White Label distributions?

Excited yet? No? How about being able to continuously build and deploy your app every time you push
to GitHub? If CI doesn’t get you excited, then I don’t what will! 🤓

If you’ve used v1.x versions of the plugin before and thought there was room for improvement, you’re
not alone. Gradle Play Publisher v2.0 (GPP) covers all of the aforementioned cases and beyond. v2.0
adds more new features than I have fingers — and that’s not even including minor improvements or bug
fixes!

Without further ado, let’s begin!

## Getting started

> If you come from the v1.0 world, a lot has changed—hopefully all for the better! Be sure to read
the [migration guide](https://github.com/Triple-T/gradle-play-publisher/releases/tag/2.0.0-beta1#breaking).

If this is your first time publishing an app, you should probably start playing with the web console
first since *the initial app upload must be performed through the Play Console* anyway. Otherwise,
you should be able to breeze through the setup.

### Setting up a Service Account

Ironically, I find the Microsoft
[App Center docs](https://docs.microsoft.com/en-us/appcenter/distribution/stores/googleplay#setting-up-api-access-clients)
to be waaay better than Google’s own haphazard mess. Some notes:

- Don’t give the Service Account any roles when asked. This is recommended so the impact will be
  minimal if your keys get lost or stolen. Especially **don’t give the Service Account the Owner
  role** — that’s just ridiculous and I’m not sure why Microsoft wants that kind of access.
- I name my Service Account `CI` and use the same credentials for all of my CI tasks so I have a
  single kill switch if something goes wrong.
- When granting the service account access to the Play Console, *GPP only needs access to publish to
  alpha and beta channels at a bare minimum*. However, you’ll most likely also want to let GPP
  manage your listings. As for the production channel, I don’t let my Service Account touch it since
  that’s a sensitive place to be. Again, it’s all about minimizing the impact of a lost or stolen
  Service Account since you’ll most likely be
  [committing it to source control in some form or another](https://github.com/Triple-T/gradle-play-publisher#encrypting-service-account-keys).

### Applying the plugin

Check out the
[README](https://github.com/Triple-T/gradle-play-publisher/blob/master/README.md#installation) for
the most up-to-date instructions.

### Bootstrapping your project

You most likely already have listing details like an app title and description, promo graphics,
release notes, etc. Wouldn’t it be nice if this could automatically be downloaded for you? Well…
surprise! GPP does this for you. It’s as simple as running the bootstrap task:
`./gradlew bootstrap`.

### Getting full resolution images

**Edit:** this is no longer necessary as of beta 2.

Sadly, there’s a caveat to the `bootstrap` task: the Android Publisher API only returns image
previews — not all that helpful if you’re trying to turn around and republish them:

<iframe src="https://cdn.embedly.com/widgets/media.html?type=text%2Fhtml&amp;key=a19fcc184b9711e1b4764040d3dc5c07&amp;schema=twitter&amp;url=https%3A//twitter.com/supercilex/status/1010028428215513088&amp;image=https%3A//i.embed.ly/1/image%3Furl%3Dhttps%253A%252F%252Fpbs.twimg.com%252Fprofile_images%252F984942813426024451%252FLCKIEkHL_400x400.jpg%26key%3Da19fcc184b9711e1b4764040d3dc5c07" loading="lazy" allowfullscreen="" frameborder="0" width="100%" height="548" title="Alex Saveau on Twitter" scrolling="no"></iframe>
<p></p>
<div style="text-align: center" class="text-gray"><p class="caption">Maybe with enough RTs Google will oblige?</p></div>

So, how do we get around this? There are two solutions:

1. 😃 You saved your screenshots somewhere and can just replace the downloaded previews with the
   real ones.
1. 😡 You have to manually extract each screenshot from the Play Console.

\#2 is somewhat unpleasant, so brace yourself:

1. Find your app’s listing under `Store presence` ➡️ `Store listing`
1. Scroll down to `Graphic Assets`
1. For each screenshot, right click it and select `Inspect`
1. Right above the `div`, there will be an `img` tag with a link to the scaled-down version which
   looks like this:
   <a href="https://lh3.googleusercontent.com/lmkCVdLXkHJ0E28prBee9uqDjWN_Ta1s9OcO47S4j2Ke_KtYQgXX_TnefpQr17cGLoI=h150-rw">https://lh3.googleusercontent.com/...=h150-rw</a>
1. Replace the param value (`h150-rw`) with `h15000` so you get the highest resolution as a PNG. The
   link should now look like this:
   <a href="https://lh3.googleusercontent.com/lmkCVdLXkHJ0E28prBee9uqDjWN_Ta1s9OcO47S4j2Ke_KtYQgXX_TnefpQr17cGLoI=h15000">https://lh3.googleusercontent.com/...=h15000</a>
1. Rinse and repeat 🔄

This process is painful. I know. I’m sorry. Maybe now that will motivate you to try and get the
Google Play team’s attention?

## Using Gradle Play Publisher

As mentioned earlier, GPP includes a plethora of features. In fact, the plugin is almost feature
complete in the sense that we cover every important
[Android Publisher API](https://developers.google.com/android-publisher).

While GPP’s comprehensive
[README](https://github.com/Triple-T/gradle-play-publisher/blob/master/README.md) explains the
*how*, it isn’t intended to provide the *why*. That’s where this article comes in. Below, you’ll
find various use cases to improve your productivity.

### The basics

Since GPP is a Gradle plugin, you can publish your app artifacts and listing from the command line.
While that may not be too exciting, it can be a huge productivity boost if you need to upload APK
splits or update your app’s translations all at once.

### Versioning your metadata

I doubt I need to tell you why versioning is important, however, here’s a
[reminder](https://www.git-tower.com/learn/git/ebook/en/command-line/basics/why-use-version-control)
if that’s not the case.

### Publishing from a CI environment

One of the cooler use cases for GPP is publishing app updates on every build. You’ll first need to
[encrypt your credentials](https://github.com/Triple-T/gradle-play-publisher/blob/master/README.md#encrypting-service-account-keys),
but with that done, simply run your Gradle tasks as you normally would. I
[extract my secrets](https://github.com/SUPERCILEX/Robot-Scouter/blob/2979fd4fa4a785c4678788333db2bcd1e747694c/buildSrc/src/main/kotlin/com/supercilex/robotscouter/build/tasks/Setup.kt#L18-L24)
straight from Gradle.

### Automatically incrementing the version code on every build

This is GPP’s coolest feature! Not only can you publish your app from CI, but you also won’t have to
ever touch version codes again. Just push code and *voila*, a new version of your app is published
with the lowest version code available.

{% gist 13416fd977ebc2c37fdd5c232faf558a %}
<div style="text-align: center" class="text-gray"><p class="gist-caption">Automatically pick the right version code</p></div>

As a bonus, you can easily revert a change simply by triggering a rebuild on an older commit!

### Publishing to both the `internal` and `alpha` tracks at once (kinda)

If you haven’t been using the `internal` track, you’re doing yourself a disservice — it’s insanely
fast! The problem is that it’s meant to be, well… internal. What if you could publish your app to
both the `internal` track and then immediately to the `alpha` track so your team gets the fastest
updates while the outside world also gets your freshly baked builds?

You can do this with GPP by promoting a release. On CI, you would run
`./gradlew publishBundle && ./gradlew promoteArtifact --track alpha`. That’s it!

### Generating release notes on the fly

How many times have you wished you could provide a better experience to your beta testers?
(Hopefully it’s pretty often 😀.) With GPP, you can generate release notes from your commit messages
to let your testers know what you’re up to.

{% gist b0c5fb9756497e3f2b985fcabc7fd272 %}
<div style="text-align: center" class="text-gray"><p class="gist-caption">Help your beta testers test your app!</p></div>

### Generating screenshots on the fly

This is a hypothetical since I haven’t done it yet, but if you had a process to automatically
generate screenshots, you could pipe those to the `play` folder and automatically publish your newly
minted screenshots with the rest of your app on every build.

### Automate all the things!

If you’ve thought of a use case I haven’t mentioned, please share it with me! I’d love to hear what
people are building with GPP. And, if there’s something you don’t think is possible yet, feel free
to [file an issue](https://github.com/Triple-T/gradle-play-publisher/issues/new?template=feature-request.md).

## How does it work?

Since the best way to figure out how something works is to
[poke at the source code](https://github.com/Triple-T/gradle-play-publisher/tree/master/play/plugin/src/main/kotlin/com/github/triplet/gradle/play)
yourself, I won’t go into too many details.

If you’re looking to contribute, here are the basics you’ll need to know:

- The `PlayPublisherPlugin` is where everything starts. You’ll find task definitions,
  `PlayPublisherExtension` and `PlayAccountConfigExtension` setup, and a few other lifecycle tidbits.
- Most tasks extend `PlayPublishTaskBase` which helps access the publishing API.
- You’ll need an instance of `AndroidPublisher.Edits` and an edit ID (provided by
  `PlayPublishTaskBase`) to use the API.

> Note: if you’re thinking of creating a new task, definitely
[file an issue](https://github.com/Triple-T/gradle-play-publisher/issues/new?template=feature-request.md)
first so we can work with you to fit all the pieces I haven’t mentioned yet together.

### Meet the team 👋

[Björn Hurling](https://twitter.com/devhu) and [Christian Becker](https://twitter.com/DerGreeny)
both incubated the project while [Charles Anderson](https://twitter.com/gtcompscientist) and
[I](https://twitter.com/SUPERCILEX) coincidentally both joined the project in the same week to
kickstart the v2.0 spree. Björn is currently the Merge Master and Publishing Wizard.

All of us are happy to help and get feedback, so don’t hesitate to ping us on the interwebs.

## Future plans

That’s a wrap! I hope you enjoyed this look into what GPP v2.0 has to offer. While we think we have
99% of use cases covered, *please
[file an issue](https://github.com/Triple-T/gradle-play-publisher/issues/new?template=feature-request.md)
if there’s anything you think could be improved* — we’ll use this feedback to decide what to work on
next. And of course, don’t hesitate to
[file bugs](https://github.com/Triple-T/gradle-play-publisher/issues/new?template=bug-report.md).

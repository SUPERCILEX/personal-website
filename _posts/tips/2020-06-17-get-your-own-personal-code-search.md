---
title: Get your own personal Code Search
subtitle: Understand the links between your repositories and third-party code

image: /assets/general/gradle-codesearch-comparison.png
image_alt: Example search for a Gradle API
image_caption: Comparing a search for examples on how to use Gradle's new <a href="https://docs.gradle.org/6.5/userguide/configuration_cache.html#undeclared_file_read">Configuration Cache APIs</a> between GitHub and my codesearch instance.

categories: [Tips, Search, GitHub]
redirect_from:
  - /blog/personal-codesearch/
---

When it comes to finding a piece of code, GitHub's search can be less than helpful at times.
In stark contrast to that, the public version of Google's Code Search tooling absolutely kicks ass.
[cs.android.com](https://cs.android.com/) and [cs.opensource.google](https://cs.opensource.google/)
are my go-to tools for finding open source Google code, but unfortunately, they're just that:
*Google* Code Search. If you're looking for non-Google code, you're out of luck. Until now.

GCP offers "Cloud Source Repositories," which are basically just private GitHub repos with one
major benefit: Google will build a unified index of your code across all the repos in *all* the GCP
projects you have access to. That means you can log in with an account that has access to your
personal and work GCP projects to get one view into every line of code that matters to you.

For this guide, I'm going to assume your code is on GitHub, but GCP also supports Bitbucket out of
the box. If your code isn't on one of those two platforms (think GitLab), you can always set up
[manual mirroring](https://cloud.google.com/source-repositories/docs/pushing-code-from-a-repository#cloud-sdk).

Let's get going!

* TOC
{:toc}

## Fork third-party repos you care about

To mirror code from GitHub to GCP, you must be the owner of the repository in question (or at least
have admin privileges). This is because Source Repositories will add a
[webhook](https://developer.github.com/webhooks/) to your GitHub repo that copies all changes as
they happen. Since you probably don't have admin privileges on third-party repositories, you can
instead fork them and mirror the fork.

One small hiccup: your fork will get quickly out-of-date without regular syncing. Thankfully, GitHub
Actions makes this problem trivially easy to solve. Put this CRON job in a
`.github/workflows/fork-sync.yml` workflow file, and you'll be all set:

```yaml
name: Sync Fork

on:
  schedule:
    - cron: '0 0 * * *'

jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - name: Sync
        uses: TG908/fork-sync@v1
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          # TODO(you): change this to the upstream repository owner. In this case, I'm mirroring
          # https://github.com/gradle/gradle to https://github.com/SUPERCILEX/gradle and telling
          # the action that `gradle` is the upstream repo to pull from.
          owner: gradle
```

## Create a GCP project

To keep things organized, create a [new GCP project](https://console.cloud.google.com/projectcreate)
just for code mirroring. I've called mine `alex-codesearch`.

> Note: I believe Source Repositories will require setting up a billing account at some point, but
> the free quotas are
> [extremely generous](https://cloud.google.com/source-repositories/pricing/#free-tier)
> and I have yet to pay a cent.

## Mirror your repos to GCP

You can now finally [connect your repositories](https://source.cloud.google.com/repo/connect).

> Pro tip: if you're going to mirror more than a few repos, I would recommend opening up Chrome Dev
> Tools before clicking `Connect selected repository`. After clicking connect, look for the patch
> request in the Network tab. You can then `Copy as fetch` that request, paste it into the Console,
> and then replace the GitHub repo link near the bottom of the fetch URL with whatever other repos
> you're trying to connect. Or, hopefully GCP will add support for connecting multiple repos at once
> in their UI by the time you read this.

## Search!

You're all set now. The index will start populating at
[source.cloud.google.com](https://source.cloud.google.com/).

> **A note about shared access**
>
> In a corporate environment, you can create a Google Group in your G Suite domain and give that
> group email `Viewer` access to the Code Search GCP project. Anyone in the group will then be able
> to access Code Search.

As a fun little usage example, I wanted to migrate my GitHub Actions workflows to the latest
releases, so I started searching for `actions`:

{% include article-image.html src="/assets/general/sample-codesearch-part1.png" alt="Sample search for actions" %}

Oops, too many results. Let's try only YAML files:

{% include article-image.html src="/assets/general/sample-codesearch-part2.png" alt="Sample search for actions in YAML files" %}

Better, but still some extraneous results. Let's try `"actions/"`:

{% include article-image.html src="/assets/general/sample-codesearch-part3.png" alt="Sample search for actions/ in YAML files" %}

Ah-ha! Since I know `upload-artifact` has a `v2` version available, let's find all the instances
where I'm still using `v1` of the action:

{% include article-image.html src="/assets/general/sample-codesearch-part4.png" alt="Sample search for actions/upload-artifact@v1 in YAML files" %}

As you get better at Code Search, you'll be able to skip straight to the last step, but this demo
shows the power of having killer search capabilities.

<hr/>

Happy code searching!

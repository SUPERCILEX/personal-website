---
title: Server-side analytics with Firebase Hosting
subtitle: RIP Google Analytics (finally!)

image: /assets/firebase/website-basic-analytics.png
image_alt: Data Studio dashboard built from Firebase Hosting logs
image_caption: This website's custom analytics (mostly visited by bots 😜)

categories: [Firebase, BigQuery, Analytics, Tips]
redirect_from:
  - /blog/hosting-analytics/
---

Client-side analytics slow down your website and are inaccurate at best, especially in communities
like ours that tend to disable trackers. Until recently, Google Analytics and its equivalents were
the best you could do with a static site hosted on Firebase. No more! Firebase Hosting
[introduced](https://firebase.googleblog.com/2020/08/firebase-hosting-new-features.html)
[Cloud Logging](https://firebase.google.com/docs/hosting/web-request-logs-and-metrics) to address
this shortfall.

While Cloud Logging can be helpful in debugging a specific request, the magic comes when you enable
exports to BigQuery. Once your data is in BigQuery, you can do whatever you want — including make
the custom Data Studio dashboard pictured above. You can even go further than basic analytics and
make a health dashboard:

{% include article-image.html src="/assets/firebase/website-health-metrics.png" alt="Data Studio dashboard of website health metrics" caption="Custom health metrics" %}

If you're ok with spending a few hours to set this up and design your perfect dashboard, then the
rewards are well worth it. Onwards!

* TOC
{:toc}

## Enable Cloud Logging

It's free and just takes the
[click of a button](https://console.firebase.google.com/u/0/project/_/settings/integrations/cloudlogging).
The only concern I can think of is a potential PII issue since IP addresses are logged.

## Set up exports to BigQuery

> Note: sadly, this requires a billing account. Unless your site gets a crazy number of requests,
> it's basically free, costing only
> [$.01/200MBs](https://cloud.google.com/bigquery/pricing#streaming_pricing). Interestingly enough,
>nothing's actually shown up on my billing page… so maybe there's rounding that works in our favor?
> Either way, $.12/year for custom analytics seems worth it to me.

1. On the
   [Cloud Logging page](https://console.cloud.google.com/logs/query;query=resource.type%3D%22firebase_domain%22;timeRange=P7D),
   hit "Create sink"
1. Choose "BigQuery dataset"
1. For the name, put in something like `all-traffic`
1. For the destination, hit "Create new BigQuery dataset" and put in something like `analytics`

You can make sure there were no errors by checking your
[activity page](https://console.cloud.google.com/home/activity). If you see a bunch of BigQuery
requests and no red, you're good to go. You can now
[query your data](https://console.cloud.google.com/bigquery)! (Look for your GCP project ID in the
sidebar.) For example:

```sql
SELECT
  *,
  -- Did this request come from a bot?
  NOT STARTS_WITH(httpRequest.userAgent, "Mozilla")
  OR REGEXP_CONTAINS(httpRequest.userAgent, "(?i)bot") AS is_bot,
  -- What are all the requests an IP visited over the course of a day?
  -- (Note: this is imperfect since a session crossing over midnight will be assigned
  -- two different IDs.)
  TO_HEX(MD5(CONCAT(httpRequest.remoteIp, TIMESTAMP_TRUNC(timestamp, DAY)))) AS session,
FROM
  `alexsaveau-dev.analytics.*`
```

## Create your Data Studio dashboard

[Create a new report](https://datastudio.google.com/u/0/reporting) and choose the BigQuery
connector. From there, you can choose "Custom query" and put in whatever crazy query you came up
with.

Now all that's left is to geek out making charts. Have fun!

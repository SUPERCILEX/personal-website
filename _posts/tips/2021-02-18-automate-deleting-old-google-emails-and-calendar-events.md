---
title: Automate deleting old Google emails and calendar events
subtitle: Take control of your old data

categories: [Tips, Privacy, Automation]
redirect_from:
  - /blog/auto-delete-google/
---

Google [introduced](https://blog.google/technology/safety-security/automatically-delete-data/) auto
deletion for web, YouTube, and location activity back in 2019, but hasn't come out with official
solutions for their other products yet. Notably, gmail and gcal have data that likely isn't needed
after some number of months.

To automate deleting old data, [Google Apps Script](https://developers.google.com/apps-script) is
the handiest tool available. Off we go:

* TOC
{:toc}

## Creating a script

Visit [script.new](https://script.new) and write your own code, or paste in the solutions I've been
using from the [appendix](#appendix). Hit save, and the editor will automatically pick the first
function it sees to run by default.

You can then click on Run to execute the script manually, giving it permissions to access your
account.

> Note: the first time you run a script operating on lots of data, it will probably fail several
> times with various quota errors. You can either continue running it manually until the script
> reaches a steady state (having processed all your data), or move on to scheduling it and let
> things eventually sort themselves out.

## Scheduling scripts as CRON jobs

Once you've executed the script at least once to give it the correct permissions, you can use the
Triggers page found in the left sidebar to schedule your script for periodic execution. The defaults
when you add a trigger are good enough, but I tend to downgrade the schedule from every hour to once
a day as an hourly job seems a tad wasteful.

## Using scripts across multiple Google accounts

You can share a script like a Google Doc, but you'll have to run it once and create a Trigger for
each account. The main benefit of sharing the script is that modifications only need to be performed
once instead of being copied to each account.

## Thorn: Google accounts in the Advanced Protection Program

Sadly, if your Google account is enrolled in
the [Advanced Protection Program](https://landing.google.com/advancedprotection/), there is no way
that I'm aware of to run unapproved Apps Scripts. When you try to accept the permissions on the
first run, the request will be denied. This is
apparently [intentional](https://support.google.com/accounts/answer/7539956?hl=en#zippy=%2Ccan-i-use-non-google-apps-services-or-apps-script-with-advanced-protection)
which is a bummer.

<hr/>

## Appendix

These are the scripts I've been using to manage my own old data.

> Note: when I say "delete" below, I really mean "move to trash." The scripts don't empty the trash,
> allowing for the standard 30-day grace period to elapse.

### Email deletion

This script deletes emails that don't have the `indef` label *and* are 18 months old (or older). It
also deletes any unread emails that have been archived.

Reference docs are available [here](https://developers.google.com/apps-script/reference/gmail) and
you can read about creating labels in Gmail [here](https://support.google.com/mail/answer/118708).

Expected workflow:

- Manually label all critical emails with the `indef` label. Any other email is transient and will
  eventually be deleted.
- Any email you swipe away (archive) without opening is unneeded and gets deleted immediately. This
  mainly enables Inbox Zero without having to manually open emails you don't care about to mark them
  as read and then archive them.

#### Script

<p></p>

```javascript
/** Deletes 18 month+ old emails and unread archived emails. */
function processMail() {
  deleteEmailMatching('label:unread -label:inbox');
  deleteEmailMatching('older_than:18m -label:indef');
}

function deleteEmailMatching(query) {
  let threads = [];
  while (true) {
    threads = GmailApp.search(query, 0, 100);
    if (threads.length > 0) {
      trash(threads);
    } else {
      break;
    }
  }
}

function trash(threads) {
  threads.forEach(thread => {
    console.log(`Deleting email '${thread.getFirstMessageSubject()}': ${thread.getPermalink()}`);
  });
  GmailApp.moveThreadsToTrash(threads);
}
```

### Calendar event deletion

This script deletes calendar events that are 18 months old (or older). It includes an `OTHER_EMAILS`
field that allows a single account to handle auto-deleting events for any other account.

Reference docs are available [here](https://developers.google.com/apps-script/reference/calendar).

Expected workflow:

- Give the `Make changes to events` permission to the account running the script for any calendar
  where you want auto-deletion running. Then add the calendar's email to the `OTHER_EMAILS` array in
  the script. If it's not your primary calendar, you can find its ID/email by going to the
  calendar's settings and looking at the first field under the `Integrate calendar` section.

#### Script

<p></p>

```javascript
const OTHER_EMAILS = [
  'foo@example.com',
  '...',
]

/** Deletes calender events that took place 18 months ago or earlier. */
function processCalendars() {
  for (let calendar of CalendarApp.getAllCalendars()) {
    if (calendar.isOwnedByMe() || OTHER_EMAILS.includes(calendar.getId())) {
      console.log(`Deleting old events in calendar: ${calendar.getName()} (${calendar.getId()})`);
      deleteOldEvents(calendar);
    }
  }
}

function deleteOldEvents(calendar) {
  const epoch = new Date(0);
  const eitghteenMonthsAgo = new Date(
      new Date().getTime() - (1000 * 60 * 60 * 24 * 30 * 18));

  while (true) {
    const oldEvents =
        calendar.getEvents(epoch, eitghteenMonthsAgo, {max: 100});
    if (oldEvents.length == 0) {
      break;
    }

    for (let event of oldEvents) {
      console.log(`Deleting event '${event.getTitle()}' ` +
          `that took place between ${event.getStartTime()} and ${event.getEndTime()}`);
      event.deleteEvent();
    }
  }
}
```

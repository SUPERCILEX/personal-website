---
title: Customize GitHub's code font
subtitle: 😋 code reviews

categories: [Tips, GitHub]
redirect_from:
  - /blog/github-code-font/
---

It occurred to me yesterday that I've spent way too much time nitpicking over my IDE's font, but
then come time for code reviews... not a ligature in sight. Here's a quick guide to change that.

## Prerequisites

Install [Refined GitHub](https://github.com/sindresorhus/refined-github#install). It's probably a
sin at this point to not use that extension. 😉

## Change your font

In Refined GitHub's settings (`chrome://extensions/?options=hlepfoohegkhhmjieoechaddaejaokhf`),
paste in this custom CSS:

```css
/*
The wght@450 part is the font weight.
If you want less or more boldness, decrease or increase this number.
*/
@import url("https://fonts.googleapis.com/css2?family=Fira+Code:wght@450&display=swap");

pre, code, .blob-code, .blob-code-content, .blob-code-marker {
  font-family: 'Fira Code', monospace !important;
}
```

I personally love Fira Code, but you can change this to whatever you want as long as the font is
hosted somewhere.

{% capture before %}
    {% include article-image.html src="/assets/general/default-github-code-font.png" alt="Default GitHub font" %}
{% endcapture %}
{% capture after %}
    {% include article-image.html src="/assets/general/custom-github-code-font.png" alt="Custom GitHub code font" %}
{% endcapture %}

| Before | After |
| --- | --- |
| {{ before | strip_newlines }} | {{ after | strip_newlines }} |

<hr/>

That's it! Enjoy.

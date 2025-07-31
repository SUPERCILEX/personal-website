---
title: Generalizing over mutability in Rust
subtitle: Yes it's cursed

categories: [Tips]
---

You've seen us
[generalize over buffer types](https://blog.sunfishcode.online/writingintouninitializedbuffersinrust/),
now let's generalize over buffer mutability!

I tried to write something like this in a project I'm working on:

```rust
fn process_items<T>(buf: &<mut> [T], mut f: impl FnMut(&<mut> T)) {
    loop {
        ...
        f(&<mut> buf[i]);
    }
}
```

`process_items` abstracts over complexity retrieving items from `buf` and needs to support
processing items both mutably and immutably. Unfortunately, this isn't possible in Rust as far as
I'm aware. I first tried solving the problem with a macro, but couldn't figure out how to generalize
over `&buf[i]` in one macro invocation and `&mut buf[i]` in another.

Thus, it is with great (dis?)pleasure that I present to you: trait magic! Feast your eyes:

```rust
trait Buf<T> {
    type F;

    fn do_(&mut self, f: &mut Self::F, i: usize) -> bool;
}

impl<T, F: FnMut(&T)> Buf<T> for (&[T], PhantomData<F>) {
    type F = F;

    fn do_(&mut self, f: &mut F, i: usize) -> bool {
        let (buf, _) = self;
        if i < buf.len() {
            f(&buf[i]);
            true
        } else {
            false
        }
    }
}

impl<T, F: FnMut(&mut T)> Buf<T> for (&mut [T], PhantomData<F>) {
    type F = F;

    fn do_(&mut self, f: &mut F, i: usize) -> bool {
        let (buf, _) = self;
        if i < buf.len() {
            f(&mut buf[i]);
            true
        } else {
            false
        }
    }
}

fn process_items<T, B: Buf<T>>(mut buf: B, mut f: B::F) {
    let mut i = 0;
    loop {
        if !buf.do_(&mut f, i) {
            break;
        }
        i += 1;
    }
}

fn main() {
    let foo = ["a", "b", "c"];
    process_items((foo.as_slice(), PhantomData), |item| println!("{item}"));
    println!();

    let mut bar = ["a".to_string(), "b".to_string(), "c".to_string()];
    process_items((bar.as_mut_slice(), PhantomData), |item| {
        *item = format!("{item}{item}")
    });
    println!("{bar:?}");
}

```

Here's a
[playground link](https://play.rust-lang.org/?version=stable&mode=debug&edition=2024&gist=3d3d91ab641902137364ebeac7bfe030)
for your convenience.

The example is contrived, but I hope it gets the trick across. If anybody knows of a simpler
solution, I'd be very happy to hear it. :)

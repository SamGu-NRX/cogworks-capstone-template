# CogWorks capstone

Your team's code for all three weeks lives here. One repository, three
directories, one history. Week 1 is audio, Week 2 is vision, Week 3 is
language.

Everything below takes about ten minutes on the first day and then you can
forget it.

## Setup, once

```bash
git clone https://github.com/YOUR-TEAM/YOUR-REPO.git
cd YOUR-REPO
conda activate week1
python -m pip install cogworks-benchmark
cogworks check --benchmark audio-identification
```

`cogworks check` tells you what it found and what is missing. Run it whenever
something feels wrong; it is faster than guessing.

## The one file that matters

Each week directory has a `submission.py`. It is the seam between your code
and the benchmark, and it is the only file whose shape we ask you to keep.
Everything else in your week directory is yours: name it what you want,
structure it how you want, split it across as many files as your team needs.

`submission.py` has one job. It hands the benchmark an object with two or
three named methods, and those methods call your code. It is about ten lines
and it should stay about ten lines. If it starts doing signal processing,
move that into your own module and call it from here.

Open the `submission.py` in your week's directory. It says exactly what to
fill in.

## Running it

```bash
cd week1
cogworks run --benchmark audio-identification
```

That scores you against a small public dataset on your own machine, offline,
as many times as you like. No account, no network, no limit.

When you want the number on the leaderboard:

```bash
cogworks run --benchmark audio-identification --live
```

That reports to the portal as you go. It is still your machine doing the work
and the portal labels it as self-reported, because that is what it is.

The hidden evaluation runs on our infrastructure against data you have never
seen. Start it from the portal or from Discord. You get a limited number of
those, which is the point: they tell you whether the thing works, not whether
this particular tweak helped.

## What each week asks for

| Week | Benchmark id | Your object needs |
| --- | --- | --- |
| 1 | `audio-identification` | `enroll(song_id, samples, sample_rate)`, `identify(samples, sample_rate)` |
| 2 | `vision-recognition` | `enroll(person_id, images)`, `recognize(images)` |
| 2 | `vision-clustering` | `cluster(images, seed=...)` |
| 3 | `language-search` | `embed_text(captions)`, `embed_images(descriptors)`, `prepare_database(image_ids, descriptors)`, `search(query, k)` |

Full signatures, accepted return shapes, and what each metric means are in
each week's `submission.py` and in the benchmark's own README.

## Working as a team

Some notes that come from watching last year's teams, not from a style guide.

**Agree on the seams before you split the work.** The instructor's line was
that making the pieces work together at the end is the hardest part, and the
way to survive it is to decide up front what each piece takes in and hands
back. Write those signatures down on day one, even as empty functions that
`pass`. Then everyone can build against something real.

**Commit small and often, and push.** A commit that says "peak finder finds
peaks" and touches one file is worth more to your team than a commit that says
"stuff" and touches nine. Not for tidiness: because when the integration
breaks on Thursday, small commits let you find the one that broke it.

**Get it running end to end early, badly.** A pipeline that returns the wrong
answer for every query is enormously more useful on Tuesday than three perfect
components that have never been in the same room. Wire the whole thing up with
stubs, run `cogworks run`, watch it score near zero, then improve the pieces.

**Nobody has to understand all of it.** You should be able to explain what
your part does and what it hands the next person. That is the actual bar, and
it is the bar in real engineering too.

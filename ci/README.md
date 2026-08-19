# Turn on the integration check

One command, once, by whoever set up the repository:

    mkdir -p .github/workflows && cp ci/integration.yml .github/workflows/

Commit and push that, and GitHub runs it on every push from then on.

It lives here rather than already being in `.github/workflows/` because the
account that publishes this template cannot write workflow files into it. Two
seconds of your time on day one buys the check for the rest of the month.

## What it does

It does not score you and it does not care whether your answers are right.
It checks two things:

- Every `.py` file still parses. This catches the merge where two people
  renamed the same function in different directions.
- The benchmark can still find each week's `submission.py` and the methods it
  needs. This is the seam that breaks silently: your own tests keep passing
  while the thing that scores you cannot find a method it wants.

Ninety seconds after each push, and it tells you on Tuesday what you would
otherwise find out on Thursday night.

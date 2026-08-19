# Week 3: semantic image search

Type a sentence, get the images it describes.

Your code goes in this directory. `submission.py` has the four methods the
benchmark calls.

## A split that works

| stage | what it owns |
| --- | --- |
| COCO organizer | the json in, the three id mappings out |
| caption embedding | text in, IDF-weighted GloVe vector out |
| training | triples, margin ranking loss, W_embed out, saved to disk |
| search app | a query string in, ranked image ids out |

Training is the long pole and it is one person's week. Everyone else should
be able to work against a randomly initialized W_embed until real weights
exist, so agree on its shape early and save it in a format the search person
can load on day two.

## Two things that cost teams the whole component

A word your training set never saw contributes a zero vector. It does not
raise. Query captions contain words yours did not, and a KeyError in
`embed_text` zeroes the component that the rest of your work feeds.

IDF is computed across every caption in the dataset, once, not per query.

## Reading the score

Three components, weighted equally, because the capstone is three pieces that
have to agree on one embedding space.

- Strong text, weak retrieval means the two embeddings are not living in the
  same space. Look at training.
- Strong retrieval, weak search means the plumbing: the database, the id
  mapping, or the query path. Your embeddings are fine.

That split is the reason both are reported.

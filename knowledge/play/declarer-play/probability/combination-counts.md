---
title: Combination Counts
description: Explains how combinatorial analysis supports familiar bridge probabilities for suit breaks and honor locations.
category: play
subcategory: declarer-play
difficulty: Advanced
tags: 
  - declarer-play
  - finesse
  - probability
systems: []
aliases: []
acronyms: []
references: 
  - acronyms
  - play/counting/counting-index
  - play/declarer-play/general-techniques/finesses/finesse
  - play/declarer-play/general-techniques/finesses/finesses-index
  - play/declarer-play/probability/a-priori-and-a-posteriori-probabilities
  - play/declarer-play/probability/conditional-probability
  - play/declarer-play/probability/missing-honor-probabilities
  - play/declarer-play/probability/percentage-plays
  - play/declarer-play/probability/probability-in-bridge
  - play/declarer-play/probability/probability-index
  - play/declarer-play/probability/restricted-choice
  - play/declarer-play/probability/suit-distributions
  - play/principles/eight-ever-nine-never
  - references/references-index
last_updated: 2026-07-21
status: Draft
---


# Combination Counts

## Overview

Many bridge probabilities are derived from **combinatorial analysis**, the branch of mathematics that counts the number of possible card distributions. By understanding combinations, players can determine how likely suit breaks, honor locations, and specific layouts are.

Fortunately, declarers do **not** need to perform these calculations at the table. The purpose of combination counts is to explain **why** familiar bridge percentages are correct and to provide a deeper understanding of probability-based decisions.

---

# What Is a Combination?

A **combination** is a selection of objects where the **order does not matter**.

In bridge:

- We care **which cards** each defender holds.
- We do **not** care in which order those cards were dealt.

For example:

```
West: ♠Q ♠10
```

is the same layout as:

```
West: ♠10 ♠Q
```

Both represent a single combination.

---

# Why Combination Counts Matter

Combination counts are used to determine:

- Suit distribution probabilities.
- Honor locations.
- Percentage plays.
- Odds of successful finesses.
- Probability of various trump breaks.
- Expected distributions after the auction.

Every standard bridge percentage ultimately comes from counting combinations.

---

# The Combination Formula

The number of ways to choose **r** cards from **n** cards is given by:

> **n choose r**

Mathematically:

\[
\binom{n}{r}
=
\frac{n!}{r!(n-r)!}
\]

where:

- **n** = total number of cards
- **r** = cards chosen
- **!** denotes factorial

Bridge players rarely calculate this during play, but it underlies all distribution probabilities.

---

# Example 1 – Two Missing Cards

Suppose two cards are missing.

Possible distributions:

```
1–1
2–0
```

Combination analysis shows:

| Split | Approximate Probability |
|--------|------------------------:|
| 1–1 | 52% |
| 2–0 | 48% |

Thus, an even split is only slightly more likely.

---

# Example 2 – Five Missing Cards

Missing cards:

```
Q J 10 9 8
```

Possible splits:

```
3–2
4–1
5–0
```

Combination counts produce the familiar bridge probabilities:

| Split | Approximate Probability |
|--------|------------------------:|
| 3–2 | 68% |
| 4–1 | 28% |
| 5–0 | 4% |

These percentages are not guesses—they result directly from counting all possible combinations.

---

# Example 3 – Six Missing Cards

Possible distributions:

```
3–3
4–2
5–1
6–0
```

Combination analysis gives approximately:

| Split | Probability |
|--------|------------:|
| 4–2 | 48% |
| 3–3 | 36% |
| 5–1 | 15% |
| 6–0 | 1% |

This explains why experienced players do **not** automatically expect a 3–3 split.

---

# Honor Locations

Combination counts also determine the probability of missing honors.

Example:

Missing:

```
Q J
```

Possible layouts include:

- Both with West.
- Both with East.
- Split between defenders.

The likelihood of each arrangement depends on the number of possible combinations consistent with each layout.

Later, principles such as **Restricted Choice** modify these initial probabilities.

---

# Relationship to Suit Distribution

Suit distribution probabilities are calculated using combination counts.

For example:

- Why is a 3–2 split more likely than 4–1?
- Why is a 5–3 split slightly more likely than 4–4?
- Why is a 2–1 split overwhelmingly more common than 3–0?

The answer lies in the number of different combinations that produce each distribution.

---

# Relationship to Conditional Probability

Combination counts describe the probabilities **before** information is known.

As the auction and play reveal additional information, players move from pure combination analysis to **conditional probability**.

At that point, counting, Restricted Choice, and Vacant Spaces become more important than the original combination counts.

---

# Practical Applications

Combination counts help explain:

- Percentage plays.
- Finesse odds.
- Trump-break probabilities.
- Long-suit establishment.
- Safety plays.
- Honor-location probabilities.

Although the calculations are rarely performed during play, understanding their results improves judgment.

---

# Memorize the Results, Not the Mathematics

Most experienced players memorize the resulting percentages rather than the formulas.

Examples include:

- Five missing cards break 3–2 about 68% of the time.
- Four missing cards break 3–1 more often than 2–2.
- A 5–3 split is slightly more common than 4–4.

Knowing these percentages is far more valuable at the table than performing calculations.

---

# Common Mistakes

- Assuming all distributions are equally likely.
- Confusing combinations with permutations.
- Ignoring information revealed during the auction.
- Continuing to rely on combination counts after counting the defenders' hands.
- Forgetting that Restricted Choice and Vacant Spaces modify the original probabilities.

---

# Related Topics

- Probability in Bridge
- Suit Distribution Probabilities
- Conditional Probability
- Percentage Plays
- Restricted Choice
- Vacant Spaces
- Missing Honor Probabilities
- A Priori and A Posteriori Probabilities
- Eight Ever, Nine Never

---

# Key Principles

- Combination counts are the mathematical foundation of bridge probabilities.
- Standard percentage tables are derived from counting all possible card combinations.
- Suit distribution and honor-location probabilities originate from combinatorial analysis.
- Once information becomes available, conditional probability replaces pure combination counts.
- At the table, memorize the resulting percentages rather than the mathematical formulas.

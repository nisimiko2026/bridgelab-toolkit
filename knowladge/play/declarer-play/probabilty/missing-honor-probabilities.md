---
title: Missing Honor Probabilities
description: Explains probability-based decisions for locating missing honors and choosing between finesses, drops, and other lines.
category: probability
subcategory: declarer-play
difficulty: Intermediate
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
  - play/declarer-play/planning/planning-index
  - play/declarer-play/planning/planning-the-play
  - play/declarer-play/probabilty/probability-inference
  - play/declarer-play/probabilty/conditional-probability
  - play/declarer-play/probabilty/percentage-plays
  - play/declarer-play/probabilty/probability-in-bridge
  - play/declarer-play/probabilty/probability-index
  - play/declarer-play/probabilty/restricted-choice
  - play/declarer-play/probabilty/suit-distributions
  - play/defence/signaling/count
  - play/play-index
  - play/principals/eight-ever-nine-never
  - references/references-index
last_updated: 2026-07-21
status: Draft
---


# Missing Honor Probabilities

## Overview

Many bridge decisions depend on locating one or more **missing honors**. Declarer must decide whether to finesse, play for the drop, rely on a suit break, or choose another line of play.

Before any information is available, these decisions are based on **a priori probabilities**. As the auction and play reveal additional information, declarer should update those probabilities using **conditional probability**, **Restricted Choice**, **Vacant Spaces**, and **counting**.

Understanding the probabilities associated with missing honors is one of the foundations of expert card play.

---

# The Starting Point

When no information is available:

- Each opponent is equally likely to hold a missing honor.
- Suit distribution probabilities determine the likelihood of different layouts.
- Percentage play is based on these mathematical odds.

These probabilities serve as the starting point—not the final answer.

---

# A Single Missing Honor

Suppose you are missing only the queen.

Example:

```
Dummy
♠ A J 8 4

Declarer
♠ K 7 6 3
```

Missing:

```
♠Q
```

Initially:

- West: approximately 50%
- East: approximately 50%

Without additional information, either defender is equally likely to hold the queen.

---

# Two Missing Honors

Example:

```
Dummy
♦ A J 8 5

Declarer
♦ K 7 6 4
```

Missing:

```
♦Q10
```

Possible layouts include:

- Q10 together.
- Queen and ten split.
- Singleton queen.
- Singleton ten.

The best line depends on:

- Suit length.
- Distribution probabilities.
- Restricted Choice.
- Information from the auction.

---

# Three Missing Honors

Example:

Missing:

```
K Q J
```

Possible positions increase rapidly.

Declarer should consider:

- Which honors are likely to be together.
- Whether one defender has shown length.
- Whether the auction favors one opponent.

---

# Finesse vs. Playing for the Drop

A common probability decision is whether to:

- Take a finesse.
- Cash high cards and hope the missing honor falls.

Example:

```
Dummy
♥ A J 8 5

Declarer
♥ K 7 6 4
```

Missing:

```
♥Q
```

The best percentage play depends on:

- Number of cards held.
- Suit distribution.
- Additional information.

The guideline "Eight Ever, Nine Never" summarizes the basic percentages when no further clues exist.

---

# Missing Touching Honors

Example:

Missing:

```
QJ
```

If one opponent plays the jack, **Restricted Choice** changes the probability that the same opponent also holds the queen.

Without Restricted Choice:

Both layouts are equally likely.

After one honor appears:

The probability changes.

---

# Effect of the Auction

The auction frequently changes honor probabilities.

Example:

West opens:

```
1♠
```

West is now more likely to hold:

- Spade honors.
- Additional high-card points.
- Longer spades.

The original 50–50 assumption is no longer valid.

---

# Effect of Suit Distribution

Suppose:

West has shown:

- Six clubs.
- Four hearts.

West has relatively few unknown cards remaining.

East therefore becomes more likely to hold missing honors in the other suits.

This is an application of the **Vacant Spaces Principle**.

---

# Effect of Card Play

As defenders follow suit, declarer learns:

- Original distribution.
- Number of remaining cards.
- Possible honor locations.

Each revealed card changes the probability of where the missing honors are located.

---

# Combining Information

Expert declarers combine several sources of information:

1. Basic percentages.
2. Suit distribution.
3. Auction.
4. Counting.
5. Restricted Choice.
6. Vacant Spaces.
7. Defensive carding.

The strongest inference usually comes from combining several of these rather than relying on any single principle.

---

# Example 1

You hold:

```
♣ A J 8 4

♣ K 7 6 3
```

Missing:

```
♣Q
```

No information:

Take the normal percentage play.

---

# Example 2

West opens:

```
1♣
```

The missing queen of clubs is now more likely to be with West.

The probability has changed because of the auction.

---

# Example 3

West shows out on the second round of diamonds.

A missing diamond honor is now much more likely to be with East.

Counting has replaced the original percentage estimate.

---

# Example 4

You need to locate:

```
♠QJ
```

West plays the jack.

Restricted Choice now makes it less likely that West also holds the queen.

---

# Common Mistakes

- Assuming missing honors are always equally divided.
- Ignoring information from the auction.
- Forgetting to count defenders' distributions.
- Ignoring Restricted Choice.
- Ignoring Vacant Spaces.
- Continuing to rely on memorized percentages after new evidence appears.

---

# Related Topics

- Probability in Bridge
- Conditional Probability
- Restricted Choice
- Vacant Spaces
- Suit Distribution Probabilities
- Percentage Plays
- Eight Ever, Nine Never
- Counting
- Finessing
- Planning the Play

---

# Key Principles

- Basic honor probabilities provide only the starting point for analysis.
- Every bid and every played card changes the likelihood of where missing honors are located.
- Restricted Choice and Vacant Spaces are powerful tools for locating unseen honors.
- Counting often converts probability into near certainty.
- The best bridge decisions combine mathematics with inference, observation, and careful planning.

---
title: Fourth-Best Leads
description: Explains fourth-best opening leads and the information they provide about a defender's suit length.
category: play
subcategory: defence
difficulty: Beginner
tags: 
  - defence
  - defence/opening-leads
  - lead
  - notrump
  - opening
  - ruff
systems: []
aliases: []
acronyms: []
references: 
  - acronyms
  - bidding/principles/partnership/partnership-agreements
  - play/counting/counting-index
  - play/declarer-play/notrump-play/establishing-long-suits
  - play/defence/index-defence
  - play/defence/opening-leads/honor-leads/index-honor-leads
  - play/defence/opening-leads/leads-against-suit
  - play/defence/opening-leads/opening-leads-index
  - play/defence/opening-leads/rusinow
  - play/defence/opening-leads/top-of-nothing
  - play/defence/opening-leads/third-fifth
  - play/defence/signaling/count
  - references/references-index
last_updated: 2026-07-21
status: Draft
---


# Fourth-Best Leads

## Overview

**Fourth-Best Leads** are the most widely used opening lead agreement in bridge. When leading from a suit that does **not** contain a touching honor sequence, the defender leads the **fourth-highest card**.

The convention is used primarily against **notrump contracts**, where establishing long suits is often the defenders' main objective. Many partnerships also use fourth-best leads against suit contracts when they are not making a trump lead or leading an honor sequence.

Fourth-best leads provide partner with valuable information about the length and strength of the suit while helping establish long-suit tricks.

---

# Basic Principle

Lead the **fourth-highest card** from a suit headed by one or more honors when there is no agreed honor-sequence lead.

Examples:

| Holding | Lead |
|---------|------|
| A J 9 7 4 | 7 |
| K 10 8 5 2 | 5 |
| Q J 8 5 | Q (honor sequence) |
| Q 10 7 4 2 | 4 |
| A Q 8 6 3 | 6 |

If the suit contains a **touching honor sequence**, the agreed honor lead takes precedence.

---

# Why Use Fourth-Best?

Fourth-best leads help partner:

- Estimate the leader's suit length.
- Count remaining cards in the suit.
- Apply the Rule of Eleven.
- Decide whether to continue the suit.
- Plan defensive communications.

They also preserve higher spot cards for later tricks.

---

# The Rule of Eleven

When a defender leads the fourth-highest card, partner can estimate how many cards higher than the lead are held by the other three players.

**Rule:**

> **11 − (spot card led) = Number of higher cards in the remaining three hands.**

### Example

Leader leads:

```
♠6
```

Calculation:

```
11 − 6 = 5
```

There are **five cards higher than the 6** among dummy, declarer, and partner.

If dummy has three higher cards and partner has one, declarer has only one.

This often allows partner to determine whether to play high or low at trick one.

---

# Example 1

Holding:

```
♠ A J 9 7 4
```

Lead:

```
♠7
```

The 7 is the fourth-highest card.

---

# Example 2

Holding:

```
♦ K 10 8 5 2
```

Lead:

```
♦5
```

Partner knows the lead is fourth-best and can begin counting the suit.

---

# Example 3

Holding:

```
♣ A Q 8 6 3
```

Lead:

```
♣6
```

Although there are honors, they are **not touching**, so fourth-best is the normal lead.

---

# Honor Sequences Take Priority

Fourth-best is **not** used from touching honor sequences.

Examples:

| Holding | Normal Lead |
|---------|-------------|
| A K Q | A (or K under Rusinow) |
| K Q J | K |
| Q J 10 | Q |
| J 10 9 | J |

These honor leads give partner more accurate information than a fourth-best lead.

---

# Against Notrump Contracts

Fourth-best leads are especially effective because:

- Long suits often become winners.
- Declarer cannot ruff established tricks.
- Suit-length information is highly valuable.
- The Rule of Eleven applies.

This is the environment in which the convention is most commonly used.

---

# Against Suit Contracts

Many partnerships still use fourth-best leads from long suits, but suit contracts introduce additional considerations:

- Trump leads.
- Singleton leads seeking a ruff.
- Passive leads.
- Top of Nothing agreements.
- Rusinow honor leads.

The auction often influences the choice more than the lead convention.

---

# Advantages

- Internationally recognized standard.
- Supports the Rule of Eleven.
- Gives partner useful suit-length information.
- Preserves higher spot cards.
- Works well with standard honor leads.

---

# Disadvantages

- Sometimes reveals suit length to declarer.
- Less informative than some expert methods (such as Third-and-Fifth).
- Can be less effective against suit contracts where ruffing is important.
- Requires partner to remember the Rule of Eleven for maximum benefit.

---

# Partnership Agreements

Before using fourth-best leads, discuss:

- Against notrump only or all contracts?
- Honor-sequence leads.
- Interior sequence leads.
- Ace and king lead agreements.
- Rusinow or standard honor leads.
- Top of Nothing.
- Doubleton and singleton leads.
- Trump lead philosophy.

---

# Common Mistakes

- Leading fourth-best from a touching honor sequence.
- Forgetting that the Rule of Eleven applies only when fourth-best is being used.
- Applying fourth-best when another agreed lead takes precedence.
- Ignoring information from the auction.
- Assuming every low lead is fourth-best without partnership agreement.

---

# Comparison with Other Lead Methods

| Method | Main Principle | Typical Use |
|---------|----------------|-------------|
| Fourth-Best | Fourth-highest from length | Standard, especially vs. notrump |
| Third-and-Fifth | Third from odd, fifth from even | More precise suit-length information |
| Top of Nothing | Highest from a suit with no honors | Primarily vs. suit contracts |
| Rusinow | Second-highest from touching honor sequence | Expert partnerships |

---

# Related Topics

- Opening Leads
- Leads Against Notrump
- Leads Against Suit Contracts
- Rule of Eleven
- Third-and-Fifth Leads
- Rusinow Leads
- Top of Nothing
- Interior Sequence Leads
- Ace and King Leads

---

# Key Principles

- Lead the **fourth-highest card** from a long suit that does not contain a touching honor sequence.
- Honor-sequence leads always take precedence over fourth-best.
- Fourth-best leads are primarily used against **notrump contracts**.
- The **Rule of Eleven** helps partner interpret fourth-best leads.
- Always combine the lead convention with the information revealed by the auction.

---

## Source Contract for Implementation

### Rule name

Fourth-best card treatment within an independently selected suit.

### Scope

- **Decision stage:** opening lead only. This article does not define later defensive leads.
- **Contract type:** primarily notrump. The article says some partnerships also use the method against suit contracts, so suit-contract use requires an additional explicit partnership agreement.

### Policy dependency

The partnership must explicitly select the **FOURTH_BEST** length-lead method. Missing or unknown policy does not imply fourth-best.

### Trigger

This is a **card-within-suit** treatment, not a suit-selection rule. It applies only after another source-grounded rule or explicit input has already selected a suit, and only when that selected suit has at least four cards and does not contain a touching honor sequence whose agreed honor lead takes precedence.

The four-card minimum follows directly from the meaning of “fourth-highest.” This article does not choose among multiple suits in the leader's hand.

### Card choice

Within the independently selected qualifying suit, lead the fourth-highest card when its cards are ordered from highest rank to lowest rank.

### Exceptions and unresolved boundaries

- A touching honor sequence uses the partnership's agreed honor lead instead.
- Singleton, doubleton, and three-card holdings do not contain a fourth-highest card and therefore do not satisfy this treatment's trigger.
- Trump leads, partner's bid suit, passive-versus-active selection, unsupported-honor choices, and selection among multiple eligible suits are outside this rule.
- Suit-contract use is unresolved without an additional partnership agreement.

### Precedence

This article explicitly gives the agreed touching-honor-sequence lead precedence **within the selected suit**. It does not establish a universal priority among different candidate suits or among singleton, partner-suit, trump, passive, and aggressive leads.

### Source evidence

This contract restates the article's existing **Overview**, **Basic Principle**, **Honor Sequences Take Priority**, **Against Notrump Contracts**, **Against Suit Contracts**, and **Partnership Agreements** sections. It introduces no external bridge rule.

### Implementation status

**POLICY_PARTIAL.** Once a qualifying suit is independently selected, the card treatment is unique and requires no hidden cards or probability model. A full `OpeningLeadState`-to-card recommendation is not executable because this article does not select the suit and the current policy does not resolve contract scope.

# BridgeLab — Source Authority Contract Design

## 1. Purpose

This document defines the proposed Source Authority Contract for BridgeLab.

The contract separates four concepts that must not be conflated:

1. repository provenance,

2. source readiness,

3. source authority,

4. capability coverage.

This is a design artifact only.

It does not authorize any new production capability, change any bridge rule,

change any probability formula, or upgrade the authority classification of any

currently registered production capability.

\---

## 2. Evidence Baseline

The design is based on the current audited repository state.

Current production inventory:

\- bidding routes: 45

\- registered probability engines: 1

\- declarer techniques: 1

\- defensive algorithms: 0

\- opening-lead algorithms: 0

\- total registered production capabilities considered by the provenance audit: 47

Current cross-layer interface gaps previously selected for remediation are zero.

Current full regression baseline:

\- 2007 passed

\- 143 subtests passed

\- 0 failed

The seven previously deferred capability areas remain deferred:

1. Restricted Choice

2. Vacant Places

3. Second Hand Low

4. Third Hand High

5. Standard Honor Lead

6. Natural 1NT responder expansion

7. Safety Play

Nothing in this design changes those dispositions.

\---

## 3. Evidence Review Findings

### 3.1 Phase 17A Source Readiness

Phase 17A defines source-readiness classifications such as:

\- SOURCE\_EXECUTABLE

\- SOURCE\_PARTIAL

\- POLICY\_REQUIRED

\- PARTNERSHIP\_DEPENDENT

\- PROBABILITY\_REQUIRED

\- EXCEPTION\_INCOMPLETE

\- AMBIGUOUS\_ACTION

\- LOW\_SAMPLE

\- NOT\_PRESENT

\- ARCHITECTURE\_BLOCKED

These classifications describe whether available material is sufficiently

bounded to support deterministic implementation.

They do not establish that the underlying source is authoritative.

The only SOURCE\_EXECUTABLE candidates recorded by Phase 17A are the existing

production baselines:

\- SIMPLE\_UNBLOCK\_KING

\- KNOWN\_CARD\_COUNT

SOURCE\_EXECUTABLE must therefore not be interpreted as SOURCE\_AUTHORITATIVE.

\---

### 3.2 Phase 17 Historical Provenance

Historical Phase 17 provenance authenticates recorded repository artifacts.

Blob-pinned or AUTHORIZED historical artifacts establish artifact identity.

They do not establish bridge-theory authority.

Historical validation also records that required Phase 17 source snapshots were

not fully preserved.

Therefore:

AUTHORIZED\_ARTIFACT != AUTHORITATIVE\_BRIDGE\_SOURCE

\---

### 3.3 Core Provenance Contract

The existing ProvenanceValidator validates repository identity properties such

as:

\- approved repository path,

\- tracked state,

\- clean state,

\- Git commit relationship,

\- expected blob identity.

Its AUTHORIZED status means that an artifact or source matches the provenance

manifest requirements.

It does not mean that the content is professionally authoritative.

Therefore:

PROVENANCE\_AUTHORIZED != SOURCE\_AUTHORITY\_ESTABLISHED

\---

### 3.4 KnowledgeSource References

Existing KnowledgeSource references provide linkage between implementation

decisions and knowledge artifacts.

Such linkage is useful provenance evidence.

However, a KnowledgeSource reference alone does not establish:

\- author authority,

\- publisher authority,

\- organizational authority,

\- edition identity,

\- publication identity,

\- external authenticity,

\- bridge-theory correctness,

\- exact capability coverage.

Therefore:

KNOWLEDGE\_SOURCE\_LINK != SOURCE\_AUTHORITY\_ESTABLISHED

\---

### 3.5 References Index

The knowledge References index describes a planned reference-library structure

including bibliography and organizations.

Its "Single Source of Truth" principle means a canonical BridgeLab location for

a factual topic.

It must not be interpreted as external professional authority.

The planned bibliography directory is not present in the current checkout.

Therefore no existing bibliography repository can currently establish source

authority for production capabilities.

\---

## 4. Current Authority State

For the current 47 registered production capabilities:

SOURCE\_AUTHORITY = UNKNOWN

This is the truthful current state.

No capability may be upgraded merely because it:

\- is implemented,

\- is SOURCE\_EXECUTABLE,

\- has deterministic tests,

\- has a KnowledgeSource reference,

\- is stored in a tracked Markdown file,

\- is Git-clean,

\- has a provenance manifest,

\- is blob-pinned,

\- or has ProvenanceStatus.AUTHORIZED.

\---

## 5. Proposed Authority Taxonomy

The Source Authority Contract should use the following authority states.

### UNKNOWN

There is insufficient evidence to establish the authority of the supporting

source.

This is the default state.

### SUPPORTING\_ONLY

A source is identifiable and useful as supporting material, but the evidence

does not justify treating it as an authoritative basis for the capability.

Examples may include internally authored explanations or secondary educational

material whose authority has not been independently established.

This state does not authorize production expansion.

### PARTNERSHIP\_DEPENDENT

The behavior is governed materially by partnership agreement rather than by a

single universal bridge authority.

A source may document the method, but the capability requires an explicit

partnership-policy dependency.

Authority must not be inferred from popularity or convention naming.

### EXISTING\_AUTHENTICATED\_CLASSIFICATION

A source has passed the Source Authority Contract requirements for the exact

classification being claimed.

This state must be evidence-derived.

It must never be assigned from source path, filename, repository presence,

SourceReadinessClassification, or Git provenance alone.

\---

## 6. Source Identity Contract

Before a source can support an authenticated authority classification, its

identity must be reproducibly recorded.

Where applicable, source identity should contain:

\- source type,

\- title,

\- author or responsible organization,

\- publisher or issuing organization,

\- edition or version,

\- publication date or revision date,

\- stable external identifier where available,

\- ISBN where applicable,

\- stable URL where applicable,

\- access or retrieval date for online material where relevant,

\- repository snapshot or preserved representation where legally and

&#x20; operationally appropriate.

Not every source type requires every field.

Missing fields must remain explicitly missing rather than being invented.

\---

## 7. Proposed Source Types

The contract should distinguish source type from authority state.

Possible source types include:

\- OFFICIAL\_LAWS

\- OFFICIAL\_ORGANIZATION\_PUBLICATION

\- SYSTEM\_DOCUMENTATION

\- PUBLISHED\_BOOK

\- TECHNICAL\_ARTICLE

\- EDUCATIONAL\_REFERENCE

\- INTERNAL\_BRIDGELAB\_KNOWLEDGE

\- HISTORICAL\_REPOSITORY\_ARTIFACT

\- PARTNERSHIP\_AGREEMENT

\- UNKNOWN\_SOURCE\_TYPE

Source type alone does not establish authority.

For example, PUBLISHED\_BOOK does not automatically mean authoritative for every

claim contained in that book.

\---

## 8. Authority Evidence Requirements

An authenticated authority classification requires evidence sufficient to

answer all applicable questions below.

### Identity

Can the exact source be identified reproducibly?

### Authenticity

Is there evidence that the identified source is genuinely the claimed

publication, organization document, edition, or version?

### Relevance

Does the source actually address the capability or rule being evaluated?

### Scope

Is the relevant rule limited to a system, jurisdiction, partnership agreement,

competition format, or other context?

### Precision

Does the source support the exact claim being made, rather than only a related

general principle?

### Exceptions

Are material exceptions and qualifications represented?

### Version

Can the applicable edition/version/date be determined where version differences

could affect the rule?

### Preservation

Can future audits determine what evidence was used for the classification?

Failure of an applicable requirement prevents an authenticated authority

classification.

\---

## 9. Capability Coverage Contract

Source authority and capability coverage are separate dimensions.

A source may be authoritative but cover only part of a capability.

Proposed coverage states:

### EXACT

The cited evidence supports the exact production behavior, including applicable

trigger, action, scope, and material exceptions.

### PARTIAL

The source supports part of the production behavior but leaves relevant

conditions, exceptions, precedence, policy, or deterministic action unresolved.

### NOT\_ESTABLISHED

No adequate claim-to-source coverage mapping has been demonstrated.

### UNKNOWN

The available evidence is insufficient even to determine the appropriate

coverage classification.

Coverage must be established at the capability level and, where necessary, at

the rule or decision level.

\---

## 10. Claim-to-Source Mapping

A future authority implementation should not merely attach a bibliography entry

to an entire module.

It should permit an auditable mapping:

CAPABILITY

&#x20;   -> RULE OR DECISION

&#x20;       -> CLAIM

&#x20;           -> SOURCE

&#x20;               -> SOURCE LOCATION

Source location may be represented by an appropriate stable locator such as:

\- section,

\- chapter,

\- page,

\- heading,

\- rule number,

\- law number,

\- paragraph,

\- or other reproducible locator.

The locator must not be invented when unavailable.

\---

## 11. Separation from Repository Provenance

Repository provenance and source authority must remain separate contracts.

Repository provenance answers:

"Is this the exact repository artifact we intended to use?"

Source authority answers:

"What evidence supports treating this source as an appropriate authority for

this bridge claim?"

Both may be required.

Neither substitutes for the other.

\---

## 12. Separation from Source Readiness

Source readiness answers:

"Is the available material sufficiently complete and deterministic to support

implementation?"

Source authority answers:

"Is the supporting source sufficiently identified, authenticated, relevant, and

appropriate for the authority classification being claimed?"

A capability may therefore be:

\- source-ready but authority-unknown,

\- authoritative but source-partial,

\- both established,

\- or neither established.

No automatic conversion between these dimensions is permitted.

\---

## 13. Partnership-Dependent Material

Bridge contains methods whose meaning depends on partnership agreement.

Examples may include:

\- signaling methods,

\- lead agreements,

\- convention variants,

\- inquiry structures,

\- forcing/non-forcing agreements.

For such capabilities, the contract must preserve the partnership dependency.

External authority may establish that a method exists or describe its standard

form.

It cannot establish that a particular partnership uses that method.

Production behavior requiring such an agreement must depend on explicit policy

or partnership configuration.

\---

## 14. Official Rules Versus Bridge Technique

Official laws and regulations must be distinguished from instructional bridge

technique.

An official bridge organization may be authoritative for laws, regulations,

competition procedures, or its own published system definitions.

That status must not automatically be extended to unrelated bidding judgment,

declarer technique, defensive technique, probability formulas, or partnership

methods.

Authority is claim-specific.

\---

## 15. Probability Authority

Probability capabilities require additional discipline.

A probability source must not be treated as sufficient merely because it

mentions a percentage or familiar bridge principle.

For production probability behavior, the evidence must establish the applicable:

\- sample space,

\- conditioning assumptions,

\- known information,

\- excluded information,

\- formula or deterministic calculation,

\- precision representation,

\- and rounding behavior where relevant.

Restricted Choice and Vacant Places remain deferred until their existing

reopen gates are independently satisfied.

This contract does not weaken those gates.

\---

## 16. No-Invention Rules

The authority layer must never invent:

\- authors,

\- publishers,

\- editions,

\- ISBNs,

\- URLs,

\- publication dates,

\- quotations,

\- page numbers,

\- source classifications,

\- source authority,

\- capability coverage,

\- formulas,

\- bridge rules,

\- exceptions,

\- partnership agreements,

\- or missing source snapshots.

Absence of evidence must remain visible.

UNKNOWN is an acceptable and expected result.

\---

## 17. Public Observability

Future implementation may expose source-authority information through the

existing public provenance/source observability path.

However, public exposure must distinguish:

\- repository provenance,

\- source identity,

\- authority state,

\- coverage state.

The interface must not use ambiguous wording such as "authorized source" when

the underlying fact is only Git provenance authorization.

No public schema change is authorized by this design document.

A separate implementation design must define any serialization change.

\---

## 18. Migration Rule for Existing Production Capabilities

All existing 47 production capabilities begin migration with:

authority = UNKNOWN

and must retain their currently established coverage state unless fresh evidence

supports a change.

Migration must be evidence-first and capability-by-capability.

No bulk authority upgrade is permitted.

No inference from common bridge knowledge is permitted.

No inference from existing production status is permitted.

\---

## 19. Evidence Acquisition

A future evidence-acquisition milestone may populate a bibliography or source

registry.

Such work must:

1. identify candidate sources,

2. preserve exact source identity,

3. distinguish official from secondary material,

4. map sources to claims,

5. record unresolved fields,

6. classify authority conservatively,

7. establish coverage separately,

8. preserve reproducible evidence where permitted.

Acquiring a source does not itself authorize a production change.

\---

## 20. Implementation Gate

Implementation of a Source Authority layer is justified only if the design can

be represented without falsely upgrading existing evidence.

Minimum implementation requirements:

1. immutable authority/source identity contracts,

2. conservative UNKNOWN defaults,

3. explicit separation from ProvenanceStatus.AUTHORIZED,

4. explicit separation from SourceReadinessClassification,

5. capability-level coverage representation,

6. deterministic serialization if publicly exposed,

7. tests proving absence is not converted into authority,

8. no production bridge behavior changes,

9. no new bridge rules,

10. no new probability formulas.

\---

## 21. Production Expansion Gate

Source Authority implementation does not itself authorize production expansion.

A deferred or new capability may enter production only after all of its

independent gates are satisfied, including as applicable:

\- source identity,

\- source authority,

\- exact or explicitly acceptable coverage,

\- source readiness,

\- deterministic trigger/action contract,

\- bounded exceptions,

\- policy requirements,

\- architecture readiness,

\- probability contract,

\- legal-state constraints,

\- deterministic fixtures,

\- regression protection.

\---

## 22. Current Design Verdict

Evidence review establishes:

SOURCE\_AUTHORITY\_CONTRACT = NOT\_PRESENT

BIBLIOGRAPHY\_EVIDENCE = NOT\_PRESENT

CURRENT\_PRODUCTION\_AUTHORITY\_CLASSIFICATION = UNKNOWN\_FOR\_ALL\_47

EXISTING\_GIT\_PROVENANCE\_CONTRACT = PRESENT

EXISTING\_SOURCE\_READINESS\_CONTRACT = PRESENT

SOURCE\_AUTHORITY\_IS\_DISTINCT\_FROM\_BOTH = TRUE

CURRENT\_PRODUCTION\_BEHAVIOR\_CHANGE\_REQUIRED = NO

CURRENT\_PRODUCTION\_EXPANSION\_AUTHORIZED = NO

\---

## 23. Recommended Next Step

The next step after review of this design should be a narrow implementation

feasibility audit.

That audit should determine the smallest architecture capable of representing:

\- source identity,

\- authority state,

\- coverage state,

\- claim/source linkage,

without changing production bridge behavior and without asserting authority not

supported by evidence.

Only after that audit should BridgeLab decide whether to implement the Source

Authority layer.

\---

## 24. Design Closure Marker

SOURCE\_AUTHORITY\_CONTRACT\_DESIGN\_COMPLETE\_PENDING\_FEASIBILITY\_AUDIT

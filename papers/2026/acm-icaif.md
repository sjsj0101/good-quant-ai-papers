<!-- Generated from data/papers.yaml and data/coverage.yaml by scripts/render.py. Do not edit directly. -->

# ACM ICAIF 2026

**Coverage status:** Pending

**Checked on:** 2026-11-14

**Cataloged eligible papers:** 5

**Tracks checked:** Main

**Tracks pending:** Main (partially screened: Five named main papers verified in targeted batches; the other 207 listed main records remain unadjudicated.) · Workshop (source mapped: Official workshop-paper entry point is linked from the main roster; individual workshop records remain unscreened.)

**Official audit sources:** [Source 1](<https://icaif2026.org/accepted-papers/>) · [Source 2](<https://icaif2026.org/accepted-papers/#paper-772>) · [Source 3](<https://icaif2026.org/accepted-papers/#paper-633>) · [Source 4](<https://icaif2026.org/accepted-papers/#paper-797>) · [Source 5](<https://icaif2026.org/accepted-papers/#paper-1095>) · [Source 6](<https://icaif2026.org/accepted-papers/#paper-1068>)

**Coverage notes:** The official roster lists 212 accepted main papers. Targeted batches verified FlowLOB (oral), One Basket, Many Experts (poster), SAiFE-gym (poster), LOB-Impact Benchmark (oral), and Internalizing Investment Mandates (poster). These five individual checks are not a completed roster screen. The remaining 207 main records and paper-bearing side programs remain pending.

5 verified papers curated for direct relevance to quantitative finance and asset management. Tracks are separated so main-conference, workshop, position, and affinity status remains visible.

[← Back to the main index](../../README.md)

## Main Conference (5)

### [FlowLOB: Efficient and Controllable Limit Order Book Generation with Flow Matching](<https://arxiv.org/abs/2608.13096>)

**Catalog ID:** 2026-acm-icaif-wang-flowlob

**Authors:** Zhuohan Wang, Andreea Bacalum, Ollie Olby, Carmine Ventre, Namid Stillman

**Venue / year:** ACM ICAIF · 2026

**Track / presentation:** Main · Oral

**Status / verified:** Accepted · 2026-11-10

**Topics:** Market Simulation · Synthetic Data · Market Microstructure

**Assets / frequency:** Not specified

**Identifiers:** arXiv 2608.13096

**Focus:** Uses conditional flow matching to synthesize limit-order-book paths, with scenario controls and transfer to held-out instruments.

**Why it matters:** Provides controllable synthetic market trajectories for testing market-microstructure models; the reported comparison concerns HKEX data rather than live trading profitability.

**Notes:** Official main-conference oral roster confirms title and five authors. Content checked against arXiv abstract; code URL not confirmed. This targeted check does not complete ICAIF 2026 coverage.

**Links:** [Official venue record](<https://icaif2026.org/accepted-papers/#paper-772>) · [Paper](<https://arxiv.org/abs/2608.13096>)

---

### [Internalizing Investment Mandates: A Neurosymbolic RL Approach to Portfolio Allocation](<https://arxiv.org/abs/2611.17329>)

**Catalog ID:** 2026-acm-icaif-yildiz-investment-mandates

**Authors:** Zeynep Yıldız, Satchit Chatterji, Ercan Atam, Erman Acar

**Venue / year:** ACM ICAIF · 2026

**Track / presentation:** Main · Poster

**Status / verified:** Accepted · 2026-11-14

**Topics:** Asset Allocation · Portfolio Optimization · Risk Management · Market Regimes

**Assets / frequency:** Not specified

**Identifiers:** arXiv 2611.17329 · DOI 10.1145/3858063.3858904

**Focus:** Trains a continuous portfolio policy with a differentiable Monte Carlo estimate of mandate compliance, using market-regime-dependent allocation rules rather than a separate deployment-time rule-correction layer.

**Why it matters:** Directly evaluates whether portfolio weights satisfy investment mandates. The reported compliance improvement is not a hard guarantee or evidence of a production-ready profitable strategy: the tested setting uses one ETF universe and omits transaction costs and slippage.

**Notes:** Official ICAIF main-conference poster roster confirms title and four authors. Content checked against the author arXiv abstract and selected method/limitations sections; DOI transcribed from the author manuscript, not independently used to claim ACM proceedings publication. Compliance concerns deterministic mean actions; stochastic actions can violate more rules. Code URL not confirmed; no independent reproduction. One targeted addition does not complete the 212-paper roster screen.

**Links:** [Official venue record](<https://icaif2026.org/accepted-papers/#paper-1068>) · [Paper](<https://arxiv.org/abs/2611.17329>)

---

### [LOB-Impact Benchmark: Emergent Market Impact in Generative Limit Order Book Models](<https://arxiv.org/abs/2610.27100>)

**Catalog ID:** 2026-acm-icaif-nigmatulin-lob-impact

**Authors:** George Nigmatulin, Valentin Mohl, Sascha Frey, Kang Li, Aramis Marti-Shahandeh, Mihai Cucuringu, Anisoara Calinescu, Jakob Foerster, Stefan Zohren

**Venue / year:** ACM ICAIF · 2026

**Track / presentation:** Main · Oral

**Status / verified:** Accepted · 2026-11-12

**Topics:** Market Simulation · Market Microstructure · Execution · Evaluation

**Assets / frequency:** Equities

**Identifiers:** arXiv 2610.27100 · DOI 10.1145/3858063.3858909

**Focus:** Tests generative order-book models by injecting execution metaorders and comparing their impact and relaxation with a blind simulator control.

**Why it matters:** Checks whether trading-agent world models respond credibly to the agent’s own orders, rather than matching only historical distributions; tested models did not reproduce impact decay.

**Notes:** Official main roster lists paper 1095 as oral and confirms all nine authors. Content and DOI checked in the author arXiv version, not independently in ACM proceedings. The paper links a code URL that redirects to the canonical lob\_impact repository; opened, not executed. Reported findings concern tested models and stocks, not universal market-impact laws.

**Links:** [Official venue record](<https://icaif2026.org/accepted-papers/#paper-1095>) · [Paper](<https://arxiv.org/abs/2610.27100>) · [Code](<https://github.com/george-nigmatulin/lob_impact>)

---

### [One Basket, Many Experts: Decorrelated Re-ranking for Financial Asset Recommendation](<https://arxiv.org/abs/2611.05952>)

**Catalog ID:** 2026-acm-icaif-unno-one-basket-many-experts

**Authors:** Ryuki Unno, Keigo Sakurai, Koshi Watanabe, Keisuke Maeda, Takahiro Ogawa, Miki Haseyama

**Venue / year:** ACM ICAIF · 2026

**Track / presentation:** Main · Poster

**Status / verified:** Accepted · 2026-11-10

**Topics:** Asset Allocation · Portfolio Optimization · Evaluation

**Assets / frequency:** Not specified

**Identifiers:** arXiv 2611.05952

**Focus:** Re-ranks an expert-following asset list by retaining leading recommendations and replacing selected positions with less-correlated alternatives.

**Why it matters:** Makes the recommendation-relevance versus portfolio-performance trade-off explicit; the authors attribute gains in their dataset to return differences rather than a general reduction in basket volatility.

**Notes:** Official main-conference poster roster confirms title and six authors. Content checked against arXiv abstract; code URL not confirmed. Performance is protocol- and market-phase-dependent; not independently reproduced.

**Links:** [Official venue record](<https://icaif2026.org/accepted-papers/#paper-633>) · [Paper](<https://arxiv.org/abs/2611.05952>)

---

### [SAiFE-gym: Model-based Environments for Automated Market Making with Concentrated Liquidity](<https://arxiv.org/abs/2609.17788>)

**Catalog ID:** 2026-acm-icaif-chionas-saife-gym

**Authors:** Georgios Chionas, Charalampos Kleitsikas, Stefanos Leonardos, Leandro Sánchez-Betancourt, Carmine Ventre

**Venue / year:** ACM ICAIF · 2026

**Track / presentation:** Main · Poster

**Status / verified:** Accepted · 2026-11-11

**Topics:** Market Simulation · Market Microstructure · Asset Allocation · Evaluation

**Assets / frequency:** Crypto

**Identifiers:** arXiv 2609.17788

**Focus:** Provides modular, vectorized environments for learning liquidity-allocation policies in constant-product markets with concentrated liquidity.

**Why it matters:** Makes liquidity ranges, market frictions and uncertain market parameters explicit when evaluating reinforcement-learning market makers; simulation results do not establish live trading profitability.

**Notes:** Official ICAIF main-conference roster lists paper 797 in the poster group, not oral. Five authors and author order verified; arXiv abstract and introduction read. The paper directly links the public SAiFE\_gym code repository; code was not executed.

**Links:** [Official venue record](<https://icaif2026.org/accepted-papers/#paper-797>) · [Paper](<https://arxiv.org/abs/2609.17788>) · [Code](<https://github.com/giorgoschionas/SAiFE_gym>)

---

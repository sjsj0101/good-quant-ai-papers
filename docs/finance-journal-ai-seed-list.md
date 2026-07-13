# Finance Journal AI + Finance Seed List

This is an exploratory watchlist for technical AI, machine learning, and high-dimensional-data papers in finance journals and finance-facing top journals. It is not yet part of the canonical 2024–2026 conference catalog in `data/papers.yaml`.

Verified on: 2026-07-13

## Scope

Primary target journals:

- The Journal of Finance
- Journal of Financial Economics
- The Review of Financial Studies
- Review of Finance
- Journal of Financial and Quantitative Analysis

Adjacent technical venues are included only when the paper is clearly finance-facing and methodologically central, such as Management Science asset-pricing or finance-text papers.

Included themes:

- machine learning for asset pricing and return prediction
- deep learning for asset-pricing models
- high-dimensional factor selection and factor discovery
- market efficiency under big data
- machine learning for fund-manager skill
- machine learning for analyst earnings expectations
- text-as-data and NLP signals with investment relevance
- continuous-time finance problems solved with machine learning

Excluded for now:

- generic AI adoption, FinTech diffusion, governance, and regulation papers
- fraud, credit scoring, payments, accounting QA, and banking operations unless the method is central and the paper appears in a target finance journal
- pure survey or policy pieces without a technical model or empirical method contribution

## High-Priority Core List

| Priority | Paper | Journal | Year | Why it is technical | Finance link | Source |
| --- | --- | --- | ---: | --- | --- | --- |
| Core | Empirical Asset Pricing via Machine Learning — Shihao Gu, Bryan Kelly, Dacheng Xiu | The Review of Financial Studies | 2020 | Benchmarks machine-learning models for conditional expected returns at scale. | Cross-sectional stock-return prediction and empirical asset pricing. | [DOI](https://doi.org/10.1093/rfs/hhaa009) |
| Core | Machine Learning for Continuous-Time Finance — Victor Duarte, Diogo Duarte, Dejanir H. Silva | The Review of Financial Studies | 2024 | Applies machine-learning estimation to continuous-time finance objects. | Continuous-time asset-pricing and financial-econometrics workflows. | [DOI](https://doi.org/10.1093/rfs/hhae043) |
| Core | Machine-Learning the Skill of Mutual Fund Managers — Ron Kaniel, Zihan Lin, Markus Pelger, Stijn Van Nieuwerburgh | Journal of Financial Economics | 2023 | Uses machine learning to infer persistent fund-manager skill from rich fund characteristics and histories. | Mutual-fund selection, manager evaluation, and active-management performance. | [DOI](https://doi.org/10.1016/j.jfineco.2023.07.004) |
| Core | Market Efficiency in the Age of Big Data — Ian W. R. Martin, Stefan Nagel | Journal of Financial Economics | 2022 | Studies information aggregation and efficiency when investors have increasingly large datasets. | Limits and implications of data-driven return prediction. | [DOI](https://doi.org/10.1016/j.jfineco.2021.10.006) |
| Core | Charting by Machines — Scott Murray, Yusen Xia, Houping Xiao | Journal of Financial Economics | 2024 | Machine-extracts and evaluates technical-charting information from price histories. | Price-pattern signals and technical-analysis predictability. | [DOI](https://doi.org/10.1016/j.jfineco.2024.103791) |
| Core, caution | Man versus Machine Learning: The Term Structure of Earnings Expectations and Conditional Biases — Jules H. van Binsbergen, Xiao Han, Alejandro Lopez-Lira | The Review of Financial Studies | 2023 | Builds machine-learning earnings-expectation forecasts and compares them with human analyst expectations. | Analyst forecast bias, earnings expectations, and equity valuation inputs. | [DOI](https://doi.org/10.1093/rfs/hhac085) |
| Core, caution | Man versus Machine Learning Revisited — Yingguang Zhang, Yandi Zhu, Juhani T. Linnainmaa | The Review of Financial Studies | 2025 | Reassesses the Man-versus-Machine-Learning evidence. | Important replication/reassessment companion for the analyst-expectations line. | [DOI](https://doi.org/10.1093/rfs/hhaf066) |
| Core, caution | Expression of Concern: Man versus Machine Learning: The Term Structure of Earnings Expectations and Conditional Biases | The Review of Financial Studies | 2026 | Editorial status notice rather than a research contribution. | Must be tracked before using the 2023 paper as settled evidence. | [DOI](https://doi.org/10.1093/rfs/hhag017) |

## Adjacent but Technically Valuable

| Priority | Paper | Journal | Year | Why it is technical | Finance link | Source |
| --- | --- | --- | ---: | --- | --- | --- |
| Adjacent | Deep Learning in Asset Pricing — Luyang Chen, Markus Pelger, Jason Zhu | Management Science | 2024 | Designs deep-learning asset-pricing models with latent states and nonlinear pricing kernels. | Cross-sectional returns, stochastic discount factors, and asset-pricing tests. | [DOI](https://doi.org/10.1287/mnsc.2023.4695) |
| Adjacent | How Much Can Machines Learn Finance from Chinese Text Data? — Yang Zhou, Jianqing Fan, Lirong Xue | Management Science | 2024 | Uses machine learning/NLP over Chinese financial text. | Text-derived financial prediction and market information extraction. | [DOI](https://doi.org/10.1287/mnsc.2022.01468) |
| Adjacent | Lazy Prices — Lauren Cohen, Christopher Malloy, Quoc Nguyen | The Journal of Finance | 2020 | Uses large-scale textual comparison of corporate disclosures. | Textual disclosure changes as signals for price adjustment and return predictability. | [DOI](https://doi.org/10.1111/jofi.12885) |
| Adjacent | Taming the Factor Zoo: A Test of New Factors — Guanhao Feng, Stefano Giglio, Dacheng Xiu | The Journal of Finance | 2020 | High-dimensional factor-selection and multiple-testing problem, close to statistical ML even if not framed as AI. | Factor discovery and expected-return model selection. | [DOI](https://doi.org/10.1111/jofi.12883) |

## Working-Paper Watch Items

These are not canonical top-journal inclusions yet, but they are likely worth monitoring because they match the technical AI + finance scope.

| Paper | Current status | Why monitor |
| --- | --- | --- |
| Can Machines Learn Weak Signals? — Zhouyu Shen, Dacheng Xiu | NBER / SSRN working paper as of this pass | Likely relevant to weak-signal extraction and ML return prediction. |
| Measuring Firm-Level Inflation Exposure: A Deep Learning Approach — Sudheer Chava, Wendi Du, Agam Shah, Linghang Zeng | SSRN working paper as of this pass | Deep-learning text/exposure measurement; finance-journal publication status still needs verification. |

## Next Search Queue

- Search Review of Finance and JFQA issue archives for `machine learning`, `artificial intelligence`, `deep learning`, `text`, `NLP`, `big data`, and `asset pricing`.
- Separate asset-pricing / investment papers from corporate-finance AI-adoption papers.
- Verify whether any recent 2025–2026 RFS/JFE/JF accepted or advance articles contain `LLM`, `foundation model`, or `generative AI` with direct investment relevance.
- If this watchlist becomes canonical, create a separate schema rather than overloading the existing conference-only `data/papers.yaml`.

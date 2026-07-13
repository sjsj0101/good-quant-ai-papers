# Finance Journal AI + Finance Seed List

This is an EDITH-corpus-backed watchlist for technical AI, machine learning, and high-dimensional-data papers in top finance journals. It is intentionally separate from the canonical 2024–2026 top-conference catalog in `data/papers.yaml`.

Verified on: 2026-07-13

Machine-readable metadata lives in [`data/finance_journal_ai_watchlist.yaml`](../data/finance_journal_ai_watchlist.yaml).

## Local Source Scope

This pass did not use web search. It used the local EDITH literature corpus through the literature module search path and the `v_papers` SQLite view.

| Journal code | Journal | Local records | Local year range |
| --- | --- | ---: | --- |
| `JF` | The Journal of Finance | 3,229 | 1990–2026 |
| `JFE` | Journal of Financial Economics | 3,224 | 1990–2026 |
| `RFS` | The Review of Financial Studies | 2,700 | 1955–2026 |

I did not include Review of Finance or JFQA in this pass because they are not present under distinct `RF` / `JFQA` journal codes in the local EDITH corpus.

## Inclusion Rule

Included papers need a technical AI/ML/high-dimensional-data contribution and a direct link to quantitative finance, asset management, trading, market microstructure, derivatives, asset pricing, or portfolio choice.

Excluded or downgraded:

- generic AI adoption, firm growth, governance, regulation, or entrepreneurship papers;
- generic textual-analysis corporate-finance papers without a direct investment or market-risk link;
- pure survey/editorial pieces unless they are useful context for the technical list.

## Core Quant Finance and Asset Management List

`Year` below is the EDITH local corpus year. Rows marked `year review` need later metadata cleanup because the local year appears inconsistent with the DOI/title context.

| Priority | Paper | Journal | Year | Field | Technical hook | EDITH ID / DOI |
| --- | --- | --- | ---: | --- | --- | --- |
| Core | (Re-)Imag(in)ing Price Trends — Jingwen Jiang, Bryan Kelly, Dacheng Xiu | JF | 2023 | Asset pricing | CNN/image modeling of price charts for return prediction. | `30427` · `10.1111/jofi.13268` |
| Core | Informed Trading Intensity — Vincent Bogousslavsky, Vyacheslav Fos, Dmitriy Muravyev | JF | 2024 | Market microstructure | Gradient-boosted-tree measurement of informed trading intensity. | `8896` · `10.1111/jofi.13320` |
| Core | The Virtue of Complexity in Return Prediction — Bryan Kelly, Semyon Malamud, Kangying Zhou | JF | 2024 | Asset pricing | Random-matrix/ridge-regression argument for complex prediction models. | `9960` · `10.1111/jofi.13298` |
| Core | Sparse Signals in the Cross-Section of Returns — Alexander M. Chinco, Adam D. Clark-Joseph, Mao Ye | JF | 2019 | Asset pricing | LASSO and sparse signal extraction for high-frequency return predictability. | `9134` · `10.1111/jofi.12733` |
| Core | Taming the Factor Zoo: A Test of New Factors — Guanhao Feng, Stefano Giglio, Dacheng Xiu | JF | 2020 | Factor investing | Double-selection LASSO and SDF testing for factor discovery. | `9500` · `10.1111/jofi.12883` |
| Core | Forest through the Trees: Building Cross-Sections of Stock Returns — Svetlana Bryzgalova, Markus Pelger, Jason Zhu | JF | 2025 | Asset pricing | Asset-pricing trees for characteristic interactions and SDF construction. | `8994` · `10.1111/jofi.13477` |
| Core | Anomalies and the Expected Market Return — Xi Dong, Yan Li, David E. Rapach, Guofu Zhou | JF | 2022 | Asset pricing | Elastic-net/ML forecasting with anomaly portfolios. | `9371` · `10.1111/jofi.13099` |
| Core | Equilibrium Data Mining and Data Abundance — Jérome Dugast, Thierry Foucault | JF | 2025 | Asset management | Equilibrium model of big data, data mining, and active management. | `9406` · `10.1111/jofi.13397` |
| Core | Deep surrogates for finance: With an application to option pricing — Hui Chen, Antoine Didisheim, Simon Scheidegger | JFE | 2026 | Derivatives | Deep surrogate modeling for option pricing and tail-risk objects. | `11391` · `10.1016/j.jfineco.2025.104222` |
| Core | Machine learning from a 'Universe' of signals: The role of feature engineering — Bin Li, Alberto G. Rossi, Xuemin Sterling Yan, Lingling Zheng | JFE | 2025 | Asset pricing | Feature engineering and inductive bias in large-signal return prediction. | `12729` |
| Core | Charting by machines — Scott Murray, Yusen Xia, Houping Xiao | JFE | 2024 | Asset pricing | ML/deep-learning extraction of nonlinear price-chart signals. | `12954` · `10.1016/j.jfineco.2024.103791` |
| Core | Missing Values Handling for Machine Learning Portfolios — Andrew Y. Chen, Jack McCoy | JFE | 2024 | Portfolio construction | Missing-data design for ML portfolios across many predictors. | `11354` · `10.1016/j.jfineco.2024.103815` |
| Core | Machine-Learning the Skill of Mutual Fund Managers — Ron Kaniel, Zihan Lin, Markus Pelger, Stijn Van Nieuwerburgh | JFE | 2023 | Asset management | ML and neural networks for mutual-fund skill and fund selection. | `12512` · `10.1016/j.jfineco.2023.07.004` |
| Core | Machine learning and fund characteristics help to select mutual funds with positive alpha — Victor DeMiguel, Javier Gil-Bazo, Francisco J. Nogales, André A.P. Santos | JFE | 2023 | Asset management | Nonlinear ML interactions for tradable positive-alpha mutual-fund selection. | `11649` · `10.1016/j.jfineco.2023.103737` |
| Core | Machine learning in the Chinese stock market — Markus Leippold, Qian Wang, Wenyu Zhou | JFE | 2022 | Factor investing | ML factor/return prediction in China with transaction-cost attention. | `12669` · `10.1016/j.jfineco.2021.08.017` |
| Core | Shrinking the Cross-Section — Serhiy Kozak, Stefan Nagel, Shrihari Santosh | JFE | 2020 | Asset pricing | Shrinkage/SDF estimation in high-dimensional cross sections. | `12606` · `10.1016/j.jfineco.2019.06.008` |
| Core | Market efficiency in the age of big data — Ian W.R. Martin, Stefan Nagel | JFE | 2022 | Asset pricing | High-dimensional prediction model of market efficiency and OOS testing. | `12861` · `10.1016/j.jfineco.2021.10.006` |
| Core | The diversification and welfare effects of robo-advising — Alberto G. Rossi, Stephen Utkus | JFE | 2024 | Portfolio choice | ML/technology adoption in household portfolio diversification. | `13136` · `10.1016/j.jfineco.2024.103869` |
| Core | Empirical Asset Pricing via Machine Learning — Shihao Gu, Bryan Kelly, Dacheng Xiu | RFS | 2020 | Asset pricing | Benchmark ML models for conditional expected returns at scale. | `24800` · `10.1093/rfs/hhaa009` |
| Core, year review | Machine Learning for Continuous-Time Finance — Victor Duarte, Diogo Duarte, Dejanir H. Silva | RFS | 2018 | Continuous-time finance | Deep-learning dynamic programming for high-dimensional continuous-time models. | `24414` · `10.1093/rfs/hhae043` |
| Core, year review | Option Return Predictability with Machine Learning and Big Data — Turan G. Bali, Heiner Beckmeyer, Mathis Mörke, Florian Weigert | RFS | 1996 | Derivatives | Gradient boosting and big-data option-return prediction. | `23687` · `10.1093/rfs/hhad017` |
| Core | Bond Risk Premia with Machine Learning — Daniele Bianchi, Matthias Büchner, Andrea Tamoni | RFS | 2021 | Fixed income | Neural-network bond-return predictability and term-structure signals. | `23847` |
| Core | Dissecting Characteristics Nonparametrically — Joachim Freyberger, Andreas Neuhierl, Michael Weber | RFS | 2020 | Asset pricing | Nonparametric/LASSO estimation of characteristic-return relations. | `24586` · `10.1093/rfs/hhz123` |
| Core | Thousands of Alpha Tests — Stefano Giglio, Yuan Liao, Dacheng Xiu | RFS | 2021 | Asset pricing | Multiple-testing and false-discovery controls for alpha/data mining. | `24691` · `10.1093/rfs/hhaa111` |
| Core | Microstructure in the Machine Age — David Easley, Marcos López de Prado, Maureen O’Hara, Zhibai Zhang | RFS | 2021 | Market microstructure | Random forests, VPIN, and high-frequency cross-asset microstructure. | `24433` · `10.1093/rfs/hhaa078` |
| Core | Risk Price Variation: The Missing Half of Empirical Asset Pricing — Andrew J. Patton, Brian M. Weller | RFS | 2022 | Asset pricing | Clustering/ML view of risk-price variation and market segmentation. | `25511` · `10.1093/rfs/hhac012` |
| Core | Narrative Asset Pricing: Interpretable Systematic Risk Factors from News Text — Leland Bybee, Bryan Kelly, Yinan Su | RFS | 2022 | Asset pricing | Topic modeling/LDA/sparse IPCA for interpretable news-based factors. | `24012` · `10.1093/rfs/hhad042` |
| Core | Confident Risk Premiums and Investments Using Machine Learning Uncertainties — Rohit Allena | RFS | 2023 | Asset pricing | ML uncertainty quantification and confidence intervals for risk premia. | `25736` · `10.1093/rfs/hhaf087` |
| Core, caution | Man versus Machine Learning: The Term Structure of Earnings Expectations and Conditional Biases — Jules H. van Binsbergen, Xiao Han, Alejandro Lopez-Lira | RFS | 2023 | Analyst expectations | ML earnings-expectation forecasts versus human analyst expectations. | `25739` · `10.1093/rfs/hhac085` |
| Core, caution | Man versus Machine Learning Revisited — Yingguang Zhang, Yandi Zhu, Juhani T. Linnainmaa | RFS | 2023 | Analyst expectations | Reassessment of look-ahead bias and ML analyst-forecast evidence. | `25811` · `10.1093/rfs/hhaf066` |
| Core | News and Asset Pricing: A High-Frequency Anatomy of the SDF — Saketh Aleti, Tim Bollerslev | RFS | 2023 | Asset pricing | Neural-network/textual-analysis anatomy of high-frequency news risk premia. | `23563` · `10.1093/rfs/hhae019` |
| Core | Unmasking Mutual Fund Derivative Use — Ron Kaniel, Pingle Wang | RFS | 2022 | Asset management | K-means/ML discovery of mutual-fund derivative use and amplification. | `25104` · `10.1093/rfs/hhaf001` |
| Core | The Market Inside the Market: Odd-Lot Quotes — Robert P. Bartlett, Justin McCrary, Maureen O’Hara | RFS | 2022 | Market microstructure | XGBoost/SHAP study of odd-lot quotes and effective NBBO information. | `23727` · `10.1093/rfs/hhad074` |
| Core | Finding Fortune: How Do Institutional Investors Pick Asset Managers? — Gregory W. Brown, Oleg R. Gredil, Preetesh Kantak | RFS | 2021 | Asset management | ML/NLP applied to due diligence and hedge-fund/asset-manager selection. | `23969` · `10.1093/rfs/hhac090` |
| Core | Approaching Mean-Variance Efficiency for Large Portfolios — Mengmeng Ao, Yingying Li, Xinghua Zheng | RFS | 2019 | Portfolio construction | High-dimensional regression/LASSO for sparse large-portfolio efficiency. | `23620` · `10.1093/rfs/hhy105` |
| Core | Valuing Financial Data — Maryam Farboodi, Dhruv Singal, Laura Veldkamp, Venky Venkateswaran | RFS | 2022 | Financial data economics | Structural/rational-expectations model of financial-data valuation. | `24515` · `10.1093/rfs/hhae034` |

## Secondary Technical Papers Found Locally

These are technically relevant but less central to quant investing or asset management than the core list above.

| Paper | Journal | Year | Why secondary |
| --- | --- | ---: | --- |
| Lazy Prices — Lauren Cohen, Christopher Malloy, Quoc Nguyen | JF | 2020 | Important disclosure-text/NLP return-predictability paper, but the method is more text-as-data than modern ML. |
| Measuring Innovation and Product Differentiation: Evidence from Mutual Funds — Leonard Kostovetsky, Jerold B. Warner | JF | 2020 | Mutual-fund NLP/product differentiation; useful for asset management but not primarily ML forecasting. |
| From Man vs. Machine to Man + Machine: The art and AI of stock analyses — Sean Cao, Wei Jiang, Junbo Wang, Baozhong Yang | JFE | 2024 | AI stock-analysis paper; relevant, but analyst-workflow oriented rather than portfolio construction. |
| A picture is worth a thousand words: Measuring investor sentiment by combining machine learning and photos from news — Khaled Obaid, Kuntara Pukthuanthong | JFE | 2022 | Deep-learning/news-photo sentiment with return predictability; strong alternative-data candidate. |
| Real-time price discovery via verbal communication: Method and application to Fedspeak — Roberto Gómez-Cram, Marco Grotteria | JFE | 2022 | High-frequency textual Fedspeak price-discovery method; more macro-event/microstructure than pure asset management. |
| Big Data in Finance — Itay Goldstein, Chester S. Spatt, Mao Ye | RFS | 2021 | Useful context/special-issue overview rather than a primary technical contribution. |
| The Next Chapter of Big Data in Finance — Itay Goldstein, Chester S. Spatt, Mao Ye | RFS | 2021 | Useful context/special-issue overview rather than a primary technical contribution. |

## Local Search Artifacts

The EDITH literature module wrote local search artifacts under `workspace/literature/searches/` for the JF/JFE/RFS passes. Those local artifacts are not committed to this public repository; this repo stores the distilled metadata and editorial classification only.

## Next Local-Only Cleanup Queue

- Add a dedicated schema and validator for `data/finance_journal_ai_watchlist.yaml`.
- Clean suspicious EDITH local year fields, especially `Machine Learning for Continuous-Time Finance` and `Option Return Predictability with Machine Learning and Big Data`.
- Add Review of Finance and JFQA only if/when those journal records are added to the EDITH local corpus or a separate local source is mounted.
- Split the secondary list into `asset-pricing`, `asset-management`, `microstructure`, `derivatives`, `text-as-data`, and `context` views.

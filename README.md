<!-- Generated from data/papers.yaml and data/coverage.yaml by scripts/render.py. Do not edit directly. -->

<div align="center">

# Good Quant AI Papers

Curated top-conference research for quantitative finance and asset management.

[![Papers-23](https://img.shields.io/badge/Papers-23-0B7285?style=flat-square)](papers/2026/icml.md) [![Venues-11](https://img.shields.io/badge/Venues-11-364FC7?style=flat-square)](#browse-by-year-and-venue) [![Last verified-2026--07--11](https://img.shields.io/badge/Last_verified-2026--07--11-5F3DC4?style=flat-square)](data/papers.yaml) [![License-CC BY 4.0](https://img.shields.io/badge/License-CC_BY_4.0-2B8A3E?style=flat-square)](LICENSE)

</div>

## Scope

This catalog admits only officially accepted computer-science conference work with a direct contribution to quantitative investing, trading, portfolio construction, derivatives, or market-risk decisions. Every entry must have a verified venue record; an unverified preprint is not eligible. Main-conference, workshop, and position papers are labeled explicitly.

**Included:** asset allocation, alpha and factor modeling, market regimes, microstructure and execution, derivatives, market simulation, financial decision agents, and investment-linked alternative data.

**Excluded:** General banking, credit scoring, fraud detection, payments, accounting QA, regulatory technology, and generic financial NLP without a clear investment, trading, portfolio, or market-risk contribution.

The catalog stores original one-sentence editorial summaries and links—not paper PDFs or copied abstracts.

## Coverage: 2024–2026

| Venue | 2026 | 2025 | 2024 |
| --- | ---: | ---: | ---: |
| ICML | [23 papers](papers/2026/icml.md) · Pending | 0 papers · Pending | 0 papers · Pending |
| NeurIPS | 0 papers · Pending | 0 papers · Pending | 0 papers · Pending |
| ICLR | 0 papers · Pending | 0 papers · Pending | 0 papers · Pending |
| KDD | 0 papers · Pending | 0 papers · Pending | 0 papers · Pending |
| AAAI | 0 papers · Pending | 0 papers · Pending | 0 papers · Pending |
| IJCAI | 0 papers · Pending | 0 papers · Pending | 0 papers · Pending |
| WWW | 0 papers · Pending | 0 papers · Pending | 0 papers · Pending |
| WSDM | 0 papers · Pending | 0 papers · Pending | 0 papers · Pending |
| SIGIR | 0 papers · Pending | 0 papers · Pending | 0 papers · Pending |
| AISTATS | 0 papers · Pending | 0 papers · Pending | 0 papers · Pending |
| ACM ICAIF | 0 papers · Pending | 0 papers · Pending | 0 papers · Pending |

## Browse by Topic

[Alpha Modeling](https://github.com/sjsj0101/good-quant-ai-papers/search?q=path%3Adata%2Fpapers.yaml+%22alpha-modeling%22&type=code) · [Alternative Data](https://github.com/sjsj0101/good-quant-ai-papers/search?q=path%3Adata%2Fpapers.yaml+%22alternative-data%22&type=code) · [Asset Allocation](https://github.com/sjsj0101/good-quant-ai-papers/search?q=path%3Adata%2Fpapers.yaml+%22asset-allocation%22&type=code) · [Derivatives](https://github.com/sjsj0101/good-quant-ai-papers/search?q=path%3Adata%2Fpapers.yaml+%22derivatives%22&type=code) · [Evaluation](https://github.com/sjsj0101/good-quant-ai-papers/search?q=path%3Adata%2Fpapers.yaml+%22evaluation%22&type=code) · [Execution](https://github.com/sjsj0101/good-quant-ai-papers/search?q=path%3Adata%2Fpapers.yaml+%22execution%22&type=code) · [Factor Investing](https://github.com/sjsj0101/good-quant-ai-papers/search?q=path%3Adata%2Fpapers.yaml+%22factor-investing%22&type=code) · [Financial Agents](https://github.com/sjsj0101/good-quant-ai-papers/search?q=path%3Adata%2Fpapers.yaml+%22financial-agents%22&type=code) · [Financial Forecasting](https://github.com/sjsj0101/good-quant-ai-papers/search?q=path%3Adata%2Fpapers.yaml+%22financial-forecasting%22&type=code) · [Market Microstructure](https://github.com/sjsj0101/good-quant-ai-papers/search?q=path%3Adata%2Fpapers.yaml+%22market-microstructure%22&type=code) · [Market Regimes](https://github.com/sjsj0101/good-quant-ai-papers/search?q=path%3Adata%2Fpapers.yaml+%22market-regimes%22&type=code) · [Market Simulation](https://github.com/sjsj0101/good-quant-ai-papers/search?q=path%3Adata%2Fpapers.yaml+%22market-simulation%22&type=code) · [Portfolio Optimization](https://github.com/sjsj0101/good-quant-ai-papers/search?q=path%3Adata%2Fpapers.yaml+%22portfolio-optimization%22&type=code) · [Risk Management](https://github.com/sjsj0101/good-quant-ai-papers/search?q=path%3Adata%2Fpapers.yaml+%22risk-management%22&type=code) · [Synthetic Data](https://github.com/sjsj0101/good-quant-ai-papers/search?q=path%3Adata%2Fpapers.yaml+%22synthetic-data%22&type=code)

## ICML 2026

### Main Conference (13)

| Paper | Track | Focus | Assets / Frequency | Why it matters |
| --- | --- | --- | --- | --- |
| [A Linearly Convergent Proximal Subgradient Algorithm for Sparse Portfolio Optimization with Transaction Cost](<https://openreview.net/forum?id=yZAo4TPqhE>)<br><sub>Xiaoting Yao, Na Zhang</sub> | Main<br><sub>Poster</sub> | Solves transaction-cost-aware sparse online portfolios through a difference-of-convex reformulation and proximal updates. | — | Adds a convergence-backed route to controlling both turnover costs and the number of active positions. |
| [Adversarially Robust Control of Conditional Value-at-Risk via Kelly Conformal Inference](<https://openreview.net/forum?id=Vhesstbfg6>)<br><sub>Catherine Chen, Jingyan Shen, Xinyu Yang, Lihua Lei</sub> | Main<br><sub>Poster</sub> | Controls empirical conditional value-at-risk online with distribution-free guarantees under shifting or adversarial data. | — | Offers tail-risk safeguards for adaptive portfolio decisions without assuming a stationary return process. |
| [BizFinBench.v2: Towards Reliable LLMs in Finance via Real-User Data and Offline/Online Bilingual Evaluation](<https://icml.cc/virtual/2026/poster/65946>)<br><sub>Xin Guo, Rongjunchen Zhang, Guilong Lu, Xuntao Guo, Jia Shuai, Zhi Yang, Liwen Zhang</sub> | Main<br><sub>Poster</sub> | Benchmarks bilingual language models on authentic Chinese and U.S. equity-market tasks, including quantitative computation and stock-price prediction. | — | Tests whether models can handle real investment queries across markets and online or offline settings, not only scripted finance questions. |
| [Decision-focused Sparse Tangent Portfolio Optimization](<https://openreview.net/forum?id=KV7XHF0IbK>)<br><sub>Haeun Jeon, Seunghoon Choi, Hyunglip Bae, Yongjae Lee, Woo Chang Kim</sub> | Main<br><sub>Poster</sub> | Trains a return model through differentiable asset selection and sparse tangency-portfolio reoptimization. | — | Targets risk-adjusted portfolio quality under a fixed holding budget rather than forecast accuracy in isolation. |
| [Error Propagation in Dynamic Programming: From Stochastic Control to American Option Pricing](<https://icml.cc/virtual/2026/poster/65273>)<br><sub>Andrea Della Vecchia, Damir Filipovic</sub> | Main<br><sub>Poster</sub> | Analyzes how approximation errors accumulate through dynamic programs, including learned American-option valuation schemes. | — | Clarifies when local model errors remain controlled in sequential pricing and exercise decisions. |
| [Global Merger-Arbitrage Forecasting with Language Models](<https://icml.cc/virtual/2026/poster/60833>)<br><sub>Hinal Jajal, Michał Mucha, Charles Sweat, Chris Pulman, Charlie Flanagan, Peter Anderson</sub> | Main<br><sub>Poster</sub> | Builds language-model forecasts of announced merger outcomes from structured analysis of deal-specific risks. | — | Grounds investment-research agents in a probability forecast tied to a concrete merger-arbitrage decision. |
| [Joint-Embedding Predictive Learning of Latent Market States in U.S. Equities](<https://openreview.net/forum?id=BZfkxSasd3>)<br><sub>Simon Mahns, Randall Balestriero, Mahmoud Assran</sub> | Main<br><sub>Poster</sub> | Uses self-supervised joint-embedding prediction to compress daily equity cross-sections into latent market-state representations. | — | Provides a learned view of persistent volatility and correlation regimes without requiring return labels. |
| [Learning the ESG Geometry with Domain Aware Language Models](<https://icml.cc/virtual/2026/poster/65502>)<br><sub>Kunal Pradeep Pimparkhede, Chirayu Chaurasia, Jatin Roy, Mahesh Mohan Mohanachandran Radhamany</sub> | Main<br><sub>Poster</sub> | Learns domain-aware language representations that organize ESG information for investment analysis. | — | Turns unstructured sustainability disclosures into geometry that can support asset comparison and selection. |
| [MarketSim: Simulating Stock Markets with Large-Scale Generative Agents](<https://openreview.net/forum?id=EzpJxPDqXB>)<br><sub>Jinghua Piao, zhentao liu, Cheng Huang, Jiarui Huang, Songwei Li, Ranran Wang, Yong Li</sub> | Main<br><sub>Poster</sub> | Simulates stock-market dynamics through a large population of generative agents with heterogeneous behaviors. | — | Creates an experimental environment for studying emergent market outcomes and stress scenarios before live deployment. |
| [Signature-Informed Transformer for Asset Allocation](<https://openreview.net/forum?id=eBM5ALLJNx>)<br><sub>Yoontae Hwang, Stefan Zohren</sub> | Main<br><sub>Poster</sub> | Learns multi-asset allocations end to end using path-signature features and a downside-risk objective. | — | Connects market-path geometry directly to portfolio decisions instead of optimizing an intermediate forecast loss. |
| [Tail Annealing for Heavy-Tailed Flow Matching](<https://icml.cc/virtual/2026/poster/60665>)<br><sub>Jean Pachebat</sub> | Main<br><sub>Poster</sub> | Evaluates extreme-tail and CVaR99 fidelity on controlled heavy-tailed benchmarks, then validates generation on real Fama–French equity-factor returns. | Equities | Combining CVaR99 fidelity with Fama–French validation makes the generator directly relevant to tail-sensitive market-risk scenario analysis. |
| [The Label Horizon Paradox: Rethinking Supervision Targets in Financial Forecasting](<https://arxiv.org/abs/2602.03395>)<br><sub>Chen-Hui Song, Shuoling Liu, Liyuan Chen</sub> | Main<br><sub>Poster</sub> | Selects a training-label horizon separately from the ultimate return horizon through bilevel optimization. | — | Shows that the most useful supervision target for an investment forecast need not match its deployment horizon. |
| [Towards Professional-Grade Financial Agents: Benchmarking, Tooling, and Structured Reasoning](<https://icml.cc/virtual/2026/poster/60732>)<br><sub>Cheng Huang, Jinghua Piao, Ranran Wang, Yong Li</sub> | Main<br><sub>Poster</sub> | Evaluates financial agents through tool-enabled tasks and structured reasoning workflows aimed at professional practice. | — | Moves agent assessment toward auditable investment workflows rather than isolated finance questions. |

### Position Papers (1)

| Paper | Track | Focus | Assets / Frequency | Why it matters |
| --- | --- | --- | --- | --- |
| [Position: Evaluating LLMs in Finance Requires Explicit Bias Consideration](<https://icml.cc/virtual/2026/poster/67204>)<br><sub>Yaxuan Kong, Hoyoung Lee, Yoontae Hwang, Alejandro Lopez-Lira, Bradford Levy, Dhagash Mehta, Qingsong Wen, CHANYEOL CHOI, Yongjae Lee, Stefan Zohren</sub> | Position<br><sub>Poster</sub> | Argues that finance LLM evaluation must explicitly control look-ahead, survivorship, and trading-cost biases. | — | Point-in-time universes and realistic trading frictions determine whether reported forecasting and investment performance is valid. |

### Workshops (9)

| Paper | Track | Focus | Assets / Frequency | Why it matters |
| --- | --- | --- | --- | --- |
| [Behavioral Proxy Conditioning for Financial Stress Scenario Generation with a Pretrained Diffusion Model](<https://openreview.net/forum?id=xrwkOUb8kp>)<br><sub>Elena Kuular, Junsuk Choe</sub> | Workshop<br><sub>Poster</sub> | Conditions a pretrained diffusion model on behavioral proxies to generate financially meaningful stress scenarios. | — | Expands scenario design beyond historical replay while retaining interpretable links to stressed market behavior. |
| [DELPHYNE: A Pre-Trained Model for General and Financial Time Series](<https://arxiv.org/abs/2506.06288>)<br><sub>Xueying Ding, Aakriti Mittal, Achintya Gopal</sub> | Workshop<br><sub>Poster</sub> | Pretrains a general time-series model on a mixture that deliberately includes financial series and multiple sampling frequencies. | — | Addresses negative transfer that can make broad time-series foundation models weak on volatility and risk forecasts. |
| [Forecast-to-Trade: Hierarchical Reinforcement Learning for Decision-Aware Financial Forecasting](<https://openreview.net/forum?id=pTiRAPtDzK>)<br><sub>Zijie Zhao, Roy E. Welsch</sub> | Workshop<br><sub>Spotlight</sub> | Separates directional asset selection from constrained portfolio-weight execution in a hierarchical reinforcement-learning trader. | — | Evaluates forecasts through implementable rebalancing decisions that account for turnover, downside risk, and trading costs. |
| [Leakage-Aware Benchmarking of LLM Forecasting: Real-Time Nowcasts as the Decision-Time Input for Macro Factor Ranking](<https://arxiv.org/abs/2606.22719>)<br><sub>Mao Guan, Qian Chen</sub> | Workshop<br><sub>Poster</sub> | Benchmarks macro-conditioned equity-factor ranking using only data and nowcasts available at each historical decision time. | — | Separates genuine forecasting value from publication-lag leakage in investment backtests. |
| [Learning to Trade Like an Expert: Cognitive Fine-Tuning for Stable Financial Reasoning in Language Models](<https://arxiv.org/abs/2604.16862>)<br><sub>Yuchen Pan, Soung Chang Liew</sub> | Workshop<br><sub>Poster</sub> | Fine-tunes open language models on structured financial reasoning examples and evaluates transfer to chronological trading simulations. | — | Tests whether explicit decision reasoning produces more stable trading behavior across market regimes. |
| [Mechanism-Inspired Aggregation for Multi-Agent Alpha Discovery: Optimizing Agent Distributions in Heterogeneous LLM Markets](<https://openreview.net/forum?id=mbstEcHW0R>)<br><sub>Ajitabh Kumar</sub> | Workshop<br><sub>Poster</sub> | Aggregates heterogeneous language-model agents by optimizing their population mix for multi-agent alpha discovery. | — | Treats agent diversity and weighting as part of the investment signal design rather than relying on simple voting. |
| [One Token per Trade: Multi-Resolution Limit Order Book Forecasting with a Foundation Model](<https://openreview.net/forum?id=ZMEIc25o0a>)<br><sub>Srijan Sood, Maxime Kawawa-Beaudan, Z. Guo, Daniel Borrajo</sub> | Workshop<br><sub>Poster</sub> | Represents individual trades as tokens and forecasts limit-order-book behavior across several temporal resolutions. | — | Offers a shared sequence model for short-horizon order-flow signals that otherwise require separately calibrated models. |
| [Reflexivity as Prompt: Does Awareness of Self-Reinforcing Market Dynamics Improve LLMs as Financial Market Forecasters?](<https://arxiv.org/abs/2606.00061>)<br><sub>Eugene Park</sub> | Workshop<br><sub>Poster</sub> | Tests whether prompts describing reflexive boom-bust dynamics change language-model forecasts across historical market cycles. | — | Examines whether economic mechanism awareness improves directional and risk-adjusted forecasts rather than only narrative quality. |
| [TradeFM: A Generative Foundation Model for Trade-flow and Market Microstructure](<https://openreview.net/forum?id=anK6dppdfa>)<br><sub>Srijan Sood, Maxime Kawawa-Beaudan, Daniel Borrajo, Manuela Veloso</sub> | Workshop<br><sub>Poster</sub> | Trains a generative trade-event model with scale-invariant features designed to transfer across equity markets. | — | Supports cross-asset order-flow simulation and synthetic microstructure data without asset-specific tokenization. |

## Browse by Year and Venue

- **2026** · [ICML 2026](papers/2026/icml.md) — 23 papers

## Contributing

Contributions to [`sjsj0101/good-quant-ai-papers`](https://github.com/sjsj0101/good-quant-ai-papers) are welcome. Add or correct metadata in [`data/papers.yaml`](data/papers.yaml), provide an official venue source, and write original summary prose. Do not edit generated indexes by hand.

```bash
python3 scripts/validate.py
python3 scripts/render.py
python3 scripts/render.py --check
```

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for the complete submission checklist.

## License

Catalog metadata and original editorial prose are licensed under [Creative Commons Attribution 4.0 International](LICENSE). Linked papers and third-party resources remain under their respective terms.

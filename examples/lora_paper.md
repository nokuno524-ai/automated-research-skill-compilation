# LoRA: Low-Rank Adaptation of Large Language Models

## Abstract
We propose Low-Rank Adaptation, or LoRA, which freezes the pre-trained model weights and injects trainable rank decomposition matrices into each layer of the Transformer architecture, greatly reducing the number of trainable parameters for downstream tasks.

## 1 Introduction
Natural Language Processing has witnessed a paradigm shift with the rise of large pre-trained language models. Fine-tuning all parameters becomes prohibitively expensive. We propose LoRA which adapts models using low-rank update matrices.

## 4 Our Method
We augment a pre-trained weight matrix $W_0 \in \mathbb{R}^{d \times k}$ with a low-rank decomposition $W_0 + \Delta W = W_0 + BA$, where $B \in \mathbb{R}^{d \times r}$, $A \in \mathbb{R}^{r \times k}$, and the rank $r \ll \min(d, k)$.

$$h = W_0 x + \Delta W x = W_0 x + BAx$$

During training, $W_0$ is frozen and only $A$ and $B$ are updated. We scale $\Delta W$ by $\alpha / r$ where $\alpha$ is a constant scaling factor.

## 5 Experiments
We evaluate on RoBERTa, DeBERTa, GPT-2, and GPT-3. LoRA reduces trainable parameters by 10,000x while matching or exceeding full fine-tuning quality.

Key hyperparameters: rank r ∈ {1, 2, 4, 8, 64}, alpha = 2r, applied to query and value projection matrices.

# Attention Is All You Need

## Abstract
We propose a new simple network architecture, the Transformer, based solely on attention mechanisms, dispensing with recurrence and convolutions entirely. The Transformer achieves 28.4 BLEU on WMT 2014 English-to-German translation.

## 1 Introduction
Recurrent neural networks have been firmly established as state of the art approaches in sequence modeling. However, their sequential nature precludes parallelization. We propose the Transformer, a model architecture eschewing recurrence and instead relying entirely on an attention mechanism to draw global dependencies between input and output.

## 3 Model Architecture
The Transformer follows an encoder-decoder structure using stacked self-attention and point-wise, fully connected layers.

### 3.1 Scaled Dot-Product Attention

$$\text{Attention}(Q, K, V) = \text{softmax}\left(\frac{QK^T}{\sqrt{d_k}}\right)V$$

### 3.2 Multi-Head Attention

$$\text{MultiHead}(Q, K, V) = \text{Concat}(\text{head}_1, ..., \text{head}_h)W^O$$

where $\text{head}_i = \text{Attention}(QW_i^Q, KW_i^K, VW_i^V)$

The projections are parameter matrices $W_i^Q \in \mathbb{R}^{d_{model} \times d_k}$, $W_i^K \in \mathbb{R}^{d_{model} \times d_k}$, $W_i^V \in \mathbb{R}^{d_{model} \times d_v}$ and $W^O \in \mathbb{R}^{hd_v \times d_{model}}$.

### 3.3 Position-wise Feed-Forward Networks
Each layer has a fully connected feed-forward network applied to each position separately: $FFN(x) = \max(0, xW_1 + b_1)W_2 + b_2$.

### 3.5 Positional Encoding
We use sine and cosine functions of different frequencies:

$$PE_{(pos, 2i)} = \sin(pos / 10000^{2i/d_{model}})$$
$$PE_{(pos, 2i+1)} = \cos(pos / 10000^{2i/d_{model}})$$

## 5 Training
We trained the Transformer on the WMT 2014 English-to-German translation task (4.5M sentence pairs) using Adam with $\beta_1=0.9, \beta_2=0.98, \epsilon=10^{-9}$.

Key hyperparameters: d_model=512, d_ff=2048, h=8, N=6, dropout=0.1, warmup_steps=4000.

# Training Strategy Optimization

## Abstract
We introduce a novel training strategy to speed up convergence by 2x.

## Proposed Training Strategy
Our approach modifies the standard learning rate schedule. We decay the learning rate linearly.

$$\text{lr}_t = \text{lr}_0 \times (1 - \frac{t}{T})$$

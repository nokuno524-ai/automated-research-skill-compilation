# Denoising Diffusion Probabilistic Models

## Abstract
We present high quality image synthesis results using diffusion probabilistic models, a class of latent variable models inspired by thermodynamics. Our results are competitive with GANs.

## 2 Background
Diffusion models are latent variable models of the form $p_\theta(x_0) := \int p_\theta(x_{0:T}) dx_{1:T}$, where $x_1, ..., x_T$ are latents of the same dimensionality as the data $x_0 \sim q(x_0)$.

## 3 Method
The forward process adds Gaussian noise gradually:

$$q(x_t | x_{t-1}) = \mathcal{N}(x_t; \sqrt{1 - \beta_t} x_{t-1}, \beta_t I)$$

The reverse process learns to denoise:

$$p_\theta(x_{t-1} | x_t) = \mathcal{N}(x_{t-1}; \mu_\theta(x_t, t), \Sigma_\theta(x_t, t))$$

We train using a simplified loss:

$$L_{simple}(\theta) = \mathbb{E}_{t, x_0, \epsilon} \left[ \| \epsilon - \epsilon_\theta(x_t, t) \|^2 \right]$$

where $\epsilon \sim \mathcal{N}(0, I)$ and $\epsilon_\theta$ is a neural network predicting the noise.

## 4 Experiments
We evaluate on CIFAR10, CelebA-HQ, and LSUN. Our models achieve Inception scores of 9.46 on CIFAR10.

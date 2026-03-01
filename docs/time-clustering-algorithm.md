# Time Clustering Algorithm Research

## Note Existence Time Index Algorithm

### Note Timing

#### Initial Values (Given or Observable)

- `note count` n / positive integer representing total number of notes
- `generation time` t_i / generation timestamp of note i, satisfying t_1 ≤ t_2 ≤ ... ≤ t_n, fixed and unchanging
- `current time` T / observation timestamp, variable, satisfying T ≥ t_n

#### Derived Values (Calculated from Initial Values)

- `existence time` d_i(T) = T - t_i / time elapsed from generation to current time for note i
- `total existence time` D(T) = ∑_{i=1}^n d_i(T) = nT - ∑_{i=1}^n t_i
- `existence weight` w_i(T) = d_i(T) / D(T) = (T - t_i) / (nT - ∑ t_i)
  - Satisfies 0 < w_i < 1 and ∑ w_i = 1
- `average generation time` t̄ = (1/n) ∑ t_i
- `convergent value (equilibrium weight)` w* = lim_{T→∞} w_i(T) = 1/n
- `weight deviation` Δw_i(T) = w_i(T) - 1/n
- `weight change rate` dw_i/dT = n(t_i - t̄) / D^2

#### Memory Fragmentation Probability

For weight vector w = (w_1, w_2, ..., w_n), equilibrium weight is w* = 1/n.

Original Variance:

Var(w) = (1/n) ∑_{i=1}^n (w_i - w*)^2

Maximum Possible Variance (when all weight concentrates on one note):
Assuming weight concentrates on note k, then w_k = 1, others are 0:

Var_max = (1/n) [(1 - 1/n)^2 + (n-1)(0 - 1/n)^2] = (n-1)/n^2

Normalized Variance (0~1):

C_norm = Var(w) / Var_max = (n^2/(n-1)) * (1/n) ∑_{i=1}^n (w_i - 1/n)^2
= (n/(n-1)) ∑_{i=1}^n (w_i - 1/n)^2

Verification:

- Uniform distribution: w_i = 1/n, then C_norm = 0
- Complete concentration: one weight is 1, others are 0, then C_norm = 1

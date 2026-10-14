"""Create the simulated survey data used to train the risk-profile model (run once).

Each row is one investor who answered a short survey. The label `risk_profile` comes from a
hidden scoring rule plus random noise, so the model has to learn the pattern from data.
"""
import numpy as np
import pandas as pd

rng = np.random.default_rng(336)
n = 1500
age = rng.integers(20, 66, n)
income = np.round(rng.lognormal(np.log(30_000), 0.5, n), -2).clip(9_000, 300_000)
saving_rate = rng.integers(0, 41, n)
experience = np.minimum(rng.poisson(3, n), age - 18)
horizon = rng.integers(1, 31, n)
reaction = rng.choice(["sell", "hold", "buy_more"], n, p=[0.3, 0.5, 0.2])

score = (-0.04 * (age - 40) + 0.6 * np.log(income / 30_000) + 0.03 * saving_rate
         + 0.10 * np.minimum(experience, 10) + 0.06 * np.minimum(horizon, 20)
         + pd.Series(reaction).map({"sell": -1.3, "hold": 0.0, "buy_more": 1.0}).to_numpy()
         + rng.normal(0, 0.45, n))
low, high = np.quantile(score, [0.35, 0.75])
label = np.where(score < low, "conservative", np.where(score < high, "moderate", "aggressive"))

pd.DataFrame({"age": age, "monthly_income": income.astype(int), "saving_rate_pct": saving_rate,
              "invest_experience_years": experience, "horizon_years": horizon,
              "reaction_to_20pct_drop": reaction, "risk_profile": label}).to_csv("risk_profile_survey.csv", index=False)
print(pd.Series(label).value_counts())

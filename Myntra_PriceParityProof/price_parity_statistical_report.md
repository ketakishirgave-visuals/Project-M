# Project Siphon: Price Parity Statistical Report

## 1\. Valid Samples Analysis (Excluding Outliers)

* **Sample Size**: 277
* **Median Delta %**: 0.0%
* **Wilcoxon Statistic**: 4017.0
* **p-value**: 0.1273

> \\\\\\\*\\\\\\\*Conclusion\\\\\\\*\\\\\\\*: Fail to reject H0 → No significant price inflation / broad parity holds.



## 2\. Valid + Review Samples Analysis

* **Sample Size**: 381
* **Median Delta %**: 0.0%
* **Wilcoxon Statistic**: 11914.0
* **p-value**: 0.0138

> \\\\\\\*\\\\\\\*Conclusion\\\\\\\*\\\\\\\*: Reject H0 → Significant pricing difference appears when review-tier included.



The distribution of delta\_pct in the valid\_review group is statistically different. This suggests that even if the middle value is zero, there might be a greater tendency for positive or negative deviations, or the deviations might be larger, leading to a statistically significant difference when considering the overall distribution, even if the median itself is 0%. The 'review' products, by definition, include larger absolute price differences, which likely contribute to this statistical significance without necessarily shifting the median.



## 3\. Platform Parity Rankings (Median Delta %)

```text
competitor\\\\\\\_platform
Puma             -4.000
Mamaearth        -2.065
Max Fashion       0.000
Amazon            0.000
Off Duty          2.300
LA Girl           5.500
Shoppers Stop    12.360
```

## 4\. Category vs Platform Matrix (Median Delta %)

```text
competitor\\\\\\\_platform  Amazon  LA Girl  Mamaearth  Max Fashion  Off Duty   Puma  Shoppers Stop
category                                                                                    
Clothing               3.03      NaN        NaN          0.0       2.3  -2.00            NaN
Ethnic Wear             NaN      NaN        NaN          0.0       NaN    NaN            NaN
Footwear               0.00      NaN        NaN          0.0       NaN -12.31            NaN
Lingerie               0.00      NaN        NaN          NaN       NaN    NaN            NaN
Makeup                 0.00      5.5      -3.06          NaN       NaN    NaN          12.36
Skincare               0.25      NaN      -1.07          NaN       NaN    NaN            NaN
```


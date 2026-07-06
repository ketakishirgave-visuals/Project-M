WITH row_level_bands AS (
    SELECT 
        f.final_cluster_id,
        w.cashback_applied_rs,
        w.weekly_orders,
        NTILE(5) OVER (PARTITION BY f.final_cluster_id ORDER BY w.cashback_applied_rs) AS cashback_efficiency_band
    FROM weekly_features_gt w
    JOIN final_cluster_assignments f ON w.customer_id = f.customer_id
    WHERE w.cashback_applied_rs > 0
),
band_aggregates AS (
    SELECT 
        final_cluster_id,
        cashback_efficiency_band,
        AVG(cashback_applied_rs) AS avg_incentive_spend,
        AVG(CAST(weekly_orders AS DECIMAL(10,4))) AS purchase_frequency_rate
    FROM row_level_bands
    GROUP BY final_cluster_id, cashback_efficiency_band
)
SELECT 
    final_cluster_id,
    cashback_efficiency_band,
    ROUND(avg_incentive_spend, 2) AS avg_incentive_spend,
    ROUND(purchase_frequency_rate, 4) AS purchase_frequency_rate,
    ROUND(
        purchase_frequency_rate - LAG(purchase_frequency_rate, 1, 0.0) 
        OVER (PARTITION BY final_cluster_id ORDER BY cashback_efficiency_band), 
        4
    ) AS frequency_marginal_difference
FROM band_aggregates
ORDER BY final_cluster_id, cashback_efficiency_band;
WITH ranked_wallets AS (
    SELECT 
        wallet_end_rs,
        ROW_NUMBER() OVER (ORDER BY wallet_end_rs) AS row_num,
        COUNT(*) OVER () AS total_rows
    FROM weekly_features_gt
),
weekly_median AS (
    SELECT AVG(wallet_end_rs) AS global_median_wallet
    FROM ranked_wallets
    WHERE row_num IN (FLOOR((total_rows + 1) / 2), CEIL((total_rows + 1) / 2))
), 
dependency_aggregates AS (
    SELECT 
        f.final_cluster_id,
        SUM(CASE WHEN w.wallet_end_rs > m.global_median_wallet THEN w.weekly_orders ELSE 0 END) AS high_wallet_orders,
        SUM(CASE WHEN w.wallet_end_rs <= m.global_median_wallet THEN w.weekly_orders ELSE 0 END) AS low_wallet_orders,
        SUM(w.weekly_orders) AS total_orders,
        SUM(CASE WHEN w.cashback_applied_rs = 0 THEN w.weekly_orders ELSE 0 END) AS zero_cashback_orders
    FROM weekly_features_gt w
    JOIN final_cluster_assignments f ON w.customer_id = f.customer_id
    CROSS JOIN weekly_median m
    GROUP BY f.final_cluster_id
),
cluster_rates AS (
    SELECT final_cluster_id, AVG(full_price_rate) AS full_price_purchase_rate
    FROM final_cluster_assignments
    GROUP BY final_cluster_id
)
SELECT      
    da.final_cluster_id,
    da.high_wallet_orders,
    da.low_wallet_orders,
    ROUND(da.high_wallet_orders * 100.0 / NULLIF(da.total_orders, 0), 2) AS high_wallet_conversion_pct,
    ROUND(da.low_wallet_orders * 100.0 / NULLIF(da.total_orders, 0), 2) AS low_wallet_conversion_pct,
    ROUND(da.zero_cashback_orders * 100.0 / NULLIF(da.total_orders, 0), 2) AS zero_cashback_purchase_pct,
    ROUND(cr.full_price_purchase_rate, 4) AS full_price_purchase_rate 
FROM dependency_aggregates da 
JOIN cluster_rates cr ON da.final_cluster_id = cr.final_cluster_id
ORDER BY da.final_cluster_id;

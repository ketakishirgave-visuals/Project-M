SELECT 
    f.final_cluster_id,
    c.city_tier,
    SUM(t.order_value_rs) AS gross_revenue_generated,
    SUM(t.net_revenue_rs) AS total_profit_generated,
    SUM(t.cashback_applied) AS total_cashback_received,
    ROUND(SUM(t.order_value_rs) / NULLIF(SUM(t.cashback_applied), 0), 2) AS revenue_per_1_cashback,
    ROUND(SUM(t.net_revenue_rs) / NULLIF(SUM(t.cashback_applied), 0), 2) AS profit_per_1_cashback,
    AVG(f.expired_cashback_fraction) AS geographic_leakage_rate
FROM final_cluster_assignments f
JOIN customers c ON f.customer_id = c.customer_id
LEFT JOIN transactions t ON c.customer_id = t.customer_id
GROUP BY f.final_cluster_id, c.city_tier
ORDER BY profit_per_1_cashback DESC;
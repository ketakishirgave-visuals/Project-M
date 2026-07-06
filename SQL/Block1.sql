SELECT 
    f.final_cluster_id,
    c.city_tier,
    COUNT(DISTINCT c.customer_id) AS customer_count,
    SUM(t.cashback_applied) AS total_cashback_received,
    SUM(t.order_value_rs) AS gross_revenue_generated,
    SUM(t.net_revenue_rs) AS total_profit_generated,
    RANK() OVER (PARTITION BY c.city_tier ORDER BY COUNT(DISTINCT c.customer_id) DESC) AS cluster_distribution_rank
FROM customers c
JOIN final_cluster_assignments f ON c.customer_id = f.customer_id
LEFT JOIN transactions t ON c.customer_id = t.customer_id
GROUP BY f.final_cluster_id, c.city_tier
ORDER BY total_profit_generated DESC;
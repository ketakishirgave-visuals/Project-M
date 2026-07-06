SELECT 
    f.final_cluster_id,
    COUNT(s.customer_id) AS total_cards,
    ROUND(SUM(CASE WHEN s.deliberately_expired = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS deliberate_expiry_rate_pct,
    ROUND(SUM(CASE WHEN s.scratched = 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS card_rejection_rate_pct,
    AVG(COALESCE(s.card_amount_rs, 0)) AS average_card_amount,
    SUM(CASE WHEN s.deliberately_expired = 1 OR s.scratched = 0 THEN COALESCE(s.card_amount_rs, 0) ELSE 0 END) AS total_value_lost_to_optimization
FROM scratch_cards s
JOIN final_cluster_assignments f ON s.customer_id = f.customer_id
GROUP BY f.final_cluster_id;
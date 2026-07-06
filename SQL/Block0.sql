WITH leakage_base AS (     
    SELECT          
        s.customer_id,         
        f.final_cluster_id,         
        c.city_tier,         
        SUM(COALESCE(s.card_amount_rs, 0)) AS total_issued,         
        SUM(CASE WHEN s.scratched = 0 THEN COALESCE(s.card_amount_rs, 0) ELSE 0 END) AS unscratched_leakage,         
        SUM(CASE WHEN s.deliberately_expired = 1 THEN COALESCE(s.card_amount_rs, 0) ELSE 0 END) AS deliberate_expiry_leakage
    FROM scratch_cards s     
    JOIN customers c ON s.customer_id = c.customer_id     
    JOIN final_cluster_assignments f ON c.customer_id = f.customer_id     
    GROUP BY s.customer_id, f.final_cluster_id, c.city_tier 
) 
SELECT      
    final_cluster_id,     
    city_tier,     
    SUM(total_issued) AS total_cashback_issued,     
    SUM(unscratched_leakage) AS unscratched_cards_leakage,     
    SUM(deliberate_expiry_leakage) AS deliberate_expiry_leakage,     
    SUM(unscratched_leakage + deliberate_expiry_leakage) AS total_observed_leakage,     
    ROUND(SUM(unscratched_leakage + deliberate_expiry_leakage) * 100.0 / NULLIF(SUM(total_issued), 0), 2) AS leakage_rate_pct,     
    CASE          
        WHEN SUM(unscratched_leakage) > SUM(deliberate_expiry_leakage) THEN 'Unscratched Cards'         
        WHEN SUM(deliberate_expiry_leakage) > SUM(unscratched_leakage) THEN 'Deliberate Expiry'         
        ELSE 'Balanced / No Leakage'     
    END AS primary_leakage_source 
FROM leakage_base 
GROUP BY final_cluster_id, city_tier
ORDER BY final_cluster_id, city_tier;
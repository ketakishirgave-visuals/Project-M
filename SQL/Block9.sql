WITH tenure_cohorts AS (
    SELECT 
        customer_id,
        final_cluster_id,
        CASE 
            WHEN signup_tenure_weeks <= 12 THEN 'New Cohort (<=12 Weeks)'
            WHEN signup_tenure_weeks <= 52 THEN 'Mid Cohort (13-52 Weeks)'
            ELSE 'Mature Cohort (>52 Weeks)'
        END AS tenure_vintage
    FROM final_cluster_assignments
)
SELECT 
    tc.tenure_vintage,
    tc.final_cluster_id,
    COUNT(DISTINCT tc.customer_id) AS active_headcount,
    SUM(t.cashback_applied) AS total_cashback_distributed,
    SUM(t.order_value_rs) AS gross_revenue_generated,
    SUM(t.net_revenue_rs) AS net_profit_realized,
    ROUND(SUM(t.net_revenue_rs) / NULLIF(SUM(t.cashback_applied), 0), 2) AS profit_per_1_cashback
FROM tenure_cohorts tc
LEFT JOIN transactions t ON tc.customer_id = t.customer_id
GROUP BY tc.tenure_vintage, tc.final_cluster_id
ORDER BY tc.tenure_vintage, profit_per_1_cashback DESC;
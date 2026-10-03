-- Replace main.circular_portfolio if you chose different widgets.
-- Each query can become a tile in a Databricks SQL dashboard.
SELECT COUNT(*) AS assets, SUM(expected_net) AS expected_contribution_brl,
       SUM(baseline_expected_net) AS baseline_contribution_brl,
       SUM(decision_gain) AS expected_policy_gain_brl,
       SUM(CASE WHEN needs_review THEN 1 ELSE 0 END) AS review_assets
FROM main.circular_portfolio.gold_asset_decisions;

SELECT route, COUNT(*) AS assets, SUM(expected_net) AS expected_contribution_brl
FROM main.circular_portfolio.gold_asset_decisions GROUP BY route ORDER BY assets DESC;

SELECT model, assets, expected_net, review_assets, decision_gain
FROM main.circular_portfolio.gold_model_summary ORDER BY expected_net DESC;

SELECT equipment_id, model, supplier, route, naive_route, expected_net, baseline_expected_net, decision_gain
FROM main.circular_portfolio.gold_asset_decisions
WHERE route <> naive_route ORDER BY decision_gain DESC;

SELECT quality_reason, COUNT(*) AS events
FROM main.circular_portfolio.quarantine_equipment_events GROUP BY quality_reason;

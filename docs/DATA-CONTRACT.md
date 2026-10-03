# Shared data contract · circular-v1

The CSV contains the following fields. All identities, suppliers, device models, prices and probabilities are fictional. Monetary values use BRL with two decimals; no currency conversion is implemented.

| CSV field | Salesforce field | Meaning |
|---|---|---|
| equipment_id | External_Id__c | Stable unique device identity |
| model | Model__c | Fictional device family |
| supplier | Supplier__c | Fictional source supplier |
| condition_score | Condition_Score__c | Integer 0–100 |
| resale_price | Resale_Price__c | Direct-resale receipt |
| refurbished_price | Refurbished_Price__c | Receipt after successful repair |
| repair_cost | Repair_Cost__c | Cost paid for every repair attempt |
| failure_probability | Failure_Probability__c | Assumed probability of failed repair |
| salvage_value | Salvage_Value__c | Recycling receipt and failed-repair fallback |
| acquisition_credit | Acquisition_Credit__c | Trade-in credit offered to the customer |
| logistics_cost | Logistics_Cost__c | Transport/handling cost common to all routes |
| updated_at | Export event metadata | UTC source-event timestamp, not a Salesforce field |

## Export boundary
The Databricks CSV is a shared synthetic event fixture, not a direct Salesforce export. Salesforce seed.apex loads the three featured devices only. A future connector would select these Salesforce input fields, use SystemModstamp as updated_at, format UTC timestamps, and publish event records. No connector is deployed by this project.

## Worked examples
DEMO-001: condition 85, credit 400, logistics 50. Resale net = 550. Repair expected net = 0.9×1400 + 0.1×100 − 200 − 400 − 50 = 620. Recycle net = −350. Repair wins.

DEMO-002: condition 65 excludes direct resale. Repair expected net = 0.45×1400 + 0.55×150 − 850 − 600 − 70 = −807.50. Recycle net = −520. Recycling is the least negative route and requires manager review; it is not a profitable outcome.

DEMO-003: condition 20 permits only recycling. Salvage 120 − credit 40 − logistics 30 = 50. Recycling wins with positive expected contribution.

## Approval boundary
Recommendation and approval are separate. The app never interprets a positive recommendation as an approved payout. Changes to decision inputs invalidate approval. A high-credit or negative-contribution case requires manager permission. The portfolio browser is a simulation and cannot approve platform records.

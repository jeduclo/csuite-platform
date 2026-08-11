UPDATE intel.decision_alerts SET condition_text = REPLACE(condition_text, 'â?"', N'–');
UPDATE intel.decision_alerts SET condition_text = REPLACE(condition_text, 'â%☼', N'≤');
UPDATE intel.decision_alerts SET condition_text = REPLACE(condition_text, 'â%¥', N'≥');
UPDATE intel.decision_alerts SET condition_text = REPLACE(condition_text, 'â€˜', N'''');
UPDATE intel.decision_alerts SET condition_text = REPLACE(condition_text, 'â€™', N'''');
UPDATE intel.decision_alerts SET condition_text = REPLACE(condition_text, 'â€"', N'–');
UPDATE intel.decision_alerts SET recommended_action = REPLACE(recommended_action, 'â€"', N'—');
UPDATE intel.decision_alerts SET recommended_action = REPLACE(recommended_action, 'â€˜', N'''');
UPDATE intel.decision_alerts SET recommended_action = REPLACE(recommended_action, 'â€™', N'''');
SELECT alert_name, condition_text FROM intel.decision_alerts;
GO

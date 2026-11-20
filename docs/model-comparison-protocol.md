# Model comparison protocol

The research core compares Huber regression, Extra Trees, Elastic Net and Bayesian Ridge with grouped out-of-fold (OOF) predictions. Feature selection and scaling are part of each scikit-learn Pipeline and are fitted only on each training fold.

## Grouping strategies
- `Sample Number`: primary leakage-control grouping. Repeated rows carrying the same sample/reference identifier remain in one fold.
- `Amostra`: stricter secondary analysis that holds out entire sampling points/parcels. It addresses transfer to unseen points and is not interchangeable with the primary scan/reference grouping.

Run both analyses and compare their scores. A large deterioration under point-held-out validation may indicate that scan-level validation overstates transfer to new sampling points.

## Interpretation
Metrics (R², MAE, RMSE and bias) are calculated from one OOF prediction per observation. Candidate ranking by OOF RMSE is exploratory: because the same OOF results are inspected to select a candidate, they are not an unbiased final estimate of the selected model. Use nested grouped CV or an untouched grouped test set for final performance reporting.

TOC and N are evaluated as separate targets. The dissertation reported validation concerns TOC; the N experiment remains exploratory until its laboratory reference method, units and provenance are verified. No model performance is claimed until the original dataset is loaded and the analysis is executed.

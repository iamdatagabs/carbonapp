# Model comparison protocol

The research core compares Huber regression, Extra Trees, Elastic Net and Bayesian Ridge with grouped out-of-fold (OOF) predictions. Feature selection and scaling are part of each scikit-learn Pipeline and are fitted only on each training fold.

## Grouping strategies
- `Sample Number`: primary leakage-control grouping. Repeated rows carrying the same sample/reference identifier remain in one fold.
- `Amostra`: stricter secondary analysis that holds out entire sampling points/parcels. It addresses transfer to unseen points and is not interchangeable with the primary scan/reference grouping.

Run both analyses and compare their scores. A large deterioration under point-held-out validation may indicate that scan-level validation overstates transfer to new sampling points.

## Interpretation
Metrics (R², MAE, RMSE and bias) are calculated from one OOF prediction per observation. Candidate ranking by OOF RMSE is exploratory: because the same OOF results are inspected to select a candidate, they are not an unbiased final estimate of the selected model. Use nested grouped CV or an untouched grouped test set for final performance reporting.

TOC and N are evaluated as separate targets. The dissertation reported validation concerns TOC; the N experiment remains exploratory until its laboratory reference method, units and provenance are verified. No model performance is claimed until the original dataset is loaded and the analysis is executed.


## Nested grouped model selection

The function `nested_grouped_model_selection` performs an outer GroupKFold
for evaluation and an inner GroupKFold for candidate selection. Within each
outer fold, the candidate with the lowest inner OOF RMSE is selected, refitted
on the complete outer-training partition, and evaluated on the untouched
outer-test partition. The pooled outer predictions estimate the complete
selection procedure while keeping groups separated at both levels.

The candidate hyperparameters are fixed defaults in this first implementation;
this is model-family selection, not an exhaustive hyperparameter search. The
outer metrics estimate this selection procedure, not the final model refitted
on all available observations. Repeat the analysis with `group_column="Amostra"`
for point-held-out generalization.

"""Run repeated grouped within-depth NIR band-selection stability."""
import argparse, json
from pathlib import Path
import pandas as pd
from carbonapp.data import load_dataset
from carbonapp.stability import within_depth_feature_selection_stability

def run(data_path,output_dir,n_resamples=100,seed=42):
    frame=load_dataset(data_path); output_dir.mkdir(parents=True,exist_ok=True); outputs={}
    for group in ("Amostra","Sample Number"):
        result=within_depth_feature_selection_stability(frame,group_column=group,n_resamples=n_resamples,random_state=seed)
        outputs[group]=result
        result.to_csv(output_dir/f"band-stability-{group.lower().replace(' ','-')}.csv",index=False)
    combined=pd.concat(outputs.values(),ignore_index=True); combined.to_csv(output_dir/"band-stability-summary.csv",index=False)
    (output_dir/"band-stability-metadata.json").write_text(json.dumps({"target":"TOC","resamples":n_resamples,"seed":seed,"method":"Repeated GroupShuffleSplit; training-fold depth-mean residualization; SelectKBest(f_regression).","interpretation":"Selection frequency is exploratory algorithmic stability, not chemical attribution or validated predictive value.","groups":list(outputs)},indent=2),encoding="utf-8")
    return combined

def main():
    p=argparse.ArgumentParser(description=__doc__); p.add_argument("--data",type=Path,default=Path("data/raw/[quad]base_nirs_refletancia.csv")); p.add_argument("--output",type=Path,default=Path("reports/band-stability")); p.add_argument("--resamples",type=int,default=100); p.add_argument("--seed",type=int,default=42); a=p.parse_args()
    print(run(a.data,a.output,a.resamples,a.seed).groupby("group_column").head(15).to_string(index=False))
if __name__=="__main__": main()

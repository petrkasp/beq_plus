import json
import time

from lean_interact import AutoLeanServer, LeanREPLConfig
from lean_interact.project import TempRequireProject

from beq_plus import beq_plus

import false_positives_experiment

from datasets import load_dataset

def main():
    with open("false_positives.json", "r", encoding="utf-8") as f:
        false_positives = json.load(f)

    dataset = load_dataset("PAug/ProofNetVerif", split=false_positives_experiment.SPLIT)
    repl_config = LeanREPLConfig(project=TempRequireProject(lean_version="v4.8.0", require="mathlib"), verbose=True)
    server = AutoLeanServer(config=repl_config)

    corrects = 0
    incorrects = 0

    assert len(false_positives) == false_positives_experiment.TOTAL
    
    for datum in false_positives:
        start_time = time.time()
        assert beq_plus(
                datum["lean4_formalization"],
                datum["lean4_prediction"],
                datum["lean4_src_header"],
                server=server,
                timeout_per_proof=120
            )
        
        length = time.time() - start_time

        is_correct = dataset.filter(lambda x: x["id"] == datum["id"] and x["lean4_prediction"] == datum["lean4_prediction"])[0]["correct"]

        if is_correct:
            assert length > 2

        if is_correct:
            corrects += 1
        else:
            incorrects += 1

    assert 1 <= corrects <= false_positives_experiment.TOTAL - 1
    assert 1 <= incorrects <= false_positives_experiment.TOTAL - 1

if __name__ == "__main__":
    main()

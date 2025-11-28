# Run Human Equivalence dataset from BEq with BEq+

import json

from beq_plus import beq_plus

from lean_interact import AutoLeanServer, LeanREPLConfig
from lean_interact.project import TempRequireProject, LeanRequire

from tqdm import tqdm

# HUMAN_EQUIVALENCE_DATASET = "data/human_equivalence/o1-generated"
HUMAN_EQUIVALENCE_DATASET = "data/human_equivalence/rautoformalizer-generated"

DATA = "autoformalization.json"
LABELS = "labels.json"


BASE_DATASET = "data/proofnet/benchmark.jsonl"
def load_proofnet():
    with open(BASE_DATASET, "r", encoding="utf-8") as f:
        proofnet = [json.loads(line) for line in f]
    return {p["full_name"]: p for p in proofnet}


def main():
    # LeanInteract (BEq+) does not support Lean 4.7.0-rc2
    repl_config = LeanREPLConfig(project=TempRequireProject(lean_version="v4.8.0", require="mathlib"), verbose=True)
    server = AutoLeanServer(config=repl_config)

    true_positives = 0
    false_positives = 0
    false_negatives = 0
    true_negatives = 0

    proofnet = load_proofnet()
    
    with open(HUMAN_EQUIVALENCE_DATASET + "/" + DATA, "r", encoding="utf-8") as f:
        autoformalization = json.load(f)
    
    with open(HUMAN_EQUIVALENCE_DATASET + "/" + LABELS, "r", encoding="utf-8") as f:
        labels = json.load(f)

    for key in tqdm(autoformalization):
        prediction = autoformalization[key][0]["formal_stmt_pred"]
        correct = labels[prediction]
        header = proofnet[key]["header"]
        reference = proofnet[key]["formal_stmt"] 

        beq_result = beq_plus(
            reference,
            prediction,
            header,
            server=server,
            timeout_per_proof=120
        )
        if beq_result and correct:
            true_positives += 1
        elif beq_result and not correct:
            false_positives += 1
        elif not beq_result and correct:
            false_negatives += 1
        else:  # not beq_result and not correct
            true_negatives += 1

    print("True positives:", true_positives)
    print("False positives:", false_positives)
    print("False negatives:", false_negatives)
    print("True negatives:", true_negatives)

    print("Accuracy:", (true_positives + true_negatives) / (true_positives + false_positives + false_negatives + true_negatives))
    print("Precision:", true_positives / (true_positives + false_positives))
    print("Recall:", true_positives / (true_positives + false_negatives))
    print("F1:", 2 * true_positives / (2 * true_positives + false_positives + false_negatives))
    
if __name__ == "__main__":
    main()

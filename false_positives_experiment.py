import random
import json
import time

from lean_interact import AutoLeanServer, Command, LeanREPLConfig
from lean_interact.project import TempRequireProject

from beq_plus import beq_plus

from datasets import load_dataset

TRUE_POSITIVE_CHECK_TIME = 5
DEBUG = False

VALID_FALSE_POSITIVES = [294, 411, 553, 1218]
TEST_FALSE_POSITIVES = [321, 446, 554]

SPLIT = "test"
if SPLIT == "valid":
    FALSE_POSITIVES = VALID_FALSE_POSITIVES
else:
    FALSE_POSITIVES = TEST_FALSE_POSITIVES

TOTAL = 4

def main():
    random.seed(69)
    target_wrongs = random.randrange(1, TOTAL)
    target_corrects = TOTAL - target_wrongs

    dataset = load_dataset("PAug/ProofNetVerif", split=SPLIT)
    not_correct_dataset = dataset.filter(lambda x: not x["correct"])
    correct_dataset = dataset.filter(lambda x: x["correct"])

    selected_false_positives = random.sample(FALSE_POSITIVES, target_wrongs)
    selected_corrects = random.sample(range(len(correct_dataset)), target_corrects)

    repl_config = LeanREPLConfig(project=TempRequireProject(lean_version="v4.8.0", require="mathlib"), verbose=True)
    server = AutoLeanServer(config=repl_config)
    
    # Validate that false positives are false positives
    # for i in FALSE_POSITIVES:
    #     datum = not_correct_dataset[i]
    #     for _ in range(2):
    #         start = time.time()
    #         assert beq_plus(
    #             datum["lean4_formalization"],
    #             datum["lean4_prediction"],
    #             datum["lean4_src_header"],
    #             server=server,
    #             timeout_per_proof=120
    #         )
    #         length = time.time() - start
    #     print("False positive checked in", length)
    #     assert not datum["correct"]

    # Validate and replace true positives
    used = set(selected_corrects)

    i = 0
    while i < len(selected_corrects):
        datum = correct_dataset[selected_corrects[i]]
        assert datum["correct"]
        
        for _ in range(2):
            start = time.time()
            is_correct = beq_plus(
                datum["lean4_formalization"],
                datum["lean4_prediction"],
                datum["lean4_src_header"],
                server=server,
                timeout_per_proof=120
            )
            length = time.time() - start
            if not is_correct:
                break
        if DEBUG:
            print(f"{is_correct} checked in", length)
        if length < TRUE_POSITIVE_CHECK_TIME:
            is_correct = False

        if is_correct:
            i += 1
        else:
            while selected_corrects[i] in used:
                selected_corrects[i] = random.randrange(0, len(correct_dataset))
            used.add(selected_corrects[i])
    

    examples = [correct_dataset[i] for i in selected_corrects] + [not_correct_dataset[i] for i in selected_false_positives]
    assert len(examples) == TOTAL

    for e in examples:
        del e["correct"]
    random.shuffle(examples)

    with open("false_positives.json", "w", encoding="utf-8") as f:
        json.dump(examples, f, ensure_ascii=False, indent=2)
    
    
if __name__ == "__main__":
    main()

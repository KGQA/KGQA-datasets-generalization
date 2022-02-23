import os
import sys
import json
import argparse

import numpy as np
import pandas as pd
from datasets import load_dataset
from utils.sparql_util import get_triples_lcquad, get_triples_lcquad2, get_triples_qald, get_functions_from_sparql, formalize_for_lcquad2, add_missing_angle_brackets_lcquad2


TASKS = ["LCQUAD", "LCQUAD2", "QALD"]


def _extract_schema_terms_qald(x):
    terms = []
    try:
        triples = get_triples_qald(x["query"]["sparql"])
        for triple in triples:
            terms.append(triple[1].toPython())
    except Exception as e:
        print(e)
        return np.NAN
    functions = get_functions_from_sparql(x["query"]["sparql"])
    terms.extend(functions)
    return terms


def _extract_schema_terms_lcquad(x):
    terms = []
    try:
        triples = get_triples_lcquad(x["query"]["sparql"])
        for triple in triples:
            terms.append(triple[1].toPython())
    except Exception as e:
        print(e)
        return np.NAN

    functions = get_functions_from_sparql(x["query"]["sparql"])
    terms.extend(functions)

    return terms

def _extract_schema_terms_lcquad2(x, kb):
    terms = []
    try:
        triples = get_triples_lcquad2(x["query"]["sparql"], kb)
        for triple in triples:
            terms.append(triple[1].toPython())
    except:
        try:
            triples = get_triples_lcquad2(formalize_for_lcquad2(x["query"]["sparql"]), kb)
            for triple in triples:
                terms.append(triple[1].toPython())
        except:
            return np.NAN
    functions = get_functions_from_sparql(x["query"]["sparql"])
    terms.extend(functions)
    return terms

def process_qald():

    train = load_dataset("kgqa_datasets/qald/qald.py", "qald", split="train").to_pandas()[
        ["id", "question", "query", "answers"]]
    test = load_dataset("kgqa_datasets/qald/qald.py", "qald", split="test").to_pandas()[
        ["id", "question", "query", "answers"]]

    train["id"] = train["id"].map(lambda x: "qald_train_" + str(x))
    test["id"] = test["id"].map(lambda x: "qald_test_" + str(x))

    qald = pd.concat([train, test])

    def func(xs):
        for x in json.loads(xs):
            if x["language"] == "en":
                return [x]

    qald["question"] = qald["question"].map(lambda x: func(x))
    qald["answers"] = qald.apply(lambda x: json.loads(x["answers"]), axis=1)
    qald["schema_terms"] = qald.apply(lambda x: _extract_schema_terms_qald(x), axis=1)

    errors = qald[qald['schema_terms'].isnull()]
    qald = qald.dropna()

    return qald, errors


def process_lcquad():

    train = load_dataset("kgqa_datasets/lcquad_v1/lcquad_v1.py", "lcquad", split="train").to_pandas()[
        ["_id", "corrected_question", "sparql_query"]]
    test = load_dataset("kgqa_datasets/lcquad_v1/lcquad_v1.py", "lcquad", split="test").to_pandas()[
        ["_id", "corrected_question", "sparql_query"]]

    train["_id"] = train["_id"].map(lambda x: "lcquad_train_" + str(x))
    test["_id"] = test["_id"].map(lambda x: "lcquad_test_" + str(x))

    lcquad = pd.concat([train, test])
    lcquad.rename(columns={"_id": "id", "corrected_question": "question", "sparql_query": "query"}, inplace=True)
    lcquad["question"] = lcquad["question"].map(lambda x: [{"language": "en", "string": x}])
    lcquad["query"] = lcquad["query"].map(lambda x: {"sparql": x})

    lcquad["answers"] = ""
    lcquad["answers"] = lcquad["answers"].map(lambda x: [])

    lcquad["schema_terms"] = lcquad.apply(lambda x: _extract_schema_terms_lcquad(x), axis=1)

    errors = lcquad[lcquad['schema_terms'].isnull()]
    lcquad = lcquad.dropna()

    return lcquad, errors


def process_lcquad2(kb="dbpedia"):

    config_name = f"lcquad2-{kb}"

    train = load_dataset("kgqa_datasets/lcquad_v2/lcquad_v2.py", config_name, split="train").to_pandas()[
        ["uid", "question", "sparql", "answer"]]
    test = load_dataset("kgqa_datasets/lcquad_v2/lcquad_v2.py", config_name, split="test").to_pandas()[
        ["uid", "question", "sparql", "answer"]]

    train["uid"] = train["uid"].map(lambda x: "lcquad2_train_" + str(x))
    test["uid"] = test["uid"].map(lambda x: "lcquad2_test_" + str(x))

    lcquad2 = pd.concat([train, test])
    lcquad2.rename(columns={"uid": "id", "sparql": "query", "answer": "answers"},
                   inplace=True)
    lcquad2["question"] = lcquad2["question"].map(lambda x: [{"language": "en", "string": x}])

    if kb == "dbpedia":
        lcquad2["query"] = lcquad2["query"].map(lambda x: {"sparql": add_missing_angle_brackets_lcquad2(x)})
    else:
        lcquad2["query"] = lcquad2["query"].map(lambda x: {"sparql": x})

    lcquad2["schema_terms"] = lcquad2.apply(lambda x: _extract_schema_terms_lcquad2(x, kb), axis=1)

    errors = lcquad2[lcquad2['schema_terms'].isnull()]
    lcquad2 = lcquad2.dropna()

    return lcquad2, errors


def get_tasks(task_names):
    task_names = task_names.split(',')
    if "all" in task_names:
        tasks = TASKS
    else:
        tasks = []
        for task_name in task_names:
            assert task_name.upper() in TASKS, "Task %s not found!" % task_name
            tasks.append(task_name.upper())
    return tasks


def main(arguments):
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--tasks", type=str, default="lcquad2", help="tasks to be processed as a comma separated string.")
    parser.add_argument("-d", "--data_dir", type=str, default="data_dir", help="directory to save the preprocessed datasets.")
    parser.add_argument("-s", "--shuffle", type=bool, default=True, help="whether to shuffle the datasets.")
    parser.add_argument("-r", "--random_seed", type=int, default="42", help="random seed.")
    parser.add_argument("--kb_lcquad2", default="dbpedia")
    parser.add_argument("--kb_endpoint", type=str, help="kb endpoint")

    args = parser.parse_args(arguments)

    if not os.path.isdir(args.data_dir):
        os.mkdir(args.data_dir)

    tasks = get_tasks(args.tasks)

    questions = pd.DataFrame(columns=["id", "question", "query", "schema_terms", "answers"])
    error_sets = pd.DataFrame(columns=["id", "question", "query", "schema_terms", "answers"])
    stats_file = open(os.path.join(args.data_dir, "stats.txt"), "w")
    for task in tasks:
        stats_file.write(f"==============={task}===============\n")
        if task == "QALD":
            data, errors = process_qald()
        elif task == "LCQUAD":
            data, errors = process_lcquad()
        elif task == "LCQUAD2":
            data, errors = process_lcquad2(args.kb_lcquad2)
        else:
            data = pd.DataFrame(columns=["id", "question", "query", "schema_terms", "answers"])
            errors = pd.DataFrame(columns=["id", "question", "query", "schema_terms", "answers"])
        stats_file.write(f"total: {len(data) + len(errors)}\ndata: {len(data)}\nerrors: {len(errors)}\n\n")
        questions = pd.concat([questions, data])
        error_sets = pd.concat([error_sets, errors])
    stats_file.close()

    if args.shuffle:
        questions = questions.sample(frac=1, random_state=args.random_seed)

    json.dump(json.loads(questions.to_json(orient="records")), open(os.path.join(args.data_dir, "data_sets.json"), "w"), indent=2)
    json.dump(json.loads(error_sets.to_json(orient="records")), open(os.path.join(args.data_dir, "errors.json"), "w"), indent=2)

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))







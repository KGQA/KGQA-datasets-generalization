from __future__ import division
import argparse
import sys
import os
import json
from sklearn.model_selection import GroupShuffleSplit, train_test_split
from functools import reduce
import numpy as np
import pandas as pd

def get_single_terms(data):
    single_terms = reduce(lambda x, y: x+y, data["schema_terms"].values.tolist())
    return single_terms

def get_schema_terms(data):
    schema_terms = dict()

    for idx, row in data.iterrows():
        if tuple(sorted(row["schema_terms"])) not in schema_terms:
            schema_terms[tuple(sorted(row["schema_terms"]))] = len(schema_terms)
    return schema_terms

def group_schema_terms(data):
    terms2group = dict()
    def func(x):
        if tuple(sorted(x)) not in terms2group:
            terms2group[tuple(sorted(x))] = len(terms2group)
        return terms2group[tuple(sorted(x))]
    data["schema_terms_group_idx"] = data["schema_terms"].map(lambda x: func(x))

    return data

def determine_level(schema_terms, single_terms_train, schema_terms_train):
    unseen_terms = list(set(schema_terms).difference(set(single_terms_train)))
    if tuple(sorted(schema_terms)) not in schema_terms_train:
        if len(unseen_terms) != 0:  # zero-shot
            level="zero-shot"
        else:
            level="compositional"
    else:
        level="i.i.d."
    return level


def sample_zeroshot_questions(data, sampling_ratio, n_splits, random_seed):
    group_ids = data["schema_terms_group_idx"].tolist()
    groups = np.array(group_ids)
    gss = GroupShuffleSplit(n_splits=n_splits, train_size=1-sampling_ratio, random_state=random_seed)

    train_zeroshot_splits = []

    unique_group_splits = dict()
    for train_idx, zeroshot_idx in gss.split(X=data, groups=groups):
        if tuple(sorted(train_idx)) not in unique_group_splits:
            unique_group_splits[tuple(sorted(train_idx))] = zeroshot_idx

    for train_idx, zeroshot_idx in unique_group_splits.items():
        train_idx = list(train_idx)

        train_set = data.iloc[train_idx]
        zeroshot_set = data.iloc[zeroshot_idx]

        train_zeroshot_splits.append((train_set, zeroshot_set))

    return train_zeroshot_splits

def sample_compositional_questions(data, sampling_ratio, n_splits, random_seed):

    if sampling_ratio == 0.0:
        return []

    group_ids = data["schema_terms_group_idx"].tolist()
    groups = np.array(group_ids)
    gss = GroupShuffleSplit(n_splits=n_splits, train_size=1-sampling_ratio, random_state=random_seed)

    train_compos_splits = []

    unique_group_splits = dict()
    for train_idx, compo_idx in gss.split(X=data, groups=groups):
        if tuple(sorted(train_idx)) not in unique_group_splits:
            unique_group_splits[tuple(sorted(train_idx))] = compo_idx

    for train_idx, compo_idx in unique_group_splits.items():
        train_idx = list(train_idx)

        train_set = data.iloc[train_idx]
        compo_set = data.iloc[compo_idx]

        train_compos_splits.append((train_set, compo_set))

    return train_compos_splits

def data_filter(data_src, train_set):

    single_schema_terms_train = get_single_terms(train_set)
    schema_terms_train = get_schema_terms(train_set)

    data_src["level"] = data_src["schema_terms"].map(lambda x: determine_level(x, single_schema_terms_train, schema_terms_train))
    zero_set = data_src[data_src['level']=="zero-shot"]
    compo_set = data_src[data_src['level']=="compositional"]
    iid_set = data_src[data_src['level']=="i.i.d."]

    return zero_set, compo_set, iid_set


def zeroshot_filter(zeroshot_set, train_set):

    zeroshot_set, compositional_set, iid_set = data_filter(zeroshot_set, train_set)

    non_zeroshot_set = pd.concat([compositional_set, iid_set])

    return zeroshot_set, non_zeroshot_set


def compositional_filter(compositional_set, train_set):

    zeroshot_set, compositional_set, iid_set = data_filter(compositional_set, train_set)

    non_compositional_set = pd.concat([zeroshot_set, iid_set])

    return compositional_set, non_compositional_set


def sample_iid_questions(data, sampling_ratio, random_seed):
    train_set, iid_set = train_test_split(data, train_size=1-sampling_ratio, random_state=random_seed)
    return train_set, iid_set


def main(arguments):
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset_id", type=str, help="the unique identifier of the dataset newly generated.")
    parser.add_argument("--input_path", type=str, help="full path of datasets to be resplitted.")
    parser.add_argument("--output_dir", default="output_dir", type=str, help="directory to save the resplitted datasets.")
    parser.add_argument("--n_splits_zero", default=1, type=int, help="the number of splits for zeroshot generalization.")
    parser.add_argument("--n_splits_compo", default=1, type=int, help="the number of splits for compositional generalization.")
    parser.add_argument("--random_seed", default=42, type=int, help="random seed.")
    parser.add_argument("--sampling_ratio_zero", default=.4, type=float, help="the ratio for sampling zeroshot questions from the data set.")
    parser.add_argument("--sampling_ratio_compo", default=.1, type=float, help="the ratio for sampling compositional questions from the data set.")
    parser.add_argument("--sampling_ratio_iid", default=.1, type=float, help="the ratio for sampling iid questions from the data set.")
    parser.add_argument("--validation_size", default=.33, type=float, help="the size of validation set splitted from the test size.")

    args = parser.parse_args(arguments)

    if not os.path.isdir(args.output_dir):
        os.mkdir(args.output_dir)

    data_sets = pd.read_json(args.input_path, orient="records")

    data_sets = group_schema_terms(data_sets)
    num_samples = len(data_sets)

    empty_data = pd.DataFrame(columns=data_sets.columns)
    candidate_zero_compo_iid_train_splits = []

    if args.sampling_ratio_iid == 0.0 and args.sampling_ratio_compo == 0.0 and args.sampling_ratio_zero > 0.0:
        candidate_train_zeroshot_splits = sample_zeroshot_questions(data_sets, args.sampling_ratio_zero,
                                                                    args.n_splits_zero,
                                                                    args.random_seed)
        for train_set_1, zeroshot_set_1 in candidate_train_zeroshot_splits:
            zeroshot_set, non_zeroshot_set = zeroshot_filter(zeroshot_set_1, train_set_1)
            train_set = pd.concat([train_set_1, non_zeroshot_set])
            candidate_zero_compo_iid_train_splits.append((zeroshot_set, empty_data, empty_data, train_set))
    elif args.sampling_ratio_iid == 0.0 and args.sampling_ratio_compo > 0.0 and args.sampling_ratio_zero == 0.0:
        candidate_train_compo_splits = sample_compositional_questions(data_sets,
                                                                      args.sampling_ratio_compo,
                                                                      args.n_splits_compo, args.random_seed)
        for train_set_2, compositional_set_1 in candidate_train_compo_splits:
            compositional_set, non_compositional_set = compositional_filter(compositional_set_1, train_set_2)
            train_set = pd.concat([train_set_2, non_compositional_set])
            candidate_zero_compo_iid_train_splits.append((empty_data, compositional_set, empty_data, train_set))
    elif args.sampling_ratio_iid > 0.0 and args.sampling_ratio_compo == 0.0 and args.sampling_ratio_zero == 0.0:
        train_set, iid_set = sample_iid_questions(data_sets, args.sampling_ratio_iid, args.random_seed)
        candidate_zero_compo_iid_train_splits.append((empty_data, empty_data, iid_set, train_set))
    else:
        if args.sampling_ratio_zero > 0.0:
            candidate_train_zeroshot_splits = sample_zeroshot_questions(data_sets, args.sampling_ratio_zero, args.n_splits_zero,
                                                                        args.random_seed)

            for train_set_1, zeroshot_set_1 in candidate_train_zeroshot_splits:

                zeroshot_set, non_zeroshot_set = zeroshot_filter(zeroshot_set_1, train_set_1)
                intermediate_train_set_1 = pd.concat([train_set_1, non_zeroshot_set])

                if args.sampling_ratio_compo > 0.0:
                    candidate_train_compo_splits = sample_compositional_questions(intermediate_train_set_1, args.sampling_ratio_compo,
                                                                                  args.n_splits_compo, args.random_seed)
                    for train_set_2, compositional_set_1 in candidate_train_compo_splits:
                        compositional_set, non_compositional_set = compositional_filter(compositional_set_1, train_set_2)
                        intermediate_train_set_2 = pd.concat([train_set_2, non_compositional_set])

                        if args.sampling_ratio_iid > 0.0:
                            train_set, iid_set = sample_iid_questions(intermediate_train_set_2, args.sampling_ratio_iid, args.random_seed)
                            candidate_zero_compo_iid_train_splits.append((zeroshot_set, compositional_set, iid_set, train_set))
                        else:
                            candidate_zero_compo_iid_train_splits.append(
                                (zeroshot_set, compositional_set, empty_data, intermediate_train_set_2))
                else:
                    train_set, iid_set = sample_iid_questions(intermediate_train_set_1, args.sampling_ratio_iid,
                                                              args.random_seed)
                    candidate_zero_compo_iid_train_splits.append((zeroshot_set, empty_data, iid_set, train_set))
        else:
            candidate_train_compo_splits = sample_compositional_questions(data_sets,
                                                                          args.sampling_ratio_compo,
                                                                          args.n_splits_compo, args.random_seed)
            for train_set_2, compositional_set_1 in candidate_train_compo_splits:
                compositional_set, non_compositional_set = compositional_filter(compositional_set_1, train_set_2)
                intermediate_train_set_2 = pd.concat([train_set_2, non_compositional_set])

                train_set, iid_set = sample_iid_questions(intermediate_train_set_2, args.sampling_ratio_iid,
                                                          args.random_seed)
                candidate_zero_compo_iid_train_splits.append((empty_data, compositional_set, iid_set, train_set))

    train_zero_compo_iid_splits = []

    for zero, compo, iid, train in candidate_zero_compo_iid_train_splits:

        zero_set_tmp = pd.DataFrame(columns=train.columns)
        compo_set_tmp = pd.DataFrame(columns=train.columns)
        iid_set_tmp = pd.DataFrame(columns=train.columns)

        if not zero.empty:
            zero_set_1, compo_set_1, iid_set_1 = data_filter(zero, train)
            zero_set_tmp = pd.concat([zero_set_tmp, zero_set_1])
            compo_set_tmp = pd.concat([compo_set_tmp, compo_set_1])
            iid_set_tmp = pd.concat([iid_set_tmp, iid_set_1])

        if not compo.empty:
            zero_set_2, compo_set_2, iid_set_2 = data_filter(compo, train)
            zero_set_tmp = pd.concat([zero_set_tmp, zero_set_2])
            compo_set_tmp = pd.concat([compo_set_tmp, compo_set_2])
            iid_set_tmp = pd.concat([iid_set_tmp, iid_set_2])

        if not iid.empty:
            zero_set_3, compo_set_3, iid_set_3 = data_filter(iid, train)
            zero_set_tmp = pd.concat([zero_set_tmp, zero_set_3])
            compo_set_tmp = pd.concat([compo_set_tmp, compo_set_3])
            iid_set_tmp = pd.concat([iid_set_tmp, iid_set_3])

        if zero.empty:
            train = pd.concat([train, zero_set_tmp])
            zero_set = empty_data
        else:
            zero_set = zero_set_tmp

        if iid.empty:
            train = pd.concat([train, iid_set_tmp])
            iid_set = empty_data
        else:
            iid_set = iid_set_tmp

        if compo.empty:
            train = pd.concat([train, compo_set_tmp])
            compo_set = empty_data
        else:
            compo_set = compo_set_tmp

        train_zero_compo_iid_splits.append((train, zero_set, compo_set, iid_set))

    for idx, splits in enumerate(train_zero_compo_iid_splits, 1):

        split_dir_name = "new_split_"+str(idx) if len(train_zero_compo_iid_splits) > 1 else "new_split"
        split_dir = os.path.join(args.output_dir, split_dir_name)
        if not os.path.isdir(split_dir):
            os.makedirs(split_dir)

        train, zero, compo, iid = splits

        train = train[["id", "question", "query", "answers", "schema_terms"]]
        test = pd.concat([zero, compo, iid])[["id", "question", "query", "answers", "schema_terms", "level"]]

        if args.validation_size > 0.0:
            validation, test, _, _ = train_test_split(test, test["level"], train_size=args.validation_size, stratify=test["level"], random_state=args.random_seed)
            json_rslt_valid = {
                "dataset": {
                    "id": f"{args.dataset_id}-valid"
                },
                "questions": json.loads(validation.to_json(orient="records"))
            }
            json.dump(json_rslt_valid, open(os.path.join(split_dir, f"{args.dataset_id}-valid.json"), "w"), indent=2)

        json_rslt_train = {
            "dataset": {
                "id": f"{args.dataset_id}-train"
            },
            "questions": json.loads(train.to_json(orient="records"))
        }
        json.dump(json_rslt_train, open(os.path.join(split_dir, f"{args.dataset_id}-train.json"), "w"), indent=2)
        json_rslt_test = {
            "dataset": {
                "id": f"{args.dataset_id}-test"
            },
            "questions": json.loads(test.to_json(orient="records"))
        }
        json.dump(json_rslt_test, open(os.path.join(split_dir, f"{args.dataset_id}-test.json"), "w"), indent=2)

        stats_file = open(os.path.join(split_dir, "stats.txt"), "w")
        stats_file.write("==============Split %d==============\n" % idx)
        if args.validation_size > 0.0:
            stats_file.write(
                f"total: {num_samples}\ntrain: {len(train)} ({len(train)/num_samples*100} %%)\nvalid: {len(validation)}({len(validation)/num_samples*100} %%)\ntest: {len(test)}({len(test)/num_samples*100} %%)\nzero: {len(zero)} ({len(zero)/num_samples*100} %%)\ncompo: {len(compo)} ({len(compo)/num_samples*100} %%)\niid: {len(iid)} ({len(iid)/num_samples*100} %%)"
            )
        else:
            stats_file.write(
                f"total: {num_samples}\ntrain: {len(train)} ({len(train) / num_samples * 100} %%)\ntest: {len(test)}({len(test) / num_samples * 100} %%)\nzero: {len(zero)} ({len(zero) / num_samples * 100} %%)\ncompo: {len(compo)} ({len(compo) / num_samples * 100} %%)\niid: {len(iid)} ({len(iid) / num_samples * 100} %%)"
            )
        stats_file.write("\n\n")
        stats_file.close()

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))

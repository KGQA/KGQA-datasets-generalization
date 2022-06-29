# KGQA-datasets-generalization

[![License: Apache-2.0](https://img.shields.io/badge/License-Apache--2.0-blue.svg)](LICENSE.txt)

> Existing approaches on Question Answering over Knowledge Graphs (KGQA) have weak generalizability. That is often due to the standard i.i.d. assumption on the underlying dataset. Recently, three levels of generalization for KGQA were defined, namely _i.i.d._, _compositional_, _zero-shot_. We analyze 25 well-known KGQA datasets for 5 different Knowledge Graphs (KGs). We show that according to this definition many existing and online available KGQA datasets are either not suited to train a generalizable KGQA system or that the datasets are based on discontinued and out-dated KGs. Generating new datasets is a costly process and, thus, is not an alternative to smaller research groups and companies. In this work, we propose a mitigation method for re-splitting available KGQA datasets to enable their applicability to evaluate generalization, without any cost and manual effort. We test our hypothesis on three KGQA datasets, i.e., [LC-QuAD 1.0](http://lc-quad.sda.tech/lcquad1.0.html), [LC-QuAD 2.0](http://lc-quad.sda.tech/) and [QALD-9](https://github.com/ag-sc/QALD)


## Table of contents

 1. [Datasets](#datasets)
    1. [Overview](#overview)
    2. [Statistics](#statistics)
    3. [Use of the datasets](#use-of-the-datasets)
 2. [Reproduction](#reproduction)
    1. [Requirements](#requirements)
    2. [Run Scripts](#run-scripts)
 3. [License](#license)

## Datasets

### Overview

By analyzing 25 existing KGQA datasets, we spot a huge gap in generalization evaluation of KGQA systems in the Semantic Web community. The main goal of this work is to reuse existing datasets from nearly a decade of research and thus generate new datasets applicable to generalization evaluation. 
We propose a simple and novel method to achieve this goal, and evaluate the effectiveness of our method and the quality of the new datasets it generate in generalizable KGQA systems. 

### Test Existing KGQA Datasets

The table below shows the evaluation result w.r.t. three levels of generalization defined in ([Gu et al., 2021](https://arxiv.org/pdf/2011.07743.pdf)).

|                                                                            Dataset                                                                            |     KG     |  Year  |  I.I.D.  | Compositional | Zero-Shot |
|:-------------------------------------------------------------------------------------------------------------------------------------------------------------:|:----------:|:------:|:--------:|:-------------:|:---------:|
|                                                     [WebQuestions](https://aclanthology.org/D13-1160.pdf)                                                     |  Freebase  |  2013  | &#x2611; |   &#x2612;    | &#x2612;  |
|                                                    [SimpleQuestions](https://arxiv.org/pdf/1506.02075.pdf)                                                    |  Freebase  |  2015  | &#x2611; |   &#x2612;    | &#x2612;  |
|                                                   [ComplexQuestions](https://aclanthology.org/C16-1236.pdf)                                                   |  Freebase  |  2016  |    -     |       -       |     -     |
|                                                  [GraphQuestions](https://github.com/ysu1989/GraphQuestions)                                                  |  Freebase  |  2016  | &#x2611; |   &#x2611;    | &#x2612;  |
|                                                    [WebQuestionsSP](https://aclanthology.org/P16-2033.pdf)                                                    |  Freebase  |  2016  | &#x2611; |   &#x2612;    | &#x2612;  |
|                                                  [The 30M Factoid QA](https://arxiv.org/pdf/1603.06807.pdf)                                                   |  Freebase  |  2016  | &#x2611; |   &#x2612;    | &#x2612;  |
|                                              [SimpleQuestionsWikidata](http://ceur-ws.org/Vol-1963/paper555.pdf)                                              |  Wikidata  |  2017  | &#x2611; |   &#x2612;    | &#x2612;  |
|                                             [LC-QuAD 1.0](http://lc-quad.sda.tech/static/ISWC2017_paper_152.pdf)                                              |  DBpedia   |  2017  | &#x2611; |   &#x2611;    | &#x2611;  |
|                                                  [ComplexWebQuestions](https://arxiv.org/pdf/1803.06643.pdf)                                                  |  Freebase  |  2018  | &#x2611; |   &#x2612;    | &#x2612;  |
|                                                  [QALD-9](https://svn.aksw.org/papers/2018/QALD9/public.pdf)                                                  |  DBpedia   |  2018  | &#x2611; |   &#x2611;    | &#x2611;  |
|                                                     [PathQuestion](https://arxiv.org/pdf/1801.04726.pdf)                                                      |  Freebase  |  2018  |    -     |       -       |     -     |
|                                                        [MetaQA](https://arxiv.org/pdf/1709.04071.pdf)                                                         | WikiMovies |  2018  |    -     |       -       |     -     |
|                                                   [SimpleDBpediaQA](https://aclanthology.org/C18-1178.pdf)                                                    |  DBpedia   |  2018  | &#x2611; |   &#x2612;    | &#x2612;  |
| [TempQuestions](https://dl.acm.org/doi/fullHtml/10.1145/3184558.3191536#:~:text=The%20benchmark%20proposed%20in%20this,and%20tagging%20of%20temporal%20cues.) |  Freebase  |  2018  |    -     |       -       |     -     |
|                                              [LC-QuAD 2.0](https://jens-lehmann.org/files/2019/iswc_lcquad2.pdf)                                              |  Wikidata  |  2019  | &#x2611; |   &#x2611;    | &#x2611;  |
|                                                      [FreebaseQA](https://aclanthology.org/N19-1028.pdf)                                                      |  Freebase  |  2019  |    -     |       -       |     -     |
|                                           [Compositional Freebase Questions](https://arxiv.org/pdf/2007.08970.pdf)                                            |  Freebase  |  2020  | &#x2611; |   &#x2611;    | &#x2612;  |
|                                                       [RuBQ 1.0](https://arxiv.org/pdf/2005.10659.pdf)                                                        |  Wikidata  |  2020  |    -     |       -       |     -     |
|                                                        [GrailQA](https://arxiv.org/pdf/2011.07743.pdf)                                                        |  Freebase  |  2020  | &#x2611; |   &#x2611;    | &#x2611;  |
|                                                                         [Event-QA](https://arxiv.org/pdf/2004.11861.pdf)                                                                          |  EventKG   |  2020  |    -     |       -       |     -     |
|                       [RuBQ 2.0](https://www.springerprofessional.de/rubq-2-0-an-innovated-russian-question-answering-dataset/19211406)                       |  Wikidata  |  2021  |    -     |       -       |     -     |
|                                                                             MLPQ                                                                              |  DBpedia   |  2021  |    -     |       -       |     -     |
|                                           [Compositional Wikidata Questions](https://arxiv.org/pdf/2108.03509.pdf)                                            |  Wikidata  |  2021  | &#x2611; |   &#x2611;    | &#x2612;  |
|                                                [TimeQuestions](https://dl.acm.org/doi/10.1145/3459637.3482416)                                                |  Wikidata  |  2021  |    -     |       -       |     -     |
|                                                     [CronQuestions](https://arxiv.org/pdf/2106.01515.pdf)                                                     |  Wikidata  |  2021  |    -     |       -       |     -     |

### Statistics

The statistics of the original datasets and its counterparts (*) generated by our approach is shown below. 

|                   Dataset                    | Total | Train | Validation | Test | I.I.D. | Compositional | Zero-Shot |
|:--------------------------------------------:|:-----:|:-----:|:----------:|:----:|:------:|:-------------:|:---------:|
|     [QALD-9](output_dir/qald/orig_split)     |  558  |  408  |     -      | 150  |   46   |      53       |    51     |
| [LC-QuAD 1.0](output_dir/lcquad/orig_split)  | 5000  | 4000  |     -      | 1000 |  434   |      559      |     7     |
| [LC-QuAD 2.0](output_dir/lcquad2/orig_split) | 30221 | 24177 |     -      | 6044 |  4624  |      948      |    472    |
|     [QALD-9*](output_dir/qald/new_split)     |  558  |  385  |     -      | 173  |   14   |      41       |    118    |
| [LC-QuAD 1.0*](output_dir/lcquad/new_split)  | 5000  | 3420  |    521     | 1059 |  331   |     1021      |    228    |
| [LC-QuAD 2.0*](output_dir/lcquad2/new_split) | 30221 | 20321 |    3267    | 6633 |  4014  |     3235      |   	2651   |

### Use of the datasets 

 * The datasets are available in ``json`` format.
 * All the datasets are stored in the `output_dir` directory, where three sub-directories exist for LC-QuAD 1.0, LC-QuAD 2.0 and QALD-9 respectively. In each dataset directory, there are two sub-directories for its original and new versions respectively.  

## Reproduction

### Requirements

 * rdflib==6.0.2
 * datasets==1.16.1
 * scikit-learn==1.0.1
 * numpy==1.20.3
 * pandas==1.3.5

Due to usage of the `kgqa_datasets` repository (see [link](https://github.com/semantic-systems/KGQA-datasets)), you need to clone it into the root directory of this project.

### Parameters

In order to ensure reproducibility, we set ``random_seed`` to 42 for all the KGQA datasets (e.g., LC-QuAD 1.0, LC-QuAD 2.0, and QALD-9).

#### QALD 

 * ``dataset_id``: dataset-qald
 * ``input_path`` data_dir/qald/data_sets.json
 * ``output_dir``: output_dir/qald
 * ``sampling_ratio_zero``: .4
 * ``sampling_ratio_compo``: .1
 * ``sampling_ratio_iid``: .1 
 * ``n_splits_compo``: 1
 * ``n_splits_zero``: 1 
 * ``validation_size``: 0.0

#### LC-QuAD 1.0 

 * ``dataset_id``: dataset-lcquad
 * ``input_path`` data_dir/lcquad/data_sets.json
 * ``output_dir``: output_dir/lcquad
 * ``sampling_ratio_zero``: .6
 * ``sampling_ratio_compo``: .1
 * ``sampling_ratio_iid``: .2
 * ``n_splits_compo``: 1
 * ``n_splits_zero``: 1

#### LC-QuAD 2.0 

 * ``dataset_id``: dataset-lcquad2
 * ``input_path`` data_dir/lcquad2/data_sets.json
 * ``output_dir``: output_dir/lcquad2
 * ``sampling_ratio_zero``: .6
 * ``sampling_ratio_compo``: .1
 * ``sampling_ratio_iid``: .2
 * ``n_splits_compo``: 1
 * ``n_splits_zero``: 1 
 * ``validation_size``: 0.0

### Run Scripts

1. Prior to re-splitting a given KGQA dataset, first preprocess raw datasets by running the following command:

````bash
python preprocess.py --tasks <dataset_name> --data_dir <data_dir> --shuffle True --random_seed 42
````

2. Start to re-split the given dataset by running the following command:

```bash
python resplit.py --dataset_id <dataset_id> --input_path <data_dir> --output_dir <output_dir> --sampling_ratio_zero .4 --sampling_ratio_compo .1 --sampling_ratio_iid .1 --random_seed 42 --n_splits_compo 1 --n_splits_zero 1 --validation_size 0.0
```

## Citation
Please cite our paper if you use any tool or datasets provided in this repository:

´´´
@article{jiang2022knowledge,
  title={Knowledge Graph Question Answering Datasets and Their Generalizability: Are They Enough for Future Research?},
  author={Jiang, Longquan and Usbeck, Ricardo},
  journal={arXiv preprint arXiv:2205.06573},
  year={2022}
}
´´´

## License
This work is licensed under the Apache 2.0 License - see the [LICENSE](LICENSE.txt) file for details.



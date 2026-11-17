# PDAN8412w POE: CNN Image Classification with Goodbooks-10k

| | |
|---|---|
| **Student** | Katlego Thejane |
| **Student number** | ST10104762 |
| **Programme** | Postgraduate Diploma in Data Analytics |
| **Module** | Programming for Data Analysis (PDAN8412w) |
| **Institution** | Rosebank College (IIE) |
| **Submission date** | 18 November 2026 |

## 1. Overview

This submission is a reproducible Apache Spark and TensorFlow workflow for a convolutional neural network (CNN) image-classification proof of concept, framed as a first step towards premises-based facial recognition for a publisher.

- **Stage A (Spark):** loads, profiles, cleans, screens and labels 10,000 book records from the Goodbooks-10k metadata.
- **Stage B (TensorFlow/Keras):** trains a baseline CNN and a regularised, retrained CNN on book-cover images and evaluates both on the same unseen test set.
- **Target:** four balanced reader-popularity tiers (Emerging, Established, Popular, Blockbuster) built with Spark `NTILE(4)` on `ratings_count`. This is a Goodreads engagement proxy, not verified sales.
- **Input to the CNN:** cover pixels only (160 × 160 RGB). All numeric metadata fields are excluded to prevent label leakage.

## 2. Files in this submission

| File | Description |
|---|---|
| `ST10104762_Katlego-Thejane_PDAN8412w_POE_Report.docx` | Written report: problem definition, data, methods, results, limitations, references |
| `ST10104762_Katlego-Thejane_PDAN8412w_POE.ipynb` | Jupyter notebook that runs the whole pipeline |
| `goodbooks-10k-books.csv` | Source metadata (10,000 records, 23 variables) |
| `<dataset attribution file>.txt` | Dataset attribution and licence statement |
| `insert_results.py` | Helper script that copies the notebook's saved outputs (tables, figures, metrics) into the report |
| `README.md` | This file |

## 3. Requirements

- Python 3 with Jupyter (the notebook kernel is named *Python 3 (PySpark + TensorFlow)*).
- A Java runtime (JDK) installed and on the `PATH`, which PySpark requires.
- Python packages: `pyspark`, `tensorflow`, `scikit-learn`, `scipy`, `pandas`, `numpy`, `matplotlib`, `seaborn`, `pillow`, `requests`. For the report script only: `python-docx`.
- Internet access, because the notebook downloads the cover images from the `image_url` column.
- A GPU is optional but speeds up training considerably. Google Colab works.

The first code cell contains a commented-out `%pip install` line for missing packages. The exact Python, Spark, TensorFlow and Keras versions used in a run are saved to `poe_cnn_work/results/run_summary.json`.

## 4. How to run

1. Place `goodbooks-10k-books.csv` in the same folder as the notebook. The notebook stops with a clear error if the file is missing. On Colab, upload it to the session.
2. Open the notebook and choose **Run all**, or run the cells from top to bottom. The Spark session is stopped at the end of Stage A, and Stage B uses pandas and TensorFlow only.
3. All generated files are written to a `poe_cnn_work/` folder next to the notebook.

The run is repeatable: a fixed seed of 42 controls the image sampling, the data split and the weight initialisation. Downloads are resumable, so an interrupted run can be restarted.

## 5. Notebook structure

| Section | Content |
|---|---|
| 1 | Environment and reproducibility (seed, folders, plot style) |
| Stage A | Spark metadata layer: data-quality assessment and cleaning, exploratory analysis, target construction, feature selection and leakage screening, image sampling plan |
| Stage B | TensorFlow image layer: cover download and image checks, train/validation/test split, input pipeline, baseline CNN, evaluation metrics, retrained CNN, comparison against the success criteria, limitations and ethics |

## 6. Outputs created by the notebook

Everything is saved inside `poe_cnn_work/`:

- `images/` and `image_manifest.csv`: downloaded covers and a record of every download attempt.
- `books_labeled.csv`: the cleaned metadata with popularity tiers.
- `results/`:
  - `model_comparison.csv`: test-set metrics for both models (Table 9).
  - `success_criteria.json`: acceptance-criteria outcomes (Table 8).
  - `recall_by_class.csv` and `confusion_matrices.json`: per-class results.
  - `feature_screening.csv` and `tier_summary.csv`: Spark screening and tier tables.
  - `run_summary.json`: seed, package versions, split sizes, epochs run, download success by tier.
  - `goodbooks_tuned_cnn.keras`: the saved retrained model.
- `results/figures/`: `fig6_sample_covers.png`, `fig7_learning_curves.png` and `fig8_confusion_matrices.png`.

## 7. Populating the report from the notebook

The report's results tables and Figures 6 to 8 are filled from the notebook's saved outputs, not typed by hand.

1. Run every notebook cell.
2. Install the helper dependency once: `pip install python-docx`.
3. In one folder, place `insert_results.py`, the report `.docx` and the `poe_cnn_work/` folder, then run:
   `python insert_results.py --report <report>.docx --out <final>.docx`
4. Open the output in Word and press **Ctrl+A** then **F9** to refresh the contents page and lists.

If an expected notebook output is missing, the script stops and names the missing file without changing the report.

## 8. Key design decisions

- **Leakage control:** the seven popularity-count fields correlate with the target at ρ = 0.61 to 0.98 and are excluded. The remaining fields are weak or non-visual predictors, so the model sees only the cover image (report Section 5.2).
- **Placeholder covers:** one identical Goodreads "no photo" image covers 33.3% of records and is unevenly spread across tiers, so those books are excluded from the image sample (`EXCLUDE_PLACEHOLDER_COVERS = True`). Set it to `False` to reproduce the unfiltered sample.
- **Sampling:** up to 1,200 genuine covers per tier (`MAX_PER_CLASS`), at most 4,800 images.
- **Evaluation:** stratified 70:15:15 split, balanced class weights, macro F1 as the primary metric, and four pre-set acceptance criteria applied to the retrained model.

## 9. Scope and limitations

- Book-cover classification does not validate facial recognition. The workflow demonstrates a transferable CNN pipeline only.
- `ratings_count` is a platform engagement proxy, not sales or bestseller status.
- Results apply to books with a genuine cover image and depend on which cover downloads succeed.
- Any later face-recognition stage would need explicit consent, purpose limitation and compliance with the Protection of Personal Information Act 4 of 2013. See Section 9 of the report.

## 10. Dataset attribution

Zając, Z. (n.d.) *goodbooks-10k: Ten thousand books, six million ratings*. Available at: https://github.com/zygmuntz/goodbooks-10k (Accessed: 6 October 2026).

The dataset is released under the Creative Commons Attribution-ShareAlike 4.0 licence (CC BY-SA 4.0). Attribution is retained in the attribution file and in the report's reference list.

# Retrieval

Generated on 2026-10-05.

## Summary

- Queries evaluated: 5
- Top K: 10
- Ranking rows: 372
- Mean precision@K: 0.3200

## Query Evaluation

| query | retrieved | relevant retrieved | precision@K | avg matched terms |
| --- | ---: | ---: | ---: | ---: |
| artificial intelligence healthcare education | 10 | 3 | 0.3000 | 2.1000 |
| climate change policy economics | 10 | 2 | 0.2000 | 1.5000 |
| dementia cognitive impairment | 10 | 3 | 0.3000 | 1.3000 |
| digital marketing social media | 10 | 3 | 0.3000 | 1.6000 |
| tuberculosis diagnosis treatment | 10 | 5 | 0.5000 | 1.7000 |

## Top Results

| query | rank | title | score | relevant |
| --- | ---: | --- | ---: | --- |
| artificial intelligence healthcare education | 1 | Generic Artificial Intelligent Agent Using Iot And Deep Learning | 33.4687 | False |
| artificial intelligence healthcare education | 2 | "You Don't Wanna Teach Little Kids about Climate Change": Beliefs and Barriers to Sustainability Education in Early Childhood. | 29.5462 | False |
| artificial intelligence healthcare education | 3 | Peran Kepala Madrasah Pasca Pandemi Covid-19: Kajian Integrasi Manajemen Pendidikan dan Kecerdasan Sosial Perspektif Islam | 26.7174 | False |
| climate change policy economics | 1 | Urban politics on housing policy transformation in Indonesia: an institutional perspective | 38.3756 | False |
| climate change policy economics | 2 | The global costs of extreme weather that are attributable to climate change | 35.2277 | True |
| climate change policy economics | 3 | Transient prosperity or durable resilience: how place-based specialty agricultural policy shapes rural household welfare in China | 30.4304 | False |
| dementia cognitive impairment | 1 | Pharmacologic Treatments for Dementia and the Risk of Developing Age-Related Macular Degeneration | 84.5869 | False |
| dementia cognitive impairment | 2 | Conversion to major neurocognitive disorder after COVID‐19 in a woman with bipolar disorder: A 6‐year longitudinal case report | 71.0678 | False |
| dementia cognitive impairment | 3 | Implementation of a targeted screening program for Alzheimer's disease risk in a primary care setting | 60.9812 | True |
| digital marketing social media | 1 | Identity Disturbance in the Digital Era during the COVID-19 Pandemic: The Adverse Effects of Social Media and Job Stress | 68.9269 | False |
| digital marketing social media | 2 | Improving Marketing Performance of Small-Medium Enterprises of Food Stall by Innovation on Online Orders | 60.3092 | False |
| digital marketing social media | 3 | Social media use is associated with lower COVID-19 booster uptake in Japan | 56.6028 | True |
| tuberculosis diagnosis treatment | 1 | Population Decline May Affect the Incidence of Pulmonary Tuberculosis in Japan | 84.8908 | True |
| tuberculosis diagnosis treatment | 2 | RISK FACTORS FOR THE DEVELOPMENT OF CRITICAL CONDITIONS REQUIRING HOSPITALIZATION IN THE INTENSIVE CARE UNIT AND INTENSIVE CARE UNIT IN PATIENTS WITH TUBERCULOSIS | 54.0971 | True |
| tuberculosis diagnosis treatment | 3 | Treatment Outcomes of Childhood Tuberculosis in Three Districts of Balochistan, Pakistan: Findings from a Retrospective Cohort Study | 36.6199 | True |

## Interpretation

This milestone is a sparse lexical retrieval baseline over saved TF-IDF terms. Relevance is approximated from OpenAlex topic-name substring matches, so precision values are diagnostic rather than definitive information-retrieval judgments.

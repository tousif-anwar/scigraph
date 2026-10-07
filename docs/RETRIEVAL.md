# Retrieval

Generated on 2026-10-06.

## Summary

- Queries evaluated: 5
- Top K: 10
- Ranking rows: 886
- Mean precision@K: 0.3800

## Query Evaluation

| query | retrieved | relevant retrieved | precision@K | avg matched terms |
| --- | ---: | ---: | ---: | ---: |
| artificial intelligence healthcare education | 10 | 4 | 0.4000 | 1.8000 |
| climate change policy economics | 10 | 6 | 0.6000 | 2.1000 |
| dementia cognitive impairment | 10 | 4 | 0.4000 | 1.9000 |
| digital marketing social media | 10 | 3 | 0.3000 | 2.4000 |
| tuberculosis diagnosis treatment | 10 | 2 | 0.2000 | 1.7000 |

## Top Results

| query | rank | title | score | relevant |
| --- | ---: | --- | ---: | --- |
| artificial intelligence healthcare education | 1 | ‘Our bodies are sacred… the information we share with healthcare providers is sacred’: Envisioning the future of culturally safe healthcare systems for Indigenous women, Two-Spirit, Indigiqueer and gender diverse peoples | 54.8547 | False |
| artificial intelligence healthcare education | 2 | Nurse educator education in six European countries: a descriptive study / Ausbildung von Pflegepädagog/-innen in sechs europäischen Ländern – eine deskriptive Studie | 45.0703 | False |
| artificial intelligence healthcare education | 3 | “Aidemics” examined analytically through the connectivist theory: institutional AI-Mediation in higher education via an artificial intelligence center (CILT-AI) | 40.5103 | True |
| climate change policy economics | 1 | Climate Change and Mental Health: An Interactive Educational Session | 70.0466 | True |
| climate change policy economics | 2 | Simulating and mapping the risks and impact of fall army worm (Spodoptera frugiperda) and white grub (Holotrichia serrata) in maize production outlooks for Nigeria under climate change | 52.7000 | True |
| climate change policy economics | 3 | Climate-sensitive urban energy poverty indicator framework | 41.6485 | False |
| dementia cognitive impairment | 1 | Functional health and cognitive impairment: insights from elderly residents in old-age homes in Delhi | 78.5121 | True |
| dementia cognitive impairment | 2 | Dementia detection from brain activity during sleep | 64.5228 | True |
| dementia cognitive impairment | 3 | Music and the aging brain – Exploring the role of long-term Carnatic music training on cognition and gray matter volumes | 40.3482 | False |
| digital marketing social media | 1 | Impact of Hate Speech on Building the Value of Pro-Social Activities. Perspective of Author and Social Media User | 81.9407 | True |
| digital marketing social media | 2 | The Effect of Social Media on Students' School Life in Indonesia | 65.1545 | False |
| digital marketing social media | 3 | Exploring the use of digital media to improve English speaking skills among Thai students in English Education Study Program | 56.9055 | False |
| tuberculosis diagnosis treatment | 1 | Tuberculosis Modeling in East Java Based on Geographically Weighted Regression Approach | 80.4212 | True |
| tuberculosis diagnosis treatment | 2 | Caregiver Perceived Barriers to Diagnosis and Care in Down Syndrome Regression Disorder | 64.2022 | False |
| tuberculosis diagnosis treatment | 3 | The treatment of relapsed/refractory anaplastic large cell lymphoma expressing the anaplastic lymphoma kinase: a single-center experience | 45.3577 | False |

## Interpretation

This milestone is a sparse lexical retrieval baseline over saved TF-IDF terms. Relevance is approximated from OpenAlex topic-name substring matches, so precision values are diagnostic rather than definitive information-retrieval judgments.

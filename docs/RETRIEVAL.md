# Retrieval

Generated on 2026-10-06.

## Summary

- Queries evaluated: 5
- Top K: 10
- Ranking rows: 893
- Mean precision@K: 0.3600

## Query Evaluation

| query | retrieved | relevant retrieved | precision@K | avg matched terms |
| --- | ---: | ---: | ---: | ---: |
| artificial intelligence healthcare education | 10 | 3 | 0.3000 | 1.9000 |
| climate change policy economics | 10 | 3 | 0.3000 | 2.0000 |
| dementia cognitive impairment | 10 | 1 | 0.1000 | 1.6000 |
| digital marketing social media | 10 | 5 | 0.5000 | 2.2000 |
| tuberculosis diagnosis treatment | 10 | 6 | 0.6000 | 1.8000 |

## Top Results

| query | rank | title | score | relevant |
| --- | ---: | --- | ---: | --- |
| artificial intelligence healthcare education | 1 | How Artificial Intelligence is Strategically Evolving the Customers Relationships: In Context to Indian Banking Sector | 44.0412 | False |
| artificial intelligence healthcare education | 2 | Relationship between optimism, emotional intelligence, and academic resilience of nursing students: the mediating effect of self-directed learning competency | 42.9300 | True |
| artificial intelligence healthcare education | 3 | Generic Artificial Intelligent Agent Using Iot And Deep Learning | 34.1053 | False |
| climate change policy economics | 1 | Investigating the Effectiveness of TikTok in Promoting Public Awareness and Engagement on Climate Change Adaptation and Mitigation Measures in Nigeria | 76.4088 | False |
| climate change policy economics | 2 | The role of risk mitigation and adaptation measures in climate resilience: A case study of Ho Chi Minh City in Vietnam | 40.0747 | False |
| climate change policy economics | 3 | Urban politics on housing policy transformation in Indonesia: an institutional perspective | 39.1651 | False |
| dementia cognitive impairment | 1 | Pharmacologic Treatments for Dementia and the Risk of Developing Age-Related Macular Degeneration | 89.4759 | False |
| dementia cognitive impairment | 2 | Conversion to major neurocognitive disorder after COVID‐19 in a woman with bipolar disorder: A 6‐year longitudinal case report | 71.0619 | False |
| dementia cognitive impairment | 3 | Implementation of a targeted screening program for Alzheimer's disease risk in a primary care setting | 60.5722 | True |
| digital marketing social media | 1 | Digital marketing employability skills in job advertisements – must-have soft skills for entry level workers: A content analysis | 99.5760 | False |
| digital marketing social media | 2 | Identity Disturbance in the Digital Era during the COVID-19 Pandemic: The Adverse Effects of Social Media and Job Stress | 68.5428 | False |
| digital marketing social media | 3 | Improving Marketing Performance of Small-Medium Enterprises of Food Stall by Innovation on Online Orders | 61.0258 | False |
| tuberculosis diagnosis treatment | 1 | Changes in chest X-ray findings in 1- and 2-month group after treatment initiation for suspected pulmonary tuberculosis | 116.7610 | True |
| tuberculosis diagnosis treatment | 2 | Population Decline May Affect the Incidence of Pulmonary Tuberculosis in Japan | 94.4247 | True |
| tuberculosis diagnosis treatment | 3 | RISK FACTORS FOR THE DEVELOPMENT OF CRITICAL CONDITIONS REQUIRING HOSPITALIZATION IN THE INTENSIVE CARE UNIT AND INTENSIVE CARE UNIT IN PATIENTS WITH TUBERCULOSIS | 59.8095 | True |

## Interpretation

This milestone is a sparse lexical retrieval baseline over saved TF-IDF terms. Relevance is approximated from OpenAlex topic-name substring matches, so precision values are diagnostic rather than definitive information-retrieval judgments.

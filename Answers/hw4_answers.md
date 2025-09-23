## Questions for evaluation
1. What student organizations at the iSchool focus on data science?

    -> Testing topic-specific information retrieval

2. Which iSchool organizations collaborate with companies or industry partners?
    -> tests the model's ability to retrieve nuanced details (like “this org partners with X companies” or “brings in guest speakers from industry”)

3. What leadership opportunities are available through student organizations?

    -> reflects student's real concern and helps to evaluate if the pipeline can handle multi-document answers

4. How do I get involved with a student club at the iSchool?

    -> Checks if the model can provide procedural information

5. Are there any organizations that help with career development, networking, or professional skills?

    -> Tests model's contextual understanding. requires model to retrieve functional goals rather than just group names


## Model Evaluation

### Overall evaluation

Overall, all three models managed to retrieve the basic facts. Differences arise in their depth, structure and nuances. 
GPT-5's answers were fast, clear and verbose. It even tried to go 'beyond'the question, offering outreach drafts or instructions on how to verify unclear points. 
Gemini was more concise but tended to provide clear examples for each question. 
Claude struck a balance between factual retrieval and contextual guidance, often giving step-by-step procedural advice with concrete details, but sometimes added extra context that may not have been strictly in the source snippets.

### Best model: GPT-5
Personally, I found gpt-5 to be the best. It was fast, structured and highly cost-effective. Beyond answering directly, it offers helpful extras like email drafts and suggestions, which shows strong willingness to continue conversations. This balance of efficiency, depth, and engagement makes it the most practical choice.

Caveat: On Q2 (about industry partnerships), Claude did slightly better, confidently highlighting NEXIS and IDSA, while GPT remained slightly cautious.

### Worst Model: Gemini
Gemini was the weakest in this evaluation. Its answers were shallow, repetitive, and often too generic, lacking the depth or actionable detail that GPT-5-nano and Claude provided.Even though it was consistent, it was slow and added the least value.

Caveat: Gemini did well on Q4 (how to get involved with a club). Its response was concise, practical, and gave clear steps like emailing the org or paying a small fee. That made it easier to follow than the more detailed but heavier answers from the others.




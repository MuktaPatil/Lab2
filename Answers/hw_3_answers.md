## Questions for evaluation

1. How is baseball played?
    -> Evaluates chatbot's Summarization and simplification skills. Gotta check if it follows instructions and answers like the user is 10 years old.
2. How many players are on the field?
    -> Fact checking. Evaluating precision, ensuring there is no hallucination
3. Why are innings important in baseball?
    -> conceptual question. Goes beyond copy-pasting facts. Needs to apply reasoning
## Best Memory to use

Particularly in this usecase of baseball chat, the conversational summary works the best. It condenses prior messages into a few concise bullets, keeping the model focused and reducing token usage, which is especially useful for longer chats. For our question, the model does not need to remember every detail, making it a great option in my opinion.

## Questions

1) Did having both documents improve the answers? Explain your answer
Yes, but only slightly. When each model used just one URL, the answers were already accurate and well-structured. They explained the basics (nine innings, nine players, scoring, outs, and game flow). When both documents were combined, the responses got a bit more detailed and polished. For example, Anthropic and Gemini added extra context like field dimensions, manager strategy, and clearer differentiation between types of outs. OpenAI’s explanation also became more comprehensive.

So the improvement was in depth and completeness, not in correctness. But I dont think this improvement is worth the cost it demands.  For eg, GPT-4o (≈ $5 per 1M input, $15 per 1M output), doubling input text increases cost linearly. If the question only needs basics (like “how many players”), then the extra cost of feeding both documents is not justified.

2) Which model was best? Explain your answer
Personally I found Anthropic to be the best. The reasons are as follows:

1. Detailed and structured answers:  Broke its answers into sections (Basic Play, Scoring, Getting Outs, Structure), which made it easier to follow and learn from.

2. Details with simplicity: It added nuance like “bases 90 feet apart” and “no ties in baseball” while still keeping explanations readable.

3. Consistency: Whether using one or both documents, Claude’s answers maintained accuracy, structure, and completeness.

While being slightly expensive, it give crisp answers, detailed but not overloading. The sort of queries asked would not cause too much monetary strain in this scenario.

OpenAI was strong too: it gave clean, straightforward answers, but slightly less structured than Claude. However, it would be the most cost effective option. 
Gemini was the weakest in this set: while correct, it was slower and repeated obvious points without adding as much nuance.
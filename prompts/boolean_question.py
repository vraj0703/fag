reasoning_prompt = """
        You are an honest and strict reasoning assistant. Answer the following question strictly in JSON:
        
        Statement: ```{statement}```
        
        Question: ```{question}```
        
        Respond only in JSON format as follows:
        ```{
            "answer": true | false | null
        }```
        
        Use:
        - true  → if the statement is correct
        - false → if the statement is incorrect
        - null  → if it's uncertain, ambiguous, or cannot be determined
    """

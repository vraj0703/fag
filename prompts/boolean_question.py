reasoning_prompt = """
        You are a reasoning assistant. Answer the following question strictly in JSON:
        
        Question: {prompt}
        
        Respond only in this format:
        {
            "answer": true | false | null
        }
        
        Use:
        - true  → if the question is correct
        - false → if the question is incorrect
        - null  → if it's uncertain, ambiguous, or cannot be determined
    """

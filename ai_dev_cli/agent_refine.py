    def _auto_fix_test_failures(self, error_output: str):
        """PHASE 4: Refine - Auto-fix test failures using LLM."""
        prompt = f"""Tests failed. Analyze the error and fix the code.

**Error Output:**
{error_output[:1000]}

**Task:**
1. Identify what's broken
2. Write the fix
3. Return ONLY the fixed file content

Respond with:
FILE: path/to/file.py
```python
# fixed code here
```
"""
        try:
            response = self.llm.chat(prompt)
            self.total_cost += response.cost_usd
            
            # Parse response for file fixes
            import re
            file_match = re.search(r'FILE:\s*(\S+)', response.content)
            code_match = re.search(r'```(?:python)?\n(.*?)```', response.content, re.DOTALL)
            
            if file_match and code_match:
                file_path = self.output_dir / file_match.group(1)
                if file_path.exists():
                    with open(file_path, 'w') as f:
                        f.write(code_match.group(1))
                    self.results.append(f"✅ Auto-fixed {file_match.group(1)}")
        except Exception as e:
            self.errors.append(f"⚠️  Auto-fix failed: {str(e)}")

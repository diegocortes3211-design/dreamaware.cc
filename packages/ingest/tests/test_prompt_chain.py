import unittest
from packages.ingest.prompt_chain import PromptChain


class TestPromptChain(unittest.TestCase):
    def test_build_rag_prompt_structure(self):
        pc = PromptChain(prompts=[])
        task = "Summarize project plan"
        question = "What are the next steps?"
        contexts = ["first context", "second context"]
        sources = ["file1.md", "file2.md"]
        format_spec = '{"summary":"string"}'

        prompt = pc.build_rag_prompt(task, question, contexts, sources, format_spec)

        # Basic sections
        self.assertIn("System:", prompt)
        self.assertIn("User:", prompt)
        self.assertIn("Context:", prompt)
        self.assertIn("<<<DOCS", prompt)
        self.assertIn("DOCS>>>", prompt)

        # Sources should be labeled
        self.assertIn("--- SOURCE: file1.md", prompt)
        self.assertIn("--- SOURCE: file2.md", prompt)

        # Answer format guard is present and contains the provided spec
        self.assertIn("Answer format:", prompt)
        self.assertIn(format_spec, prompt)

        # The template should end with the repeated question to re-anchor the task
        self.assertTrue(prompt.endswith(f"Repeat question: {question}"))


if __name__ == "__main__":
    unittest.main()
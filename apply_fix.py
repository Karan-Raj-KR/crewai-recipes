import glob
import re

for f in glob.glob('recipes/*/llm.py'):
    with open(f, 'r') as file:
        content = file.read()
    
    if 'import warnings' not in content:
        content = content.replace('import os', 'import os\nimport warnings')
    
    content = re.sub(
        r'print\(\s*"WARNING: NVIDIA_API_KEY is deprecated\. Please use LLM_API_KEY instead\."\s*\)',
        'warnings.warn(\n                    "NVIDIA_API_KEY is deprecated. Please use LLM_API_KEY instead.",\n                    UserWarning,\n                    stacklevel=2,\n                )',
        content
    )
    
    with open(f, 'w') as file:
        file.write(content)

for test_file in ['recipes/faq-bot/test_llm.py', 'recipes/lead-qualification/test_llm.py']:
    with open(test_file, 'r') as file:
        content = file.read()
    
    content = re.sub(
        r'def test_nvidia_api_key_fallback_and_warning\(\n\s*mock_llm, capsys: pytest\.CaptureFixture\[str\]\n\) -> None:\n\s*env = \{"NVIDIA_API_KEY": "nvapi-test"\}\n\s*with patch\.dict\(os\.environ, env, clear=True\):\n\s*get_llm\(\)\n\n\s*mock_llm\.assert_called_once\(\)\n\s*kwargs = mock_llm\.call_args\.kwargs\n\s*assert kwargs\["api_key"\] == "nvapi-test"\n\n\s*captured = capsys\.readouterr\(\)\n\s*assert "WARNING: NVIDIA_API_KEY is deprecated" in captured\.out',
        'def test_nvidia_api_key_fallback_and_warning(\n    mock_llm,\n) -> None:\n    env = {"NVIDIA_API_KEY": "nvapi-test"}\n    with patch.dict(os.environ, env, clear=True):\n        with pytest.warns(UserWarning, match="NVIDIA_API_KEY is deprecated"):\n            get_llm()\n\n        mock_llm.assert_called_once()\n        kwargs = mock_llm.call_args.kwargs\n        assert kwargs["api_key"] == "nvapi-test"',
        content
    )
    
    with open(test_file, 'w') as file:
        file.write(content)

print("All replacements done.")

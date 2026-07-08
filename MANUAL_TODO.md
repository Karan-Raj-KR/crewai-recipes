# Manual To-Do

This file tracks manual items requiring review, configuration, or judgment following the repository setup.

## Actions Required

- [ ] **Verify Social Links**: Confirm that the Instagram (`https://instagram.com/karan.rajkr`) and Hashnode (`https://karanrajkr.hashnode.dev`) links in `README.md` are correct.
- [ ] **Review NVIDIA NIM Network Issue**: During automated testing, the direct API calls to `https://integrate.api.nvidia.com/v1/chat/completions` using the 70B model were timing out occasionally. It works fine for the `llama-3.1-8b-instruct` model. Please check if your network environment requires a proxy, or if the free tier API rate limits are affecting the 70B model inference time.
- [ ] **Implement Scaffolds**:
  - `appointment-booking`
  - `whatsapp-action-sim`
  *(GitHub issues have been created for these with the "good first issue" and "recipe: new" labels.)*
- [ ] **Review GitHub Issues**: 8 new issues have been created detailing next steps, unit tests, missing key error handling, and the CONTRIBUTING guide improvements. Please prioritize and assign them.

## Notes

- All Groq references have been successfully migrated to NVIDIA NIM across the codebase, documentation, and issue templates.
- The default LLM across all active recipes and scaffolds is `meta/llama-3.1-8b-instruct` for reliability and speed, but can easily be swapped to `meta/llama-3.3-70b-instruct` as per the inline comments in the `llm.py` configurations.

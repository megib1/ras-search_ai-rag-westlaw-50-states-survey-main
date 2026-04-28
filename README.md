<!-- START badge-template.html --><svg fill="none" viewBox="0 0 120 120" width="120" height="120" xmlns="http://www.w3.org/2000/svg">
  <foreignObject width="100%" height="100%">
    <div xmlns="http://www.w3.org/1999/xhtml">
      <a href="https://github.com/tr/ras-search_ai-rag-westlaw-50-states-survey/blob/tr-cicd-resources/tr/ras-search_ai-rag-westlaw-50-states-survey/badges/update-for-event-loop-error-message/last-badge-update.svg" target="_blank">
        <img alt="Last Updated" src="https://github.com/tr/ras-search_ai-rag-westlaw-50-states-survey/blob/tr-cicd-resources/badges/update-for-event-loop-error-message/last-badge-update.svg">
      </a>
      <br />
      <a href="https://github.com/tr/ras-search_ai-rag-westlaw-50-states-survey/actions/runs/22332328256" target="_blank">
        <img alt="CI Build" src="https://github.com/tr/ras-search_ai-rag-westlaw-50-states-survey/actions/workflows/python-build.yml/badge.svg?branch=update-for-event-loop-error-message">
      </a>
      <br />
      <a href="https://github.com/tr/ras-search_ai-rag-westlaw-50-states-survey/pulls?q=is:pr+created:%3C%3D2026-02-17+is%3Aopen" target="_blank">
      <img alt="Stale Pull Requests" src="https://github.com/tr/ras-search_ai-rag-westlaw-50-states-survey/blob/tr-cicd-resources/badges/update-for-event-loop-error-message/stale-pr-count.svg">
      </a>
      <br />
      <a href="https://github.com/tr/ras-search_ai-rag-westlaw-50-states-survey/labels/dependencies?q=+is%3Aopen" target="_blank">
      <img alt="Dated Dependencies" src="https://github.com/tr/ras-search_ai-rag-westlaw-50-states-survey/blob/tr-cicd-resources/badges/update-for-event-loop-error-message/dated-dependency-count.svg">
      </a>
      <br />
      <a href="https://github.com/tr/ras-search_ai-rag-westlaw-50-states-survey/runs/64617495612" target="_blank">
        <img alt="Code Coverage" src="https://github.com/tr/ras-search_ai-rag-westlaw-50-states-survey/blob/tr-cicd-resources/badges/update-for-event-loop-error-message/code-coverage.svg">
      </a>
      <br />
      <a href="https://github.com/tr/ras-search_ai-rag-westlaw-50-states-survey/runs/64617589214" target="_blank">
        <img alt="Lines of Code" src="https://github.com/tr/ras-search_ai-rag-westlaw-50-states-survey/blob/tr-cicd-resources/badges/update-for-event-loop-error-message/lines-of-code.svg">
      </a>
      <br />
      <a href="https://github.com/tr/ras-search_ai-rag-westlaw-50-states-survey/releases/latest" target="_blank">
      <img alt="Latest Release" src="https://github.com/tr/ras-search_ai-rag-westlaw-50-states-survey/blob/tr-cicd-resources/badges/main/latest-release.svg">
      </a>
    </div>
  </foreignObject>
</svg>

<!-- END badge-template.html -->
# ras-search_ai-rag-westlaw-50-states-survey


To run locally

Set the following env vars in the run config.
```
PYTHONUNBUFFERED=1;DD_ENV=local;DD_PROFILING_ENABLED=false;DD_SERVICE=ai-rag-westlaw-50-states-survey;DD_TRACE_ENABLED=True;DD_VERSION=0.0.1;RESOURCES_DIR=./app/config/resources;HOSTNAME=[put your workstation name here] 
```


The working directory needs to be set to the root

This needs to be set in the helm. Right now in the old project it is set to ./app

Change to ->
RESOURCES_DIR=./app/config/resources


### Run Smoke Tests Locally
- NOTE: you need to be cloud-tool'ed into the *ras-search-preprod* account because then you have access to the secret which allows us to auth into gcs
- NOTE: these steps are for running the commands in a powershell terminal the syntax might be a little different for other terminals

- NOTE: since this is a backend worker you need to have both ai-conversations and ai-rag-westlaw running locally for the below commands to work

- Run the following command to make sure you have the latest testing module installed in your venv
    - `poetry update`
- Then cd into the python site packages folder since we install the testing module as a wheel file
    - `cd .\.venv\Lib\site-packages\`
- Finally, execute the pytest command to run smoke tests on the localhost dns
    - `pytest -v -s -m rag_westlaw .\ai_conversations_qa_testing\ --dns http://localhost:8010`
# Amadeli Release Authority

This public repository contains governance metadata only. It does **not** contain Amadeli source code.

`authority/current-integration.json` identifies the currently recognized canonical `t15-integration` SHA.

Candidate records under `authority/candidates/` identify source PR heads that passed the declared T15 checks and are eligible for reviewed promotion.

A source branch SHA is not canonical merely because a private Git branch points to it. Canonical authority is represented by protected records in this repository.

The protected authority branch is expected to require:

- pull requests;
- the `authority-validate` status check;
- code-owner approval;
- up-to-date branch state;
- resolved conversations;
- no force push;
- no branch deletion;
- enforcement for administrators.

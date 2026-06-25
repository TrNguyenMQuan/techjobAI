# Cover Letter

Description: Generate or improve targeted cover letters from a candidate CV/profile and a specific job description.
Triggers: cover letter, thư xin việc, cv, resume, hồ sơ, ứng tuyển, motivation letter, email ứng tuyển

## When to use

Use this skill when the user asks to create, rewrite, improve, or evaluate a cover letter for a job.

## Workflow

1. Identify the target job and candidate evidence.
2. If a `job_id` and CV file are available through the API, use the cover-letter generation endpoint/tool path.
3. If only text context is available, write from the provided facts and avoid inventing experience.
4. Match candidate skills to the job requirements.
5. Keep the tone professional, specific, and concise.

## Response format

- Provide the cover letter first.
- Then list matched skills/evidence.
- Then list any missing information that would make the letter stronger.

## Guardrails

- Do not hallucinate years of experience, employers, degrees, certifications, or achievements.
- Treat the job description as employer requirements, not evidence that the candidate has those skills.
- Do not infer distributed systems, scalability, production experience, protocols, industry experience, or business impact from a small academic project.
- Preserve the candidate's name exactly as written in the CV.
- Avoid placeholders, duplicate contact headers, dates, subject lines, Markdown fences, and exaggerated words such as "mastered", "expert", or "top-tier".
- Do not include private personal data unless the user provided it.
- Keep claims verifiable from the CV/profile or user-provided notes.
